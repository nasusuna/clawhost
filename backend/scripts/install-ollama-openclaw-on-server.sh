#!/usr/bin/env bash
# Install Ollama on the VPS and reconfigure OpenClaw to use it as a local model provider.
# Reference: https://docs.openclaw.ai/providers/ollama
#
# Run on the instance via SSH (e.g. instance 144.91.98.32).
# If you see "bash\r: No such file or directory", run: sed -i 's/\r$//' ./install-ollama-openclaw-on-server.sh
#
# Usage:
#   sudo ./install-ollama-openclaw-on-server.sh <instance-domain> [gateway-token]
#
# Example:
#   sudo OPENCLAW_GATEWAY_TOKEN='your-token-from-dashboard' ./install-ollama-openclaw-on-server.sh your-instance.clawhost.com
#
# Get the gateway token from ClawHost dashboard → your instance → copy token.
# If omitted, existing container env is preserved when recreating.

set -e
DOMAIN="${1:?Usage: $0 <instance-domain> [gateway-token]}"
GATEWAY_TOKEN="${2:-${OPENCLAW_GATEWAY_TOKEN:-}}"

OPENCLAW_IMAGE="${OPENCLAW_DOCKER_IMAGE:-fourplayers/openclaw:latest}"
OPENCLAW_PORT="${OPENCLAW_APP_PORT:-18789}"
OLLAMA_MODEL="${OLLAMA_DEFAULT_MODEL:-llama3.2:latest}"

echo "Domain: $DOMAIN | Image: $OPENCLAW_IMAGE | Port: $OPENCLAW_PORT | Ollama model: $OLLAMA_MODEL"

# --- Install Ollama (official Linux method) ---
if ! command -v ollama &>/dev/null; then
  echo "--- Installing Ollama ---"
  curl -fsSL https://ollama.com/install.sh | sh
else
  echo "--- Ollama already installed ---"
fi

# --- Start Ollama and pull default model ---
echo "--- Ensuring Ollama service is running ---"
systemctl enable ollama 2>/dev/null || true
systemctl start ollama 2>/dev/null || true
# Wait for API
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then break; fi
  echo "Waiting for Ollama API..."
  sleep 2
done
echo "--- Pulling Ollama model: $OLLAMA_MODEL ---"
ollama pull "$OLLAMA_MODEL" || true

# --- Recreate OpenClaw with host network so it can use 127.0.0.1:11434 (Ollama) ---
echo "--- Stopping and removing existing OpenClaw container ---"
docker stop openclaw 2>/dev/null || true
docker rm openclaw 2>/dev/null || true

ENV_OPTS="-e OLLAMA_API_KEY=ollama-local"
if [ -n "$GATEWAY_TOKEN" ]; then
  ENV_OPTS="$ENV_OPTS -e OPENCLAW_GATEWAY_TOKEN=$GATEWAY_TOKEN"
fi

echo "--- Starting OpenClaw with host network (so Ollama at 127.0.0.1:11434 is visible) ---"
docker run -d --restart always \
  --network host \
  $ENV_OPTS \
  --name openclaw \
  --security-opt no-new-privileges \
  --cpus=2 --memory=4g \
  "$OPENCLAW_IMAGE"

# --- Ensure Nginx still proxies to OpenClaw (host listens on OPENCLAW_PORT) ---
echo "--- Verifying Nginx config for $DOMAIN ---"
if [ ! -f /etc/nginx/sites-available/openclaw ]; then
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
  rm -f /etc/nginx/sites-enabled/default
  ln -sf /etc/nginx/sites-available/openclaw /etc/nginx/sites-enabled/openclaw
fi
nginx -t && systemctl reload nginx

echo "--- Done ---"
echo "Ollama is running (port 11434). OpenClaw is running with host network and OLLAMA_API_KEY=ollama-local."
echo "In OpenClaw Control UI, add or select an agent and set the model to an Ollama model (e.g. ollama/$OLLAMA_MODEL or ollama/llama3.2)."
echo "Docs: https://docs.openclaw.ai/providers/ollama"
echo "Instance URL: https://$DOMAIN (or http if no SSL)"
