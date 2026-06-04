import os
from dotenv import load_dotenv

# Load env variables from the project root (.env is one level up from /backend)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(ROOT_DIR, ".env")
load_dotenv(dotenv_path=dotenv_path)

class Config:
    BACKEND_SECRET_TOKEN = os.getenv("BACKEND_SECRET_TOKEN")
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
    NEXTAUTH_URL = os.getenv("NEXTAUTH_URL", "http://localhost:3000")
    POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
    
    @classmethod
    def validate(cls):
        if not cls.BACKEND_SECRET_TOKEN:
            print("WARNING: BACKEND_SECRET_TOKEN is not configured! Requests to backend API will fail verification.")
        if (not cls.POLLINATIONS_API_KEY or cls.POLLINATIONS_API_KEY == "YOUR_POLLINATIONS_SK_KEY_HERE") and not cls.HUGGINGFACE_API_KEY:
            print("INFO: No image API keys configured. Using AI Horde (Free/Anonymous) as fallback.")
        print(f"Backend config loaded: HOST={cls.HOST}, PORT={cls.PORT}, NEXTAUTH_URL={cls.NEXTAUTH_URL}")

config = Config()
config.validate()
