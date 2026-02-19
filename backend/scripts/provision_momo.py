# scripts/provision_momo.py
import requests
import uuid
import os
from dotenv import load_dotenv, set_key
from pathlib import Path

# Load existing .env
env_path = Path(".env")
load_dotenv(dotenv_path=env_path)

PRIMARY_KEY = os.getenv("MTN_COLLECTION_PRIMARY_KEY")
BASE_URL = "https://sandbox.momodeveloper.mtn.com"

def provision_sandbox():
    if not PRIMARY_KEY:
        print("❌ Error: MTN_COLLECTION_PRIMARY_KEY not found in .env")
        return

    # STEP 1: Create an API User (UUID)
    api_user = str(uuid.uuid4())
    print(f"--- 🛠️ Provisioning started for User: {api_user} ---")

    headers = {
        "X-Reference-Id": api_user,
        "Ocp-Apim-Subscription-Key": PRIMARY_KEY,
        "Content-Type": "application/json",
    }
    
    # Register the user
    response = requests.post(
        f"{BASE_URL}/v1_0/apiuser",
        json={"providerCallbackHost": "localhost"}, # Not critical for sandbox
        headers=headers
    )

    if response.status_code != 201:
        print(f"❌ Failed to create API User: {response.text}")
        return

    print("✅ API User Created Successfully.")

    # STEP 2: Generate API Key
    key_response = requests.post(
        f"{BASE_URL}/v1_0/apiuser/{api_user}/apikey",
        headers={"Ocp-Apim-Subscription-Key": PRIMARY_KEY}
    )

    if key_response.status_code != 201:
        print(f"❌ Failed to generate API Key: {key_response.text}")
        return

    api_key = key_response.json().get("apiKey")
    print(f"✅ API Key Generated: {api_key}")

    # STEP 3: Save to .env automatically
    set_key(str(env_path), "MTN_API_USER", api_user)
    set_key(str(env_path), "MTN_API_KEY", api_key)
    
    print("\n🚀 SUCCESS! Your .env has been updated.")
    print("You can now restart your server to use the new credentials.")

if __name__ == "__main__":
    provision_sandbox()