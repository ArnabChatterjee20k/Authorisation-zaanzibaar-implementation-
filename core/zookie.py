"""
no encryption
the data will be still visible but if tampered the signature will change
"""

import hashlib, hmac
from datetime import datetime

FORMAT = r"%Y-%m-%d %H:%M:%S"
SECRET = "hello world"
ALGO = hashlib.md5


def encrypt(id):
    current_timestamp = datetime.now().strftime(FORMAT)
    data = f"{id}.{current_timestamp}"
    signature = hmac.new(SECRET.encode(), data.encode(), ALGO).hexdigest()
    token = f"{id}.{current_timestamp}.{signature}"
    return token


def verify(token: str):
    """
    @returns (id,token)
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise Exception("Invalid Token")
    id, timestamp, received_signature = parts
    # generating signature again for checking the validity
    data = f"{id}.{timestamp}"
    valid_signature = hmac.new(SECRET.encode(), data.encode(), ALGO).hexdigest()

    if hmac.compare_digest(received_signature, valid_signature):
        return id, timestamp

    raise Exception("Invalid token")
