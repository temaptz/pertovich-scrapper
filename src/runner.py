import os
import threading
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

headless = os.environ.get('HEADLESS')


def _start_driver_watchdog(cm: Camoufox, stop_event: threading.Event, check_interval: float = 10.0) -> None:
    def _watch():
        while not stop_event.wait(check_interval):
            try:
                proc = cm._connection._transport._proc
                if proc.returncode is not None:
                    logger.critical(
                        'Node.js-драйвер Playwright мёртв (returncode=%s). '
                        'Принудительный выход для рестарта контейнера.',
                        proc.returncode,
                    )
                    os._exit(1)
            except AttributeError:
                logger.warning('Не удалось получить статус процесса драйвера (структура Playwright изменилась?).')

    thread = threading.Thread(target=_watch, name='driver-watchdog', daemon=True)
    thread.start()


def run_with_recovery(max_restarts: int = 10) -> None:
    for attempt in range(1, max_restarts + 1):
        try:
            logger.info('Запуск браузера. Headless: %s', headless)

            cm = Camoufox(
                    os='windows',
                    window=(1280, 800),
                    humanize=True,
                    headless=headless,
                    persistent_context=True,
                    user_data_dir=f'{Path(__file__).resolve().parent.parent}/temp/camoufox_profile',
                    locale='ru-RU',
            )
            with cm as camoufox_browser:
                stop_event = threading.Event()
                _start_driver_watchdog(cm, stop_event)
                try:
                    silent_errors_context(camoufox_browser)
                    prepare_browser_cookies(camoufox_browser)
                    process_main_catalog(camoufox_browser)
                    catalog_write()
                finally:
                    stop_event.set()

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
