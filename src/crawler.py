import logging
import json
import random
from time import sleep
from playwright.sync_api import BrowserContext, Page
from src.models import Product, ProductProperty, ProductQuestion
from src.utils import page_load_and_scroll, retry
import coloredlogs

coloredlogs.install(
    level='DEBUG',
    fmt='%(asctime)s [%(levelname)s] %(message)s',
    isatty=True,
)

import sys
print(sys.stderr.isatty())

logging.debug('debug')
logging.info('info')
logging.warning('warning')
logging.error('error')
logging.critical('critical')

DOMAIN = ''
DEFAULT_TIMEOUT_MS = 10_000

# Работа с главной страницей каталога
def process_main_catalog(browser: BrowserContext) -> None:
    main_catalog_page = browser.new_page()
    page_load_and_scroll(page=main_catalog_page, url=f'{DOMAIN}/catalog/', timeout_ms=DEFAULT_TIMEOUT_MS)
    logging.info('Получена страница главного каталога')
    links = main_catalog_page.locator('.section-catalog-list-item-link').all()
    logging.debug('Получен список категорий главного каталога. Категорий : %s', len(links))

    for link in links:
        url = f'{DOMAIN}{link.get_attribute('href')}'
        _process_catalog_page_recursive(browser=browser, url=url)
        sleep(random.random() * 5)

# Работа со страницей каталога: список товаров + подкаталоги
def _process_catalog_page_recursive(browser: BrowserContext, url: str) -> None:
    page = browser.new_page()
    page_load_and_scroll(page=page, url=url, timeout_ms=DEFAULT_TIMEOUT_MS)

    # Название категории
    category_name = page.locator('h1').first.text_content()
    logging.info('Получена страница категории. Начало обхода товаров. [%s] [%s]', category_name, url)

    # Обход товаров
    _process_products_pagination(browser=browser, page=page)

    logging.debug('Завершен обход пагинации товаров в категории. [%s] [%s]', category_name, url)

    # Рекурсивный обход подкаталогов
    sub_catalog_links = page.locator('a.catalog-subsection-img').all()
    for link in sub_catalog_links:
        _process_catalog_page_recursive(browser=browser, url=f'{DOMAIN}{link.get_attribute('href')}')

    logging.debug('Завершен обход категории. [%s] [%s]', category_name, url)

    page.close()


# Обход пагинации товаров
def _process_products_pagination(browser: BrowserContext, page: Page) -> None:
    is_pagination_available = True
    processed_urls = set()

    while is_pagination_available:
        # Получение товаров
        product_links = page.locator('[data-test="product-link"]').all()
        logging.info('Обход пагинации списка товаров. Товаров: %s', len(product_links))

        for i in product_links:
            url = f'{DOMAIN}{i.get_attribute('href')}'
            if url not in processed_urls:
                _process_product_page(browser=browser, url=url)
                processed_urls.add(url)
                sleep(random.random() * 5)

        logging.debug('Завершена обработка товаров на странице пагинации')

        # Переход по пагинации дальше
        try:
            next_button = page.locator('button[data-test="products-next-button"]').first
            next_button.scroll_into_view_if_needed()
            next_button.click()
            sleep(DEFAULT_TIMEOUT_MS / 1000 / 2) # Ожидание загрузки пагинации
            logging.info('Совершен клик по кнопке дальше в пагинации списка товаров')
        except Exception as e:
            logging.debug('Не было перехода дальше по пагинации')
            is_pagination_available = False


# Работа со страницей товара
def _process_product_page(browser: BrowserContext, url: str) -> None:
    page = browser.new_page()
    page_load_and_scroll(page=page, url=url, timeout_ms=DEFAULT_TIMEOUT_MS)
    logging.info('Загружена страница товара [%s]', url)

    # Название товара
    product = Product(
        url=url,
        name=page.locator('h1').first.text_content(),
        price=_extract_product_price(page=page),
        price_unit=_extract_product_price_unit(page=page),
        qty_available=_extract_product_qty(page=page),
        description=_extract_product_description(page=page),
        properties=_extract_product_properties(page=page),
        comments=_extract_product_comments(page=page),
        questions=_extract_product_questions(page=page),
    )

    logging.debug('Получена карточка товара. [%s]', url)

    print(json.dumps(product, indent=2, ensure_ascii=False))

    logging.debug('Завершена обработка карточки товара. [%s]', url)

    page.close()


def _extract_product_price(page: Page) -> int or None:
    try:
        price = _extract_int_from_str(page.locator('[data-test="product-gold-price"]').first.text_content())

        if price:
            logging.info('Извлечена цена товара: %s [%s]', price, page.url)
            return price
    except Exception as e:
        logging.error('Ошибка извлечения цены товара. [%s] %s', page.url, e)

    return None


def _extract_product_price_unit(page: Page) -> str or None:
    return None


def _extract_product_qty(page: Page) -> int or None:
    try:
        qty = _extract_int_from_str(page.locator('.available-product-remains').first.text_content())

        if qty:
            logging.info('Извлечено количество доступного товара: %s [%s]', qty, page.url)
            return qty
    except Exception as e:
        logging.error('Ошибка извлечения количества доступного товара. [%s] [%s]', page.url, e)

    return None


def _extract_product_description(page: Page) -> str or None:
    try:
        description_read_more = page.locator('.product-page-description').first.get_by_text('Показать полностью...').first
        description_read_more.click()
        sleep(0.3)
        logging.debug('Раскрыто описание товара. [%s]', page.url)
    except Exception as e:
        logging.debug('Ошибка раскрытия описания товара. [%s] %s', page.url, e)

    try:
        description = page.locator('.product-page-description-content').first.text_content()

        if description:
            logging.info('Извлечено описание товара. [%s] %s', page.url, description)
            return description
    except Exception as e:
        logging.error('Ошибка извлечения описания товара. [%s] %s', page.url, e)

    return None


def _extract_product_properties(page: Page) -> list[ProductProperty]:
    properties: list[ProductProperty] = []
    try:
        for item in page.locator('.product-properties-columns .properties-item').all():
            label = item.locator('.properties-item-title-content').first.text_content()
            value = item.locator('.properties-item-value').first.text_content()
            if label and value:
                properties.append(ProductProperty(label=label, value=value))

        logging.info('Извлечены характеристики товара в количестве %s [%s]', len(properties), page.url)
    except Exception as e:
        logging.error('Ошибка извлечения характеристик товара. [%s] %s', page.url, e)

    return properties


def _extract_product_comments(page: Page) -> list[str]:
    comments: list[str] = []
    try:
        comments_tab_button = page.locator('[data-test="feedback-section-reviews-tab"]').first
        comments_tab_button.scroll_into_view_if_needed()
        comments_tab_button.click()
        logging.debug('Открыта вкладка комментариев товара. [%s]', page.url)
    except Exception as e:
        logging.debug('Ошибка открытия вкладки комментариев. [%s] %s', page.url, e)

    try:
        comments_more_button_class = '.review-list .review-list-show-more-button'
        comments_more_button = page.locator(comments_more_button_class).first
        while comments_more_button:
            comments_more_button.scroll_into_view_if_needed()
            comments_more_button.click()
            sleep(DEFAULT_TIMEOUT_MS / 1000 / 2) # Ожидание загрузки пагинации
            comments_more_button = page.locator(comments_more_button_class).first
            logging.debug('Открыта следующая страница комментариев товара. [%s]', page.url)
    except Exception as e:
        logging.debug('Ошибка получения следующе страницы комментариев. [%s] %s', page.url, e)

    try:
        for comment in page.locator('.product-feedback-block [itemprop="description"]').all():
            comments.append(comment.text_content())
    except Exception as e:
        logging.debug('Ошибка извлечения комментариев. [%s] %s', page.url, e)

    if comments:
        logging.info('Извлечены %s комментариев товара. [%s] ', len(comments), page.url)

    return comments


def _extract_product_questions(page: Page) -> list[ProductQuestion]:
    questions: list[ProductQuestion] = []
    try:
        questions_tab_button = page.locator('[data-test="feedback-section-questions-tab-1"]').first
        questions_tab_button.scroll_into_view_if_needed()
        questions_tab_button.click()
        logging.debug('Открыта вкладка вопросов о товаре. [%s]', page.url)
    except Exception as e:
        logging.debug('Ошибка открытия вкладки вопросов о товаре. [%s] %s', page.url, e)

    try:
        questions_more_button_class = '.question-list-show-more-button'
        questions_more_button = page.locator(questions_more_button_class).first
        while questions_more_button:
            questions_more_button.scroll_into_view_if_needed()
            questions_more_button.click()
            questions_more_button = page.locator(questions_more_button_class).first
            logging.debug('Открыта следующая страница вопросов о товаре. [%s]', page.url)
    except Exception as e:
        logging.debug('Ошибка получения следующей страницы вопросов о товаре. [%s] %s', page.url, e)

    try:
        for q in page.locator('.question-tab-content [itemprop="description"]').all():
            questions.append(ProductQuestion(
                question=q.locator('.npp-feedback-comment p').text_content(),
                answer=q.locator('.npp-review-response-list p').text_content(),
            ))
    except Exception as e:
        logging.debug('Ошибка извлечения вопросов о товаре. [%s] %s', page.url, e)

    if questions:
        logging.info('Извлечены %s вопросов о товаре. [%s]', len(questions), page.url)

    return questions


def _extract_int_from_str(text: str) -> int or None:
    import re
    if match := re.search(r'\d+', text):
        if value := int(match.group()):
            logging.debug('Извлечено число "%s" из строки "%s"', value, text)
            return value

    return None
