from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "asset-management"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    db_host: str = "mariadb-asset-management"
    db_port: int = 3306
    db_name: str = "assetdb"
    db_user: str = "assetapp"
    db_password: str = ""

    jwt_secret: str = ""
    jwt_algo: str = "HS256"
    jwt_expire_minutes: int = 480

    admin_username: str = "admin"
    admin_password: str = "admin_change_me"

    # Compliance guide (used by UI to show SSH commands)
    host_ip: str = ""
    project_path: str = ""
    ssh_user: str = ""

    password_min_length: int = 12

    @property
    def database_url(self) -> str:
        # SQLAlchemy + PyMySQL
        return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

if not settings.jwt_secret or settings.jwt_secret == "CHANGE_ME_SUPER_SECRET":
    raise ValueError(
        "JWT_SECRET must be set in .env — cannot start with default/empty value"
    )

