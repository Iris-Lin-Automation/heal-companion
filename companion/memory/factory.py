"""按环境选择存储。线上配置了 Supabase 就走数据库，测试可替换 get_store。"""

from __future__ import annotations

import os

from companion.memory.store import MemoryStore


def supabase_configured() -> bool:
    return bool(
        (os.getenv("SUPABASE_URL") or "").strip()
        and (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    )


def get_store(user_id: str):
    if supabase_configured():
        from companion.memory.supabase_store import SupabaseStore

        return SupabaseStore(user_id)
    return MemoryStore(user_id)
