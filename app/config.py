from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str = "postgresql+psycopg://invoice:invoice@localhost:5432/invoice_engine"
    company_name: str = "Demo Manufacturing Co."
    company_tax_id: str = "00.000.000/0001-00"


settings = Settings()
