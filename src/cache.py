from pathlib import Path

from diskcache import Cache

from src.models import Product
from src.logger import get_logger

logger = get_logger(__name__)

CACHE_DIR = str(Path(__file__).resolve().parent.parent / 'temp' / 'products_cache')
_cache = Cache(directory=CACHE_DIR)


def exists(url: str) -> bool:
    return url in _cache


def add(product: Product) -> None:
    _cache[product.url] = product.model_dump()
    logger.info('Товар добавлен в кэш. [%s]', product.url)


def get_all() -> list[Product]:
    return [Product(**_cache[key]) for key in _cache]


def flush() -> None:
    _cache.clear()
    logger.info('Кэш очищен')
