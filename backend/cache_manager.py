import redis
import json
import logging

logger = logging.getLogger("ShaanU_Cache")

class ShaanUCache:
    """
    Abstraction layer for Redis caching.
    Supports complex objects by JSON serialization to optimize API response times.
    """
    _redis_conn = None

    @classmethod
    def init_redis(cls):
        """
        Initializes the connection to the local Redis server.
        Falls back gracefully if the service is unavailable.
        """
        try:
            cls._redis_conn = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            cls._redis_conn.ping()
            logger.info("Successfully established ShaanU Redis bridge.")
        except Exception as e:
            logger.warning(f"Redis fallback to null-cache: {e}")
            cls._redis_conn = None

    @classmethod
    def get_value(cls, key):
        """Retrieves and deserializes data from the cache."""
        if not cls._redis_conn: return None
        data = cls._redis_conn.get(key)
        return json.loads(data) if data else None

    @classmethod
    def set_value(cls, key, value, timeout=3600):
        """Serializes and stores data with a specific expiry time."""
        if not cls._redis_conn: return False
        cls._redis_conn.setex(key, timeout, json.dumps(value))
        return True

    @classmethod
    def delete_key(cls, key):
        """Invalidates specific cache keys."""
        if not cls._redis_conn: return
        cls._redis_conn.delete(key)