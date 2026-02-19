"""Provider interface for VPS create/stop/delete/status."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CreateVpsResult:
    provider_vps_id: str
    ip_address: str
    root_password: str | None = None


@dataclass
class InstanceDetails:
    status: str
    ip_address: str | None


class ProviderClient(ABC):
    @abstractmethod
    async def create_vps(
        self,
        region: str,
        plan_type: str,
        cloud_init_user_data: str,
        root_password: str | None = None,
    ) -> CreateVpsResult:
        """Create VPS; return provider id and public IP (IP may be empty until instance is running)."""
        ...

    @abstractmethod
    async def get_status(self, provider_vps_id: str) -> str:
        """Return 'running' | 'pending' | 'stopped' | 'deleted'."""
        ...

    async def get_instance(self, provider_vps_id: str) -> InstanceDetails | None:
        """Return status and IP for the instance (for DNS/DB after running). Default: GET and parse."""
        return None

    @abstractmethod
    async def power_off(self, provider_vps_id: str) -> None:
        ...

    @abstractmethod
    async def delete(self, provider_vps_id: str) -> None:
        ...
