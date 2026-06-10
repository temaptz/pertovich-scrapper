import json
from pathlib import Path

from src.models import Catalog
from src.cache import exists, add as cache_add, get_all
from src.logger import get_logger

logger = get_logger(__name__)

CATALOG_PATH = Path(__file__).resolve().parent.parent / 'catalog' / 'catalog.json'


def add(product) -> None:
    try:
        if exists(product.url):
            logger.info('Товар уже в кэше, пропуск. [%s]', product.url)
            return
        cache_add(product)
    except Exception as e:
        logger.error('Ошибка добавления товара в кэш. [%s] %s', product.url, e)


def catalog_write() -> None:
    try:
        products = get_all()
        catalog = Catalog(products=products)
        CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CATALOG_PATH.write_text(
            json.dumps(catalog.model_dump(), indent=2, ensure_ascii=False) + '\n',
            encoding='utf-8',
        )
        logger.info('Каталог записан. Товаров: %d', len(products))
    except Exception as e:
        logger.error('Ошибка записи каталога. %s', e)
