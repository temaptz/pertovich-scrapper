import os
from pathlib import Path
from time import sleep

from dotenv import load_dotenv
load_dotenv()

from camoufox.sync_api import Camoufox

from src.browser import prepare_browser_cookies
from src.logger import setup_logging
from crawler import process_main_catalog

setup_logging()

headless = os.environ.get('HEADLESS', 'false').lower() == 'true'

with Camoufox(
        os='windows',
        window=(1280, 800),
        humanize=True,
        headless=headless,
        persistent_context=True,
        user_data_dir=f'{Path(__file__).resolve().parent.parent}/camoufox_profile',
        locale='ru-RU',
) as camoufox_browser:
    prepare_browser_cookies(camoufox_browser)
    process_main_catalog(camoufox_browser)

    sleep(10)
