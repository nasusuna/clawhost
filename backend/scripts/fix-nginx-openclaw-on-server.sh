#!/usr/bin/env bash
# Run this on the existing VPS (e.g. via SSH) to fix Nginx → OpenClaw.
# If you see "bash\r: No such file or directory", run first: sed -i 's/\r$//' ./fix-nginx-openclaw-on-server.sh
# Usage: sudo ./fix-nginx-openclaw-on-server.sh <instance-domain>
# Example: sudo ./fix-nginx-openclaw-on-server.sh d47ba3bd7376.customers.yourdomain.com
# Get the domain from the ClawHost dashboard (instance detail).

set -e
DOMAIN="${1:?Usage: $0 <instance-domain>}"
# Match backend defaults (fourplayers/openclaw Control UI on 18789)
OPENCLAW_IMAGE="${OPENCLAW_DOCKER_IMAGE:-fourplayers/openclaw:latest}"
OPENCLAW_PORT="${OPENCLAW_APP_PORT:-18789}"

echo "Using domain: $DOMAIN image: $OPENCLAW_IMAGE port: $OPENCLAW_PORT"
echo "--- Stopping and removing existing openclaw container ---"
docker stop openclaw 2>/dev/null || true
docker rm openclaw 2>/dev/null || true

echo "--- Starting OpenClaw on 127.0.0.1:$OPENCLAW_PORT only ---"
EXTRA_ENV=""
if [ -n "${OPENCLAW_GATEWAY_TOKEN:-}" ]; then
  EXTRA_ENV="-e OPENCLAW_GATEWAY_TOKEN=$OPENCLAW_GATEWAY_TOKEN"
fi
docker run -d --restart always \
  -p "127.0.0.1:${OPENCLAW_PORT}:${OPENCLAW_PORT}" \
  $EXTRA_ENV \
  --name openclaw \
  --security-opt no-new-privileges \
  --cpus=2 --memory=4g \
  "$OPENCLAW_IMAGE"

echo "--- Writing Nginx proxy config ---"
cat > /etc/nginx/sites-available/openclaw << NGINXEOF
server {
  listen 80;
  server_name $DOMAIN;
  location / {
    proxy_pass http://127.0.0.1:$OPENCLAW_PORT;
    proxy_http_version 1.1;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_set_header Upgrade \$http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 86400;
  }
}
NGINXEOF

echo "--- Enabling openclaw site, disabling default ---"
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/openclaw /etc/nginx/sites-enabled/openclaw

echo "--- Testing and reloading Nginx ---"
nginx -t && systemctl reload nginx

echo "--- Requesting SSL with Certbot (optional; DNS must point to this server) ---"
certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "admin@$DOMAIN" --redirect 2>/dev/null || echo "Certbot skipped or failed (e.g. DNS not ready). Visit http://$DOMAIN to confirm OpenClaw."

echo "Done. OpenClaw should be at http://$DOMAIN (or https:// if certbot succeeded)."
