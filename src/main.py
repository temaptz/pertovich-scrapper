from crawler import process_main_catalog
from time import sleep
from camoufox.sync_api import Camoufox
from pathlib import Path

from src.browser import prepare_browser_cookies

with Camoufox(
        os='windows',
        window=(1280, 800),
        humanize=True,
        headless=False,
        persistent_context=True,
        user_data_dir=f'{Path(__file__).resolve().parent.parent}/camoufox_profile',
        locale='ru-RU',
) as camoufox_browser:
    prepare_browser_cookies(camoufox_browser)
    process_main_catalog(camoufox_browser)

    sleep(10)
