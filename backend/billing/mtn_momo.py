import requests
import uuid
import os


class MTNMoMoClient:

    def __init__(self):
        self.base_url = os.getenv("MTN_MOMO_BASE_URL")
        self.subscription_key = os.getenv("MTN_MOMO_SUBSCRIPTION_KEY")
        self.api_key = os.getenv("MTN_MOMO_API_KEY")

    def request_payment(self, phone_number, amount, reference):
        """
        Initiates a payment request to user phone.
        """
        transaction_id = str(uuid.uuid4())

        headers = {
            "X-Reference-Id": transaction_id,
            "X-Target-Environment": "sandbox",
            "Ocp-Apim-Subscription-Key": self.subscription_key,
            "Content-Type": "application/json",
        }

        payload = {
            "amount": str(amount),
            "currency": "RWF",
            "externalId": reference,
            "payer": {
                "partyIdType": "MSISDN",
                "partyId": phone_number
            },
            "payerMessage": "Invoice OCR Credit Top-Up",
            "payeeNote": "SaaS Credit Purchase"
        }

        response = requests.post(
            f"{self.base_url}/collection/v1_0/requesttopay",
            json=payload,
            headers=headers
        )

        return transaction_id, response.status_code, response.text
