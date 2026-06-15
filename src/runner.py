import os
import traceback
from pathlib import Path
from time import sleep

from dotenv import load_dotenv
load_dotenv()

from camoufox.sync_api import Camoufox

from src.browser import prepare_browser_cookies, silent_errors_context
from src.logger import setup_logging, get_logger
from crawler import process_main_catalog
from src.catalog import catalog_write

setup_logging()

logger = get_logger(__name__)

headless = os.environ.get('HEADLESS', 'false').lower() == 'true'


def run_with_recovery(max_restarts: int = 10) -> None:
    for attempt in range(1, max_restarts + 1):
        try:
            with Camoufox(
                    os='windows',
                    window=(1280, 800),
                    humanize=True,
                    headless=headless,
                    persistent_context=True,
                    user_data_dir=f'{Path(__file__).resolve().parent.parent}/camoufox_profile',
                    locale='ru-RU',
            ) as camoufox_browser:
                silent_errors_context(camoufox_browser)
                prepare_browser_cookies(camoufox_browser)
                process_main_catalog(camoufox_browser)
                catalog_write()

            return
        except Exception as e:
            logger.error(
                'Крах браузера. Попытка %d/%d. %s\n%s',
                attempt, max_restarts, e, traceback.format_exc(),
            )

            if attempt < max_restarts:
                logger.info('Ожидание 10 сек перед перезапуском браузера...')
                sleep(10)

    logger.critical('Исчерпаны все попытки перезапуска браузера (%d)', max_restarts)
    raise RuntimeError(f'Исчерпаны все попытки перезапуска браузера ({max_restarts})')
