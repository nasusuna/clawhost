"""SQLAlchemy models — User, Subscription, Instance."""
import enum
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models import Instance, Subscription


class SubscriptionStatus(str, enum.Enum):
    active = "active"
    past_due = "past_due"
    canceled = "canceled"


class InstanceStatus(str, enum.Enum):
    provisioning = "provisioning"
    running = "running"
    stopped = "stopped"
    deleted = "deleted"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription", back_populates="user", cascade="all, delete-orphan"
    )
    instances: Mapped[list["Instance"]] = relationship(
        "Instance", back_populates="user", cascade="all, delete-orphan"
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    stripe_subscription_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.active
    )
    plan_type: Mapped[str] = mapped_column(String(64), nullable=False)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    gcp_project_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)  # per-subscription GCP project
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="subscriptions")
    instances: Mapped[list["Instance"]] = relationship("Instance", back_populates="subscription")


class Instance(Base):
    __tablename__ = "instances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True
    )
    provider_vps_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    root_password: Mapped[str | None] = mapped_column(Text, nullable=True)  # encrypted at rest
    ssh_private_key: Mapped[str | None] = mapped_column(Text, nullable=True)  # encrypted at rest
    status: Mapped[InstanceStatus] = mapped_column(
        Enum(InstanceStatus), nullable=False, default=InstanceStatus.provisioning
    )
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    gateway_token: Mapped[str | None] = mapped_column(String(128), nullable=True)
    gemini_api_key: Mapped[str | None] = mapped_column(String(256), nullable=True)
    provision_job_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="instances")
    subscription: Mapped["Subscription | None"] = relationship("Subscription", back_populates="instances")
    gemini_key_pool_entry: Mapped["GeminiKeyPool | None"] = relationship(
        "GeminiKeyPool", back_populates="instance", uselist=False, foreign_keys="GeminiKeyPool.instance_id"
    )
    gemini_usage_entries: Mapped[list["GeminiUsage"]] = relationship(
        "GeminiUsage", back_populates="instance", cascade="all, delete-orphan"
    )


class GeminiKeyPool(Base):
    """Pre-created Gemini API keys; one is assigned to each new instance when no user/shared key is set."""

    __tablename__ = "gemini_key_pool"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key: Mapped[str] = mapped_column(String(256), nullable=False)
    instance_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("instances.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    instance: Mapped["Instance | None"] = relationship("Instance", back_populates="gemini_key_pool_entry", foreign_keys=[instance_id])


class GeminiUsage(Base):
    """Monthly Gemini token usage per instance. Used for dashboard display and 60M cap."""

    __tablename__ = "gemini_usage"
    __table_args__ = (UniqueConstraint("instance_id", "period_start", name="uq_gemini_usage_instance_period"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instance_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("instances.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period_start: Mapped[date] = mapped_column(Date(), nullable=False)  # first day of month (UTC)
    tokens_used: Mapped[int] = mapped_column(BigInteger(), nullable=False, default=0)

    instance: Mapped["Instance"] = relationship("Instance", back_populates="gemini_usage_entries")
