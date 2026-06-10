import random
from time import sleep
from functools import wraps
from playwright.sync_api import Page

from src.logger import get_logger

logger = get_logger(__name__)


def retry(attempts=10, delay_ms=10000):
    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.error('Ошибка. Попытка %s/%s. %s', attempt, attempts, e)

                    if attempt < attempts:
                        logger.debug('Ожидание %s сек перед повторной попыткой...', delay_ms / 1000)
                        sleep(delay_ms / 1000)

            logger.critical('Исчерпаны все попытки повтора')
            raise Exception

        return wrapper

    return decorator


def silent_errors(page: Page) -> None:
    page.on('pageerror', lambda e: logger.warning('Ошибка страницы: %s', e))
    page.add_init_script('''
        window.addEventListener('error', function(e) { e.preventDefault(); });
        window.addEventListener('unhandledrejection', function(e) { e.preventDefault(); });
    ''')


# @retry()
def page_load_and_scroll(page: Page, url: str, timeout_ms: int) -> None:
    silent_errors(page=page)
    logger.debug('Загрузка страницы: %s', url)
    page.goto(url, timeout=timeout_ms)
    logger.debug('goto завершён. Текущий URL: %s, title: %s', page.url, page.title())
    page.wait_for_load_state('domcontentloaded', timeout=timeout_ms)
    logger.debug('domcontentloaded достигнут')
    sleep(3)
    _page_scroll_smooth(page=page)
    logger.debug('Скролл завершен')


def _page_scroll_smooth(page: Page) -> None:
    i = 0
    max_scroll_count = 50
    is_scroll_available = True
    total_mouse_wheel = 0

    page.mouse.move(random.randint(50, 100), random.randint(50, 100))

    while is_scroll_available and i <= max_scroll_count:
        viewport_height = page.viewport_size.get('height')
        mouse_wheel = random.randint(round(viewport_height / 1.5), viewport_height)
        total_mouse_wheel += mouse_wheel
        page.mouse.wheel(0, mouse_wheel)
        sleep(random.random())
        scroll_bottom = page.evaluate('document.documentElement.scrollHeight - (window.innerHeight + window.scrollY)')
        is_scroll_available = scroll_bottom > 0
        i += 1

    sleep(random.random())
    page.mouse.move(random.randint(50, 100), random.randint(50, 100))
    page.mouse.wheel(0, -total_mouse_wheel*1.5)
    page.evaluate('window.scrollTo({top: 0, behavior: "smooth"})')
    sleep(0.3)
