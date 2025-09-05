"""
Database models for the SMM Bot - Updated for JAP API compatibility
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, 
    ForeignKey, BigInteger, Enum as SQLEnum, Index, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum


Base = declarative_base()


class UserLanguage(enum.Enum):
    UZBEK = "uz"
    RUSSIAN = "ru"
    ENGLISH = "en"


class TransactionType(enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    ORDER_PAYMENT = "order_payment"
    REFERRAL_BONUS = "referral_bonus"
    ADMIN_ADJUSTMENT = "admin_adjustment"


class TransactionStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OrderStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    ERROR = "error"
    REFILL = "refill"  # For refill orders


class PaymentMethod(enum.Enum):
    COINGATE = "coingate"
    PAYPAL = "paypal"
    PAYME = "payme"
    CLICK = "click"
    UZCARD = "uzcard"
    HUMO = "humo"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True, index=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    language = Column(SQLEnum(UserLanguage), default=UserLanguage.ENGLISH, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    referral_code = Column(String(50), unique=True, nullable=False, index=True)
    referred_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    balance = relationship("Balance", back_populates="user", uselist=False)
    transactions = relationship("Transaction", back_populates="user")
    orders = relationship("Order", back_populates="user")
    referrals = relationship("User", backref="referrer", remote_side=[id])
    
    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"


class Balance(Base):
    __tablename__ = "balances"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    coins = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="balance")
    
    def __repr__(self):
        return f"<Balance(user_id={self.user_id}, coins={self.coins})>"


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(SQLEnum(TransactionType), nullable=False)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    amount = Column(Float, nullable=False)  # Amount in coins
    usd_amount = Column(Float, nullable=True)  # Amount in USD for deposits
    payment_method = Column(SQLEnum(PaymentMethod), nullable=True)
    external_id = Column(String(255), nullable=True, index=True)  # Payment provider transaction ID
    description = Column(Text, nullable=True)
    meta_data = Column(JSON, nullable=True)  # JSON for additional data
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    
    # Indexes
    __table_args__ = (
        Index('ix_transactions_user_type', 'user_id', 'type'),
        Index('ix_transactions_status_created', 'status', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Transaction(user_id={self.user_id}, type={self.type}, amount={self.amount})>"


class ServiceCategory(Base):
    __tablename__ = "service_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    jap_category_id = Column(Integer, nullable=True, index=True)  # JAP API category ID if available
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    services = relationship("Service", back_populates="category")
    
    # Indexes
    __table_args__ = (
        Index('ix_service_categories_name', 'name'),
    )
    
    def __repr__(self):
        return f"<ServiceCategory(name={self.name})>"


class Service(Base):
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("service_categories.id"), nullable=False)
    jap_service_id = Column(Integer, nullable=False, unique=True, index=True)  # JAP API service ID
    name = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    service_type = Column(String(100), nullable=True)  # JAP service type (Default, Custom Comments, etc.)
    price_per_1000 = Column(Float, nullable=False)  # Price in coins per 1000 members
    jap_rate_usd = Column(Float, nullable=True)  # Original JAP rate in USD
    min_quantity = Column(Integer, default=100, nullable=False)
    max_quantity = Column(Integer, default=100000, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    
    # JAP API specific fields
    supports_refill = Column(Boolean, default=False, nullable=False)
    supports_cancel = Column(Boolean, default=False, nullable=False)
    supports_dripfeed = Column(Boolean, default=False, nullable=False)
    
    # Additional metadata
    meta_data = Column(JSON, nullable=True)  # Store additional JAP API data
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    category = relationship("ServiceCategory", back_populates="services")
    orders = relationship("Order", back_populates="service")
    
    # Indexes
    __table_args__ = (
        Index('ix_services_jap_service_id', 'jap_service_id'),
        Index('ix_services_category_active', 'category_id', 'is_active'),
        Index('ix_services_name', 'name'),
    )
    
    def __repr__(self):
        return f"<Service(name={self.name}, jap_service_id={self.jap_service_id}, price_per_1000={self.price_per_1000})>"


class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)  # Legacy service reference
    curated_service_id = Column(Integer, ForeignKey("admin_curated_services.id"), nullable=True)  # New curated service reference
    jap_order_id = Column(Integer, nullable=True, unique=True, index=True)  # JAP API order ID
    jap_service_id = Column(Integer, nullable=False, index=True)  # Direct JAP service ID for reference
    
    # Order details
    link = Column(String(1000), nullable=False)  # Social media link
    quantity = Column(Integer, nullable=False)
    charge = Column(Float, nullable=False)  # Total cost in coins
    charge_usd = Column(Float, nullable=True)  # Total cost in USD
    
    # Status and progress
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    start_count = Column(Integer, nullable=True)  # Current delivered count
    remains = Column(Integer, nullable=True)  # Remaining count to deliver
    
    # JAP API specific fields
    jap_charge = Column(Float, nullable=True)  # JAP API charge amount
    jap_currency = Column(String(10), nullable=True, default="USD")  # JAP API currency
    jap_status = Column(String(50), nullable=True)  # JAP API status string
    
    # Additional metadata
    meta_data = Column(JSON, nullable=True)  # Store additional JAP API data
    notes = Column(Text, nullable=True)  # Admin notes or user notes
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    service = relationship("Service", back_populates="orders")
    curated_service = relationship("AdminCuratedService", back_populates="orders")
    
    # Indexes
    __table_args__ = (
        Index('ix_orders_user_status', 'user_id', 'status'),
        Index('ix_orders_status_created', 'status', 'created_at'),
        Index('ix_orders_jap_order_id', 'jap_order_id'),
        Index('ix_orders_jap_service_id', 'jap_service_id'),
    )
    
    def __repr__(self):
        return f"<Order(user_id={self.user_id}, service_id={self.service_id}, jap_order_id={self.jap_order_id}, charge={self.charge})>"


class JAPBalance(Base):
    __tablename__ = "jap_balances"
    
    id = Column(Integer, primary_key=True, index=True)
    balance = Column(Float, nullable=False)  # Current balance
    currency = Column(String(10), nullable=False, default="USD")
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<JAPBalance(balance={self.balance}, currency={self.currency})>"


class Setting(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Setting(key={self.key}, value={self.value})>"


class ReferralReward(Base):
    __tablename__ = "referral_rewards"
    
    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    referred_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reward_amount = Column(Float, nullable=False)  # Amount in coins
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    is_paid = Column(Boolean, default=False, nullable=False)
    button_taps = Column(Integer, default=0, nullable=False)  # Number of button taps by referred user
    button_taps_required = Column(Integer, default=5, nullable=False)  # Required taps to complete referral
    is_completed = Column(Boolean, default=False, nullable=False)  # Whether referral requirements are met
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    referrer = relationship("User", foreign_keys=[referrer_id])
    referred = relationship("User", foreign_keys=[referred_id])
    transaction = relationship("Transaction")
    
    def __repr__(self):
        return f"<ReferralReward(referrer_id={self.referrer_id}, referred_id={self.referred_id}, reward_amount={self.reward_amount})>"


class ReferralButtonTap(Base):
    __tablename__ = "referral_button_taps"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    referral_reward_id = Column(Integer, ForeignKey("referral_rewards.id"), nullable=False)
    button_type = Column(String(50), nullable=False)  # Type of button tapped (e.g. 'main_menu', 'service', etc.)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    referral_reward = relationship("ReferralReward")
    
    # Indexes
    __table_args__ = (
        Index('ix_referral_button_taps_user_id', 'user_id'),
        Index('ix_referral_button_taps_reward_id', 'referral_reward_id'),
    )
    
    def __repr__(self):
        return f"<ReferralButtonTap(user_id={self.user_id}, button_type={self.button_type})>"


class AdminCuratedService(Base):
    __tablename__ = "admin_curated_services"
    
    id = Column(Integer, primary_key=True, index=True)
    jap_service_id = Column(Integer, nullable=False, unique=True, index=True)  # JAP API service ID
    
    # Admin-customized fields
    custom_name = Column(String(500), nullable=False)  # Custom name set by admin
    custom_description = Column(Text, nullable=True)  # Custom description set by admin
    custom_price_per_1000 = Column(Float, nullable=False)  # Custom price in coins per 1000 members
    
    # Platform and category info (extracted from JAP)
    platform = Column(String(100), nullable=True)  # e.g., instagram, youtube, tiktok
    service_type = Column(String(100), nullable=True)  # e.g., followers, likes, views
    
    # Status and ordering
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    
    # Admin tracking
    added_by_admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    added_by_admin = relationship("User")
    orders = relationship("Order", back_populates="curated_service")
    
    # Indexes
    __table_args__ = (
        Index('ix_admin_curated_services_jap_id', 'jap_service_id'),
        Index('ix_admin_curated_services_platform', 'platform'),
        Index('ix_admin_curated_services_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<AdminCuratedService(jap_service_id={self.jap_service_id}, custom_name={self.custom_name}, price={self.custom_price_per_1000})>"