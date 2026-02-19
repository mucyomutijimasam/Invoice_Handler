# auth/models.py

from pydantic import BaseModel

class UserRegister(BaseModel):
    username: str
    password: str
    tenant_id: str


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
