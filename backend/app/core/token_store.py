"""
JWT token lifecycle management via Redis.
Handles refresh token storage, rotation, and access token blacklisting.
"""

from abc import ABC, abstractmethod

from app.core.config import settings

REFRESH_PREFIX = "refresh_token:"
BLACKLIST_PREFIX = "blacklist:"
USER_REFRESH_PREFIX = "user_refresh:"


class TokenStore(ABC):
    @abstractmethod
    async def store_refresh_token(self, jti: str, user_id: str, ttl_seconds: int) -> None:
        pass

    @abstractmethod
    async def get_refresh_token_user(self, jti: str) -> str | None:
        pass

    @abstractmethod
    async def revoke_refresh_token(self, jti: str, user_id: str | None = None) -> None:
        pass

    @abstractmethod
    async def revoke_all_user_refresh_tokens(self, user_id: str) -> None:
        pass

    @abstractmethod
    async def blacklist_access_token(self, jti: str, ttl_seconds: int) -> None:
        pass

    @abstractmethod
    async def is_access_token_blacklisted(self, jti: str) -> bool:
        pass


class RedisTokenStore(TokenStore):
    async def store_refresh_token(self, jti: str, user_id: str, ttl_seconds: int) -> None:
        from app.core.redis import get_redis

        redis = await get_redis()
        pipe = redis.pipeline()
        pipe.setex(f"{REFRESH_PREFIX}{jti}", ttl_seconds, user_id)
        pipe.sadd(f"{USER_REFRESH_PREFIX}{user_id}", jti)
        pipe.expire(f"{USER_REFRESH_PREFIX}{user_id}", ttl_seconds)
        await pipe.execute()

    async def get_refresh_token_user(self, jti: str) -> str | None:
        from app.core.redis import get_redis

        redis = await get_redis()
        return await redis.get(f"{REFRESH_PREFIX}{jti}")

    async def revoke_refresh_token(self, jti: str, user_id: str | None = None) -> None:
        from app.core.redis import get_redis

        redis = await get_redis()
        if user_id is None:
            user_id = await redis.get(f"{REFRESH_PREFIX}{jti}")
        pipe = redis.pipeline()
        pipe.delete(f"{REFRESH_PREFIX}{jti}")
        if user_id:
            pipe.srem(f"{USER_REFRESH_PREFIX}{user_id}", jti)
        await pipe.execute()

    async def revoke_all_user_refresh_tokens(self, user_id: str) -> None:
        from app.core.redis import get_redis

        redis = await get_redis()
        jtis = await redis.smembers(f"{USER_REFRESH_PREFIX}{user_id}")
        if not jtis:
            return
        pipe = redis.pipeline()
        for jti in jtis:
            pipe.delete(f"{REFRESH_PREFIX}{jti}")
        pipe.delete(f"{USER_REFRESH_PREFIX}{user_id}")
        await pipe.execute()

    async def blacklist_access_token(self, jti: str, ttl_seconds: int) -> None:
        from app.core.redis import get_redis

        redis = await get_redis()
        await redis.setex(f"{BLACKLIST_PREFIX}{jti}", max(ttl_seconds, 1), "1")

    async def is_access_token_blacklisted(self, jti: str) -> bool:
        from app.core.redis import get_redis

        redis = await get_redis()
        return await redis.exists(f"{BLACKLIST_PREFIX}{jti}") > 0


class InMemoryTokenStore(TokenStore):
    """In-memory store for unit tests."""

    def __init__(self) -> None:
        self._refresh: dict[str, tuple[str, int]] = {}
        self._user_refresh: dict[str, set[str]] = {}
        self._blacklist: set[str] = set()

    async def store_refresh_token(self, jti: str, user_id: str, ttl_seconds: int) -> None:
        self._refresh[jti] = (user_id, ttl_seconds)
        self._user_refresh.setdefault(user_id, set()).add(jti)

    async def get_refresh_token_user(self, jti: str) -> str | None:
        entry = self._refresh.get(jti)
        return entry[0] if entry else None

    async def revoke_refresh_token(self, jti: str, user_id: str | None = None) -> None:
        entry = self._refresh.pop(jti, None)
        uid = user_id or (entry[0] if entry else None)
        if uid and uid in self._user_refresh:
            self._user_refresh[uid].discard(jti)

    async def revoke_all_user_refresh_tokens(self, user_id: str) -> None:
        jtis = self._user_refresh.pop(user_id, set())
        for jti in jtis:
            self._refresh.pop(jti, None)

    async def blacklist_access_token(self, jti: str, ttl_seconds: int) -> None:
        self._blacklist.add(jti)

    async def is_access_token_blacklisted(self, jti: str) -> bool:
        return jti in self._blacklist


_token_store: TokenStore | None = None


def _init_token_store() -> TokenStore:
    if settings.USE_MEMORY_TOKEN_STORE:
        return InMemoryTokenStore()
    return RedisTokenStore()


def get_token_store() -> TokenStore:
    global _token_store
    if _token_store is None:
        _token_store = _init_token_store()
    return _token_store


def set_token_store(store: TokenStore) -> None:
    global _token_store
    _token_store = store
