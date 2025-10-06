from base64 import urlsafe_b64encode, urlsafe_b64decode
from hashlib import blake2b
from hmac import compare_digest
from fastapi import HTTPException, Request
from secrets import token_urlsafe

csrf_key: str = None


def initialize(key: str):
    global csrf_key
    csrf_key = key


def get_token(request: Request, allow_generate=True):
    if not (id := request.session.get("id")):
        if not allow_generate:
            raise HTTPException(401, "No session!")
        id = token_urlsafe(18)
        request.session["id"] = id
    return (
        urlsafe_b64encode(
            blake2b(urlsafe_b64decode(id), key=urlsafe_b64decode(csrf_key), digest_size=36).digest()
        )
        .rstrip(b"=")
        .decode("ascii")
    )


def validate_token(request: Request, csrf_token: str):
    expected_token = get_token(request, allow_generate=False)
    if not compare_digest(expected_token, csrf_token):
        raise HTTPException(401, "Invalid CSRF token!")
