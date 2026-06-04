import json
import shelve
from pathlib import Path

from src.models import Catalog, Product
from src.logger import get_logger

logger = get_logger(__name__)

CATALOG_PATH = Path(__file__).resolve().parent.parent / 'catalog' / 'catalog.json'
SHELVE_PATH = str(Path(__file__).resolve().parent.parent / 'catalog' / 'products_cache')


def exists(url: str) -> bool:
    with shelve.open(SHELVE_PATH) as db:
        return url in db


def add(product: Product) -> None:
    try:
        with shelve.open(SHELVE_PATH) as db:
            db[product.url] = product.model_dump()
        logger.info('Товар добавлен в кэш. [%s]', product.url)
    except Exception as e:
        logger.error('Ошибка добавления товара в кэш. [%s] %s', product.url, e)


def catalog_write() -> None:
    try:
        products = []
        with shelve.open(SHELVE_PATH) as db:
            for key in db:
                products.append(Product(**db[key]))

        catalog = Catalog(products=products)
        CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CATALOG_PATH.write_text(
            json.dumps(catalog.model_dump(), indent=2, ensure_ascii=False) + '\n',
            encoding='utf-8',
        )
        logger.info('Каталог записан. Товаров: %d', len(products))
    except Exception as e:
        logger.error('Ошибка записи каталога. %s', e)
