from time import sleep

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
from synology_dsm import SynologyDSM

from config import settings


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
    driver = get_driver()
    links = []

    driver.get(url)

    while True:
        WebDriverWait(driver, timeout=10).until(lambda d: d.find_element(By.CSS_SELECTOR, "#list_videos_common_videos_list_items a[href]"))
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


def syno_wait(syno: SynologyDSM):
    while True:
        sleep(settings.syno_wait_timeout)

        syno.download_station.update()

        tasks = syno.download_station.get_all_tasks()
        tasks_enabled = 0

        for task in tasks:
            if task.status in ('downloading', 'waiting'):
                tasks_enabled += 1

        if tasks_enabled < settings.syno_tasks:
            break


def main():
    syno = SynologyDSM(
        settings.syno_url, settings.syno_port,
        settings.syno_user, settings.syno_password
    )

    url = settings.watch_model_url
    links = get_links(url)

    for link in links:
        syno_wait(syno)

        url = get_video_link(link)

        print(f"[+] Downloading link {url}")
        syno.download_station.create(url)


if __name__ == '__main__':
    main()
