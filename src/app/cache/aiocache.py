from aiocache import caches

from app.core.settings import config


caches.set_config(
    {
        "default": {
            "cache": "aiocache.RedisCache",
            "endpoint": config.redis_cfg.HOST,
            "port": config.redis_cfg.PORT,
            "serializer": {"class": "aiocache.serializers.PickleSerializer"},
        }
    }
)

redis_cache = caches.get("default")
