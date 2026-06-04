import os
import re
from time import sleep
from playwright.sync_api import Page
from src.logger import get_logger
from src.models import ProductProperty, ProductQuestion

PAGE_INTERACT_TIMEOUT_MS = 3000
DEFAULT_TIMEOUT_MS = int(os.environ.get('DEFAULT_TIMEOUT_MS', '30000'))
logger = get_logger(__name__)


def extract_product_price(page: Page) -> float or None:
    try:
        if price_dirty := page.locator('.product-page-price-block [data-test="product-gold-price"]').first.text_content():
            if cleaned := re.sub(r'[^\d.,]', '', price_dirty).replace(',', '.'):
                if price := float(cleaned):
                    logger.info('Извлечена цена товара: %s из строки "%s" [%s]', price, price_dirty, page.url)
                    return price
    except Exception as e:
        logger.error('Ошибка извлечения цены товара. [%s] %s', page.url, e)

    return None


def extract_product_unit(page: Page) -> str or None:
    error = None

    try:
        unit = page.locator('.product-page-price p').get_by_text(re.compile(r"за .+")).first.text_content(timeout=PAGE_INTERACT_TIMEOUT_MS).replace('за ', '')
        if unit:
            logger.info('Извлечена единица измерения товара (способ_1): %s [%s]', unit, page.url)
            return unit
    except Exception as e:
        error = e

    try:
        unit = page.locator('.quantity-in-units p').last.text_content(timeout=PAGE_INTERACT_TIMEOUT_MS)
        if unit:
            logger.info('Извлечена единица измерения товара (способ_2): %s [%s]', unit, page.url)
            return unit
    except Exception as e:
        error = e

    logger.error('Ошибка извлечения единицы измерения товара. [%s] %s', page.url, error)

    return None


def extract_product_qty(page: Page) -> int or None:
    try:
        if qty_dirty := page.locator('.available-product-remains').first.text_content():
            if m := re.search(r'(\d+(?:\s*\d+)*)(?=(?:\s+[а-я]{1,})?$)', qty_dirty, re.I):
                if qty := re.sub(r'\s', '', m.group(1)):
                    logger.info('Извлечено количество доступного товара: %s из строки "%s" [%s]', qty, qty_dirty, page.url)
                    return qty
    except Exception as e:
        logger.error('Ошибка извлечения количества доступного товара. [%s] [%s]', page.url, e)

    return None


def extract_product_description(page: Page) -> str or None:
    try:
        description_read_more = page.locator('.product-page-description').first.get_by_text('Показать полностью...').first
        description_read_more.click(timeout=PAGE_INTERACT_TIMEOUT_MS)
        sleep(0.3)
        logger.debug('Раскрыто описание товара. [%s]', page.url)
    except Exception:
        logger.debug('Описание не раскрыто. [%s]', page.url)

    try:
        description = page.locator('.product-page-description-content').first.text_content()

        if description:
            logger.info('Извлечено описание товара. [%s] %s', page.url, description)
            return description
    except Exception as e:
        logger.error('Ошибка извлечения описания товара. [%s] %s', page.url, e)

    return None


def extract_product_properties(page: Page) -> list[ProductProperty]:
    properties: list[ProductProperty] = []
    try:
        for item in page.locator('.product-properties-columns .properties-item').all():
            label = item.locator('.properties-item-title-content').first.text_content()
            value = item.locator('.properties-item-value').first.text_content()
            if label and value:
                properties.append(ProductProperty(label=label, value=value))

        logger.info('Извлечено %s характеристик товара [%s]', len(properties), page.url)
    except Exception as e:
        logger.error('Ошибка извлечения характеристик товара. [%s] %s', page.url, e)

    return properties


def extract_product_comments(page: Page) -> list[str]:
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
    except Exception:
        logger.debug('Следующая страница отзывов не найдена. [%s]', page.url)

    try:
        for comment in page.locator('.product-feedback-block [itemprop="description"]').all():
            comments.append(comment.text_content())
    except Exception:
        logger.debug('Нет отзывов. [%s]', page.url)

    if comments:
        logger.info('Извлечено %s отзывов о товаре. [%s] ', len(comments), page.url)

    return comments


def extract_product_questions(page: Page) -> list[ProductQuestion]:
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
    except Exception:
        logger.debug('Следующая страница вопросов о товаре не найдена. [%s]', page.url)

    try:
        for q in page.locator('.question-list ul li').all():
            questions.append(ProductQuestion(
                question=q.locator('.npp-feedback-comment>p').first.text_content(),
                answer=q.locator('.npp-review-response-list .npp-feedback-comment>p').first.text_content(),
            ))
    except Exception:
        logger.debug('Нет вопросов о товаре. [%s]', page.url)

    if questions:
        logger.info('Извлечено %s вопросов о товаре. [%s]', len(questions), page.url)

    return questions