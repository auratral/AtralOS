from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:Password123@localhost:5432/atralos"
    REDIS_URL: str = "redis://localhost:6379/0"
    ENCRYPTION_KEY: str = "g4k5H8j3F6d2S1a9Q8w7E6r5T4y3U2i1o0p9O8i7U6y5T4r3E2w1Q0=="
    JWT_SECRET: str = "atralos_jwt_secret_key_2026_secure_hash_sha256"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    SYS_CRYPTO_PASSPHRASE: str = "AuratralHospitalOSSecurePIIKey2026!"
    KMS_PASSPHRASE: str = "AuratralHospitalOSSecureKMSKey2026!"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
