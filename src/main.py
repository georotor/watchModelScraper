import os

import requests

from concurrent.futures import ThreadPoolExecutor
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


def get_driver() -> WebDriver:
    if settings.debug:
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


def get_video_link(url: str) -> str:
    driver = get_driver()
    driver.get(url)

    el = WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.CSS_SELECTOR, "video.fp-engine[src]"))
    link = el.get_attribute("src")

    driver.quit()

    return link


def get_links(url: str) -> list:
    links = []

    driver = get_driver()
    driver.get(url)

    while True:
        WebDriverWait(driver, timeout=10).until(
            lambda d: d.find_element(By.CSS_SELECTOR, "#list_videos_common_videos_list_items a[href]"))
        elements = driver.find_elements(By.CSS_SELECTOR, "#list_videos_common_videos_list_items a[href]")
        for item in elements:
            link = item.get_attribute("href")
            links.append(link)
            print(f"[{len(links)}] Find link \"{link}\"")

        try:
            driver.find_element(By.CSS_SELECTOR, "div.pagination-holder li.next a[href]").click()
            sleep(3)
            continue
        except NoSuchElementException:
            break

    driver.quit()

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
    return {'file_name': os.path.basename(parsed_url.path.rstrip('/')),
            'extension': os.path.splitext(parsed_url.path)[1],
            'hostname': parsed_url.hostname}


def download(url, download_path) -> str:
    file_name = get_url_data(url)['file_name']
    final_path = os.path.join(download_path, file_name)

    if os.path.isfile(final_path):
        return f"[-] Error Downloading \"{file_name}\" exists"

    session = create_session()

    try:
        with session.get(url, stream=True) as r:
            if r.status_code != 200:
                return f"[-] Error Downloading \"{file_name}\": {r.status_code}"

            with open(final_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk is not None:
                        f.write(chunk)

    except requests.exceptions.ConnectionError:
        return f"[-] Unable download link {url}"

    return f"[+] Downloaded {url}"


def task(link: str):
    url = get_video_link(link)
    res = download(url, settings.downloads_dir)
    print(res)


def main():
    url = settings.watch_model_url
    links = get_links(url)

    with ThreadPoolExecutor(max_workers=settings.downloads_threads) as executors:
        executors.map(task, links)


if __name__ == '__main__':
    main()
