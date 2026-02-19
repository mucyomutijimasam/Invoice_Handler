import requests
import uuid
import base64
from billing import mtn_config

class MTNMoMoClient:
    def __init__(self):
        self.base_url = mtn_config.MTN_BASE_URL
        self.api_user = mtn_config.MTN_API_USER
        self.api_key = mtn_config.MTN_API_KEY
        self.subscription_key = mtn_config.MTN_COLLECTION_PRIMARY_KEY
        self.currency = mtn_config.MTN_CURRENCY
        self.target_env = mtn_config.MTN_TARGET_ENV

    def get_access_token(self):
        """Exchange API User & Key for a temporary Bearer Token."""
        auth_str = f"{self.api_user}:{self.api_key}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()

        headers = {
            "Ocp-Apim-Subscription-Key": self.subscription_key,
            "Authorization": f"Basic {encoded_auth}"
        }

        response = requests.post(f"{self.base_url}/collection/token/", headers=headers)
        
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"❌ Token Error: {response.text}")
            return None

    def request_to_pay(self, phone_number: str, amount: float, external_id: str):
        """Now correctly indented under the class!"""
        token = self.get_access_token()
        if not token:
            return None, 500

        reference_id = str(uuid.uuid4())

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Reference-Id": reference_id,
            "X-Target-Environment": self.target_env,
            "Ocp-Apim-Subscription-Key": self.subscription_key,
            "Content-Type": "application/json",
            "X-Callback-Url": mtn_config.MTN_CALLBACK_URL
        }

        payload = {
            "amount": str(amount),
            "currency": self.currency,
            "externalId": external_id,
            "payer": {
                "partyIdType": "MSISDN",
                "partyId": phone_number
            },
            "payerMessage": "Invoice Credits",
            "payeeNote": "Invox SaaS"
        }

        response = requests.post(
            f"{self.base_url}/collection/v1_0/requesttopay",
            headers=headers,
            json=payload
        )
        
        if response.status_code != 202:
            print(f"MTN Request failed: {response.status_code} - {response.text}")

        return reference_id, response.status_code