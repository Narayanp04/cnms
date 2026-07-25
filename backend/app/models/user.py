"""ConnectXperts NMS - User and Role Models"""
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class Role(str, enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    READ_ONLY = "read_only"


class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    is_superadmin = Column(Boolean, default=False)
    can_manage_devices = Column(Boolean, default=False)
    can_manage_users = Column(Boolean, default=False)
    can_manage_alerts = Column(Boolean, default=False)
    can_view_reports = Column(Boolean, default=True)
    can_export_data = Column(Boolean, default=False)
    can_configure_system = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    users = relationship("User", back_populates="user_role")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    company = Column(String(255))
    phone = Column(String(50))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role_id = Column(Integer, ForeignKey("user_roles.id"))
    role = Column(Enum(Role), default=Role.READ_ONLY)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    
    # Multi-customer support
    customer = relationship("Customer", back_populates="users")
    user_role = relationship("UserRole", back_populates="users")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    event_logs = relationship("EventLog", back_populates="user")
    notification_recipients = relationship("AlertRecipient", back_populates="user")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    address = Column(Text)
    contact_person = Column(String(255))
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="customer")
    devices = relationship("Device", back_populates="customer")
