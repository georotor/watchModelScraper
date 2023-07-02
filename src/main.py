import os

import requests

from urllib.parse import urlparse
from urllib3.util.retry import Retry
from time import sleep

from config import settings
from requests.adapters import HTTPAdapter
from requests.sessions import Session
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm


def get_driver(debug: bool = False) -> WebDriver:
    if debug:
        driver = webdriver.Firefox()
        driver.install_addon("ublock_origin-1.50.0.xpi")
        return driver

    firefox_options = webdriver.FirefoxOptions()

    driver = webdriver.Remote(
        command_executor=settings.firefox_remote,
        options=firefox_options,

    )
    driver.set_window_size(1280, 1024)
    webdriver.Firefox.install_addon(driver, "ublock_origin-1.50.0.xpi")

    return driver


def get_video_link(driver: WebDriver, url: str) -> str:
    driver.get(url)
    el = WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.CSS_SELECTOR, "video.fp-engine[src]"))
    link = el.get_attribute("src")

    return link


def get_links(driver: WebDriver, url: str) -> list:
    links = []

    driver.get(url)

    while True:
        WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.CSS_SELECTOR, "#list_videos_common_videos_list_items a[href]"))
        elements = driver.find_elements(By.CSS_SELECTOR, "#list_videos_common_videos_list_items a[href]")
        for item in elements:
            link = item.get_attribute("href")
            print(f"[>] Find link \"{link}\"")
            links.append(link)

        try:
            driver.find_element(By.CSS_SELECTOR, "div.pagination-holder li.next a[href]").click()
            sleep(3)
            continue
        except NoSuchElementException:
            break

    return links


def create_session() -> Session:
    session = requests.Session()

    retry = Retry(connect=7, backoff_factor=0.5, raise_on_redirect=False, raise_on_status=False)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    session.headers.update({
        'User-Agent': 'Googlebot/2.1 (+http://www.google.com/bot.html)',
        'Referer': 'https://watchmdh.to/'
    })

    return session


def get_url_data(url) -> dict:
    parsed_url = urlparse(url)
    return {'file_name': os.path.basename(parsed_url.path.rstrip('/')), 'extension': os.path.splitext(parsed_url.path)[1],
            'hostname': parsed_url.hostname}


def download(url, download_path):
    session = create_session()

    file_name = get_url_data(url)['file_name']
    final_path = os.path.join(download_path, file_name)

    if os.path.isfile(final_path):
        print(f"\t[-] Error Downloading \"{file_name}\" exists")
        return

    try:
        with session.get(url, stream=True) as r:
            if r.status_code != 200:
                print(f"\t[-] Error Downloading \"{file_name}\": {r.status_code}")
                return

            file_size = int(r.headers.get('content-length', -1))
            with open(final_path, 'wb') as f:
                with tqdm(total=file_size, unit='iB', unit_scale=True, desc=file_name, leave=False) as pbar:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk is not None:
                            f.write(chunk)
                            pbar.update(len(chunk))

    except requests.exceptions.ConnectionError:
        print(f"\t[-] Unable download link {url}")


def main():
    driver = get_driver()

    url = settings.watch_model_url
    links = get_links(driver, url)

    for link in links:
        if driver is None:
            driver = get_driver()

        url = get_video_link(driver, link)
        driver.quit()
        driver = None

        print(f"[+] Downloading link {url}")
        download(url, settings.downloads_dir)


if __name__ == '__main__':
    main()
