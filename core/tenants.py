from fastapi import APIRouter
import base64
from .zookie import encrypt
import random

tenant_router = APIRouter()


# TODO: return the api key
# TODO: turn this to a post route and have proper validation
@tenant_router.get("/")
def register():
    random_char = random.randbytes(10)
    api_key = base64.urlsafe_b64encode(random_char).decode()
    return encrypt(api_key)
