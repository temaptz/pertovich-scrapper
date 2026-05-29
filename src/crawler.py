import random
from time import sleep
from playwright.sync_api import BrowserContext, Page

from src.utils import page_load_and_scroll, retry

DOMAIN = ''
DEFAULT_TIMEOUT_MS = 10_000

# Работа с главной страницей каталога
def process_main_catalog(browser: BrowserContext) -> None:
    main_catalog_page = browser.pages[0]
    page_load_and_scroll(page=main_catalog_page, url=f'{DOMAIN}/catalog/', timeout_ms=DEFAULT_TIMEOUT_MS)
    links = main_catalog_page.locator('.section-catalog-list-item-link').all()

    for link in links:
        url = f'{DOMAIN}{link.get_attribute('href')}'
        process_catalog_page_recursive(browser=browser, url=url)
        sleep(random.random() * 5)

    sleep(10)


# Работа со страницей каталога: список товаров + подкаталоги
def process_catalog_page_recursive(browser: BrowserContext, url: str) -> None:
    page = browser.new_page()
    page_load_and_scroll(page=page, url=url, timeout_ms=DEFAULT_TIMEOUT_MS)

    # Название категории
    category_name = page.locator('h1').first.text_content()
    print(f'START CATEGORY: {category_name}')

    # Обход товаров
    process_products_pagination(browser=browser, page=page)

    # Рекурсивный обход подкаталогов
    sub_catalog_links = page.locator('a.catalog-subsection-img').all()
    for link in sub_catalog_links:
        process_catalog_page_recursive(browser=browser, url=f'{DOMAIN}{link.get_attribute('href')}')

    page.close()


# Обход пагинации товаров
def process_products_pagination(browser: BrowserContext, page: Page) -> None:
    is_pagination_available = True
    processed_urls = set()

    while is_pagination_available:
        # Получение товаров
        product_links = page.locator('[data-test="product-link"]').all()
        print('Links in pagination', len(product_links))

        for i in product_links:
            url = f'{DOMAIN}{i.get_attribute('href')}'
            if url not in processed_urls:
                process_product_page(browser=browser, url=url)
                processed_urls.add(url)
                sleep(random.random() * 5)

        # Переход по пагинации дальше
        try:
            next_button = page.locator('button[data-test="products-next-button"]').first
            next_button.scroll_into_view_if_needed()
            next_button.click()
            sleep(10) # Ожидание загрузки новых элементов пагинации
        except Exception as e:
            print('No next button')
            is_pagination_available = False


# Работа со страницей товара
@retry()
def process_product_page(browser: BrowserContext, url: str) -> None:
    page = browser.new_page()
    page_load_and_scroll(page=page, url=url, timeout_ms=DEFAULT_TIMEOUT_MS)

    # Название товара
    product_name = page.locator('h1').first.text_content()
    print(f'START PRODUCT: {product_name}')

    page.close()
