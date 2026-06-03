import json
from pathlib import Path

from src.models import Catalog, Product
from src.logger import get_logger

logger = get_logger(__name__)

CATALOG_PATH = Path(__file__).resolve().parent.parent / 'catalog' / 'catalog.json'


def _read_catalog() -> Catalog:
    try:
        raw = CATALOG_PATH.read_text(encoding='utf-8').strip()
        if not raw:
            return Catalog(products=[])
        return Catalog.model_validate_json(raw)
    except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
        logger.error('Ошибка чтения каталога, создаётся новая структура. %s', e)
        return Catalog(products=[])


def _write_catalog(catalog: Catalog) -> None:
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = catalog.model_dump()
    CATALOG_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + '\n',
        encoding='utf-8',
    )


def exists(url: str) -> bool:
    catalog = _read_catalog()
    return any(p.url == url for p in catalog.products)


def add(product: Product) -> None:
    try:
        catalog = _read_catalog()
        if any(p.url == product.url for p in catalog.products):
            logger.info('Товар уже в каталоге, пропуск. [%s]', product.url)
            return
        catalog.products.append(product)
        _write_catalog(catalog)
        logger.info('Товар добавлен в каталог. [%s]', product.url)
    except Exception as e:
        logger.error('Ошибка добавления товара в каталог. [%s] %s', product.url, e)
