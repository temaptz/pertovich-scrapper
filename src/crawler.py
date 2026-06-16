import os
import random
from time import sleep
from playwright.sync_api import BrowserContext, Page
from src.models import Product
from src.cache import exists, get_all
from src.catalog import add, catalog_write
from src.utils import page_load_and_scroll, retry
from src.logger import get_logger
from src.product import extract_product_price, extract_product_unit, extract_product_qty, extract_product_description, \
    extract_product_properties, extract_product_comments, extract_product_questions

logger = get_logger(__name__)

MAIN_URL = os.environ['MAIN_URL']
DEFAULT_TIMEOUT_MS = int(os.environ.get('DEFAULT_TIMEOUT_MS', '30000'))
RANDOM_ORDER = os.environ.get('RANDOM_ORDER') == 'true'

_products_saved = len(get_all())

# Работа с главной страницей каталога
@retry()
def process_main_catalog(browser: BrowserContext) -> None:
    main_catalog_page = browser.new_page()
    page_load_and_scroll(page=main_catalog_page, url=f'{MAIN_URL}/catalog/', timeout_ms=DEFAULT_TIMEOUT_MS)
    logger.info('Получена страница главного каталога. URL: %s, title: %s', main_catalog_page.url, main_catalog_page.title())
    links = main_catalog_page.locator('.section-catalog-list-item-link').all()
    logger.debug('Получен список категорий главного каталога. Категорий : %s', len(links))

    if RANDOM_ORDER:
        random.shuffle(links)

    for link in links:
        url = f'{MAIN_URL}{link.get_attribute('href')}'
        _process_catalog_page_recursive(browser=browser, url=url)
        sleep(random.random() * 3)

# Работа со страницей каталога: список товаров + подкаталоги
@retry()
def _process_catalog_page_recursive(browser: BrowserContext, url: str) -> None:
    page = browser.new_page()
    page_load_and_scroll(page=page, url=url, timeout_ms=DEFAULT_TIMEOUT_MS)

    # Название категории
    category_name = page.locator('h1').first.text_content()
    logger.info('Получена страница категории. Начало обхода товаров. [%s] [%s]', category_name, url)

    # Обход товаров
    _process_products_pagination(browser=browser, page=page)

    logger.debug('Завершен обход пагинации товаров в категории. [%s] [%s]', category_name, url)

    # Рекурсивный обход подкаталогов
    sub_catalog_links = page.locator('a.catalog-subsection-img').all()
    for link in sub_catalog_links:
        _process_catalog_page_recursive(browser=browser, url=f'{MAIN_URL}{link.get_attribute('href')}')

    logger.debug('Завершен обход категории. [%s] [%s]', category_name, url)

    page.close()


# Обход пагинации товаров
def _process_products_pagination(browser: BrowserContext, page: Page) -> None:
    is_pagination_available = True
    processed_urls = set()

    while is_pagination_available:
        # Получение товаров
        product_links = page.locator('[data-test="product-link"]').all()
        logger.info('Обход пагинации списка товаров. Товаров: %s', len(product_links))

        for i in product_links:
            url = f'{MAIN_URL}{i.get_attribute('href')}'
            if url not in processed_urls:
                _process_product_page(browser=browser, url=url)
                processed_urls.add(url)
                sleep(random.random() * 5)

        logger.debug('Завершена обработка товаров на странице пагинации')

        # Переход по пагинации дальше
        try:
            next_button = page.locator('button[data-test="products-next-button"]').first
            next_button.scroll_into_view_if_needed()
            next_button.click()
            sleep(DEFAULT_TIMEOUT_MS / 1000 / 2) # Ожидание загрузки пагинации
            logger.info('Совершен клик по кнопке дальше в пагинации списка товаров')
        except Exception as e:
            logger.debug('Не было перехода дальше по пагинации')
            is_pagination_available = False


# Работа со страницей товара
@retry()
def _process_product_page(browser: BrowserContext, url: str) -> None:
    global _products_saved
    if exists(url):
        logger.info('Товар уже в каталоге, пропуск. [%s]', url)
        return

    page = browser.new_page()
    try:
        page_load_and_scroll(page=page, url=url, timeout_ms=DEFAULT_TIMEOUT_MS)
        logger.info('Загружена страница товара [%s]', url)
        sleep(1)

        product = Product(
            url=url,
            name=page.locator('h1').first.text_content(),
            price=extract_product_price(page=page),
            unit=extract_product_unit(page=page),
            qty_available=extract_product_qty(page=page),
            description=extract_product_description(page=page),
            properties=extract_product_properties(page=page),
            comments=extract_product_comments(page=page),
            questions=extract_product_questions(page=page),
        )

        logger.debug('Сформирована полная карточка товара. [%s]', url)

        add(product)
        _products_saved += 1
        logger.info('Товар #%d сохранён в каталог. [%s]', _products_saved, url)

        if _products_saved <= 10:
            catalog_write()
        elif _products_saved <= 100 and _products_saved % 10 == 0:
            catalog_write()
        elif _products_saved > 100 and _products_saved % 100 == 0:
            catalog_write()
    finally:
        page.close()
