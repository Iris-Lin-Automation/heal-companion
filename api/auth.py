"""身份只来自已验证的 Supabase JWT。客户端传来的 user_id 一律不算数。"""

from __future__ import annotations

import os
from typing import Annotated, Any, Optional

import jwt
from fastapi import Header, HTTPException
from jwt import PyJWKClient

_jwks_clients: dict[str, PyJWKClient] = {}


def _bearer(authorization: Optional[str]) -> str:
    if not authorization:
        return ""
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return ""
    return token.strip()


def _decode(token: str, key: Any, algorithms: list[str]) -> str:
    # 本机时钟若偏慢，iat 会落在「未来」，默认 30s 不够。
    payload = jwt.decode(
        token,
        key,
        algorithms=algorithms,
        audience="authenticated",
        leeway=300,
    )
    sub = str(payload.get("sub") or "").strip()
    if not sub or len(sub) > 64:
        raise jwt.InvalidTokenError("missing sub")
    return sub


def _jwks(url: str) -> PyJWKClient:
    client = _jwks_clients.get(url)
    if client is None:
        client = PyJWKClient(f"{url}/auth/v1/.well-known/jwks.json")
        _jwks_clients[url] = client
    return client


def verify_access_token(token: str) -> str:
    """HS256（JWT Secret）或新版非对称签名（JWKS）都接受。返回 auth.users.id。"""
    secret = (os.getenv("SUPABASE_JWT_SECRET") or "").strip()
    url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
    if not secret and not url:
        raise HTTPException(status_code=503, detail="auth not configured")

    if secret:
        try:
            return _decode(token, secret, ["HS256"])
        except jwt.PyJWTError:
            pass

    if url:
        try:
            signing_key = _jwks(url).get_signing_key_from_jwt(token)
            return _decode(token, signing_key.key, ["RS256", "ES256"])
        except Exception:
            pass

    raise HTTPException(status_code=401, detail="login required")


def require_user_id(authorization: Annotated[Optional[str], Header()] = None) -> str:
    token = _bearer(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="login required")
    return verify_access_token(token)


def require_v1_user(authorization: Optional[str] = None) -> str:
    """产品用户走 JWT。服务密钥只能进固定目录 v1_service，不能指定别人。"""
    token = _bearer(authorization)
    expected = (os.getenv("HEAL_V1_KEY") or "").strip()
    if expected and token == expected:
        return "v1_service"
    if not token:
        raise HTTPException(status_code=401, detail="login required")
    return verify_access_token(token)
