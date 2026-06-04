import os
import random
import re
from time import sleep
from playwright.sync_api import BrowserContext, Page
from src.models import Product, ProductProperty, ProductQuestion
from src.catalog import exists, add
from src.utils import page_load_and_scroll
from src.logger import get_logger

logger = get_logger(__name__)

DOMAIN = os.environ['DOMAIN']
DEFAULT_TIMEOUT_MS = int(os.environ.get('DEFAULT_TIMEOUT_MS', '10000'))
PAGE_INTERACT_TIMEOUT_MS = 3000

# Работа с главной страницей каталога
def process_main_catalog(browser: BrowserContext) -> None:
    main_catalog_page = browser.new_page()
    page_load_and_scroll(page=main_catalog_page, url=f'{DOMAIN}/catalog/', timeout_ms=DEFAULT_TIMEOUT_MS)
    logger.info('Получена страница главного каталога. URL: %s, title: %s', main_catalog_page.url, main_catalog_page.title())
    links = main_catalog_page.locator('.section-catalog-list-item-link').all()
    logger.debug('Получен список категорий главного каталога. Категорий : %s', len(links))

    if len(links) == 0:
        logger.warning('Категории не найдены! Проверяем наличие элементов на странице...')
        body_text = main_catalog_page.locator('body').first.text_content()
        logger.debug('Body text (первые 500 символов): %s', body_text[:500] if body_text else 'ПУСТО')
        city_modal = main_catalog_page.locator('[class*="city"], [class*="region"], [class*="location"], [class*="modal"]').all()
        logger.debug('Найдено элементов с city/region/modal: %s', len(city_modal))
        h1 = main_catalog_page.locator('h1').all()
        logger.debug('H1 элементов: %s', [el.text_content() for el in h1])

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
    logger.info('Получена страница категории. Начало обхода товаров. [%s] [%s]', category_name, url)

    # Обход товаров
    _process_products_pagination(browser=browser, page=page)

    logger.debug('Завершен обход пагинации товаров в категории. [%s] [%s]', category_name, url)

    # Рекурсивный обход подкаталогов
    sub_catalog_links = page.locator('a.catalog-subsection-img').all()
    for link in sub_catalog_links:
        _process_catalog_page_recursive(browser=browser, url=f'{DOMAIN}{link.get_attribute('href')}')

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
            url = f'{DOMAIN}{i.get_attribute('href')}'
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
def _process_product_page(browser: BrowserContext, url: str) -> None:
    page = browser.new_page()
    if exists(url):
        logger.info('Товар уже в каталоге, пропуск. [%s]', url)
        page.close()
        return

    page_load_and_scroll(page=page, url=url, timeout_ms=DEFAULT_TIMEOUT_MS)
    logger.info('Загружена страница товара [%s]', url)
    sleep(1)

    product = Product(
        url=url,
        name=page.locator('h1').first.text_content(),
        price=_extract_product_price(page=page),
        unit=_extract_product_unit(page=page),
        qty_available=_extract_product_qty(page=page),
        description=_extract_product_description(page=page),
        properties=_extract_product_properties(page=page),
        comments=_extract_product_comments(page=page),
        questions=_extract_product_questions(page=page),
    )

    logger.debug('Получена карточка товара. [%s]', url)

    add(product)

    logger.debug('Завершена обработка карточки товара. [%s]', url)

    page.close()


def _extract_product_price(page: Page) -> float or None:
    try:
        price = _extract_float_from_str(page.locator('.product-page-price-block [data-test="product-gold-price"]').first.text_content())

        if price:
            logger.info('Извлечена цена товара: %s [%s]', price, page.url)
            return price
    except Exception as e:
        logger.error('Ошибка извлечения цены товара. [%s] %s', page.url, e)

    return None


def _extract_product_unit(page: Page) -> str or None:
    try:
        unit = page.locator('.product-page-price p').get_by_text(re.compile(r"за .+")).first.text_content(timeout=PAGE_INTERACT_TIMEOUT_MS).replace('за ', '')
        if unit:
            logger.info('Извлечена единица измерения товара (способ_1): %s [%s]', unit, page.url)
            return unit
    except Exception as e:
        logger.debug('Ошибка извлечения единицы измерения товара (способ_1). [%s] %s', page.url, e)

    try:
        unit = page.locator('.quantity-in-units p').last.text_content(timeout=PAGE_INTERACT_TIMEOUT_MS)
        if unit:
            logger.info('Извлечена единица измерения товара (способ_2): %s [%s]', unit, page.url)
            return unit
    except Exception as e:
        logger.debug('Ошибка извлечения единицы измерения товара (способ_2). [%s] %s', page.url, e)

    logger.error('Ошибка извлечения единицы измерения товара. [%s]', page.url)

    return None


def _extract_product_qty(page: Page) -> int or None:
    try:
        qty = _extract_int_from_str(page.locator('.available-product-remains').first.text_content())

        if qty:
            logger.info('Извлечено количество доступного товара: %s [%s]', qty, page.url)
            return qty
    except Exception as e:
        logger.error('Ошибка извлечения количества доступного товара. [%s] [%s]', page.url, e)

    return None


def _extract_product_description(page: Page) -> str or None:
    try:
        description_read_more = page.locator('.product-page-description').first.get_by_text('Показать полностью...').first
        description_read_more.click(timeout=PAGE_INTERACT_TIMEOUT_MS)
        sleep(0.3)
        logger.debug('Раскрыто описание товара. [%s]', page.url)
    except Exception as e:
        logger.debug('Ошибка раскрытия описания товара. [%s] %s', page.url, e)

    try:
        description = page.locator('.product-page-description-content').first.text_content()

        if description:
            logger.info('Извлечено описание товара. [%s] %s', page.url, description)
            return description
    except Exception as e:
        logger.error('Ошибка извлечения описания товара. [%s] %s', page.url, e)

    return None


def _extract_product_properties(page: Page) -> list[ProductProperty]:
    properties: list[ProductProperty] = []
    try:
        for item in page.locator('.product-properties-columns .properties-item').all():
            label = item.locator('.properties-item-title-content').first.text_content()
            value = item.locator('.properties-item-value').first.text_content()
            if label and value:
                properties.append(ProductProperty(label=label, value=value))

        logger.info('Извлечены характеристики товара в количестве %s [%s]', len(properties), page.url)
    except Exception as e:
        logger.error('Ошибка извлечения характеристик товара. [%s] %s', page.url, e)

    return properties


def _extract_product_comments(page: Page) -> list[str]:
    comments: list[str] = []
    try:
        comments_tab_button = page.locator('[data-test="feedback-section-reviews-tab"]').first
        comments_tab_button.scroll_into_view_if_needed(timeout=PAGE_INTERACT_TIMEOUT_MS)
        comments_tab_button.click(timeout=PAGE_INTERACT_TIMEOUT_MS)
        logger.debug('Открыта вкладка отзывов товара. [%s]', page.url)
    except Exception as e:
        logger.debug('Ошибка открытия вкладки отзывов. [%s] %s', page.url, e)

    try:
        comments_more_button_class = '.review-list .review-list-show-more-button'
        comments_more_button = page.locator(comments_more_button_class).first
        while comments_more_button:
            comments_more_button.scroll_into_view_if_needed(timeout=PAGE_INTERACT_TIMEOUT_MS)
            comments_more_button.click(timeout=PAGE_INTERACT_TIMEOUT_MS)
            sleep(DEFAULT_TIMEOUT_MS / 1000 / 2) # Ожидание загрузки пагинации
            comments_more_button = page.locator(comments_more_button_class).first
            logger.debug('Открыта следующая страница отзывов товара. [%s]', page.url)
    except Exception as e:
        logger.debug('Ошибка получения следующе страницы отзывов. [%s] %s', page.url, e)

    try:
        for comment in page.locator('.product-feedback-block [itemprop="description"]').all():
            comments.append(comment.text_content())
    except Exception as e:
        logger.debug('Ошибка извлечения отзывов. [%s] %s', page.url, e)

    if comments:
        logger.info('Извлечены %s отзывов о товаре. [%s] ', len(comments), page.url)

    return comments


def _extract_product_questions(page: Page) -> list[ProductQuestion]:
    questions: list[ProductQuestion] = []
    try:
        questions_tab_button = page.locator('[data-test="feedback-section-questions-tab-1"]').first
        questions_tab_button.scroll_into_view_if_needed(timeout=PAGE_INTERACT_TIMEOUT_MS)
        questions_tab_button.click(timeout=PAGE_INTERACT_TIMEOUT_MS)
        logger.debug('Открыта вкладка вопросов о товаре. [%s]', page.url)
    except Exception as e:
        logger.debug('Ошибка открытия вкладки вопросов о товаре. [%s] %s', page.url, e)

    try:
        questions_more_button_class = '.question-list-show-more-button'
        questions_more_button = page.locator(questions_more_button_class).first
        while questions_more_button:
            questions_more_button.scroll_into_view_if_needed(timeout=PAGE_INTERACT_TIMEOUT_MS)
            questions_more_button.click(timeout=PAGE_INTERACT_TIMEOUT_MS)
            sleep(DEFAULT_TIMEOUT_MS / 1000 / 2) # Ожидание загрузки пагинации
            questions_more_button = page.locator(questions_more_button_class).first
            logger.debug('Открыта следующая страница вопросов о товаре. [%s]', page.url)
    except Exception as e:
        logger.debug('Ошибка получения следующей страницы вопросов о товаре. [%s] %s', page.url, e)

    try:
        for q in page.locator('.question-list ul li').all():
            questions.append(ProductQuestion(
                question=q.locator('.npp-feedback-comment>p').first.text_content(),
                answer=q.locator('.npp-review-response-list .npp-feedback-comment>p').first.text_content(),
            ))
    except Exception as e:
        logger.debug('Ошибка извлечения вопросов о товаре. [%s] %s', page.url, e)

    if questions:
        logger.info('Извлечены %s вопросов о товаре. [%s]', len(questions), page.url)

    return questions


def _extract_int_from_str(text: str) -> int or None:
    digits = re.sub(r'\D', '', text)
    if digits:
        value = int(digits)
        logger.debug('Извлечено число "%s" из строки "%s"', value, text)
        return value
    return None


def _extract_float_from_str(text: str) -> float | None:
    cleaned = re.sub(r'[^\d.,]', '', text).replace(',', '.')
    if cleaned:
        value = float(cleaned)
        logger.debug('Извлечено число с плавающей точкой "%s" из строки "%s"', value, text)
        return value
    return None
