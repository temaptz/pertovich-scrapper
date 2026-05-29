from time import sleep
from playwright.sync_api import BrowserContext, Locator

from src.utils import silent_errors

DEFAULT_TIMEOUT_MS = 10_000

def prepare_browser_cookies(browser: BrowserContext) -> None:
    page = browser.pages[0]
    silent_errors(page)
    page.goto('https://google.ru', timeout=DEFAULT_TIMEOUT_MS)


    page.wait_for_load_state('networkidle', timeout=DEFAULT_TIMEOUT_MS)
    print('Google page loaded')

    try:
        accept_button = page.get_by_role(role='button', name='Принять все').or_(
            page.get_by_role(role='button', name='Accept all')
        )
        accept_button.click(timeout=DEFAULT_TIMEOUT_MS)
        page.wait_for_load_state('networkidle', timeout=DEFAULT_TIMEOUT_MS)
        print('Google cookies accepted')
    except Exception as e:
        print('Error (or not if elem not exists) accept cookies')
        print(e)

    first_search_result: Locator | None = None

    try:
        search_input = (
            page
            .locator('textarea[autofocus], input[autofocus]')
            .filter(visible=True)
            .first
        )

        print('Search input found')

        search_input.click()
        sleep(0.3)
        search_input.fill(value='петрович петрозаводск', force=True)
        sleep(0.3)
        search_input.press('Enter')
        page.wait_for_load_state('domcontentloaded', timeout=DEFAULT_TIMEOUT_MS)
        sleep(0.3)
        first_search_result = (
            page
            .locator('#search a')
            .filter(visible=True)
            .first
        )

    except Exception as e:
        print('Error search')
        print(e)

    try:
        first_search_result.click(timeout=DEFAULT_TIMEOUT_MS)
        page.wait_for_load_state(
            state='domcontentloaded',
            timeout=DEFAULT_TIMEOUT_MS,
        )
        sleep(0.3)

        print('First search result loaded')
    except Exception as e:
        print('Error open first search result')
        print(e)