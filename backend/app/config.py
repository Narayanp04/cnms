"""ConnectXperts NMS - Application Configuration"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "ConnectXperts NMS"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Enterprise Network Ping Monitoring Platform"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./cnms_dev.db"
    DATABASE_URL_SYNC: str = "sqlite:///./cnms_dev.db"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    
    # Redis
    REDIS_URL: str = "redis://:cnms-redis-pass@redis:6379/0"
    REDIS_CELERY_URL: str = "redis://:cnms-redis-pass@redis:6379/1"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://:cnms-redis-pass@redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://:cnms-redis-pass@redis:6379/1"
    
    # JWT Authentication
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production-cnms-2024"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Monitoring
    DEFAULT_POLLING_INTERVAL: int = 30  # seconds
    PING_TIMEOUT: float = 5.0  # seconds
    PING_COUNT: int = 4
    PING_THREADS: int = 50
    MAX_RETRIES: int = 3
    HISTORY_RETENTION_DAYS: int = 365
    ALERT_COOLDOWN_SECONDS: int = 300  # 5 minutes
    
    # WhatsApp Cloud API
    WHATSAPP_API_URL: str = "https://graph.facebook.com/v18.0"
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "alerts@cnms.local"
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    
    # SLA Settings
    SLA_TARGET_PERCENTAGE: float = 99.9  # 99.9% uptime target
    
    # High Latency Threshold (ms)
    HIGH_LATENCY_THRESHOLD: int = 150
    CRITICAL_LATENCY_THRESHOLD: int = 300
    
    # Packet Loss Threshold (%)
    HIGH_PACKET_LOSS_THRESHOLD: float = 5.0
    CRITICAL_PACKET_LOSS_THRESHOLD: float = 20.0
    
    # Backup
    BACKUP_DIR: str = "/data/backups"
    BACKUP_RETENTION_DAYS: int = 30
    AUTO_BACKUP_ENABLED: bool = True
    AUTO_BACKUP_INTERVAL_HOURS: int = 24
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "https://cnms.local"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
