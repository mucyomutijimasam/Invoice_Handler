import os
from dotenv import load_dotenv

load_dotenv()

MTN_BASE_URL = "https://sandbox.momodeveloper.mtn.com"

MTN_API_USER = os.getenv("MTN_API_USER") # Add this
MTN_API_KEY = os.getenv("MTN_API_KEY")
MTN_COLLECTION_PRIMARY_KEY = os.getenv("MTN_COLLECTION_PRIMARY_KEY")
MTN_CALLBACK_URL = os.getenv("MTN_CALLBACK_URL")

MTN_TARGET_ENV = "sandbox"
MTN_CURRENCY = "EUR"