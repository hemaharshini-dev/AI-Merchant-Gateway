from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    GROQ_API_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./ai_merchant_gateway.db"

    class Config:
        env_file = ".env"

settings = Settings()
