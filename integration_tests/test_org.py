import os
import time

import pytest
import selenium.webdriver.chrome.options
import selenium.webdriver.firefox.options
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import config

BROWSER = os.environ.get("BROWSER", "ChromeHeadless")


@pytest.fixture(scope="module")
def browser(request):
    if BROWSER == "ChromeHeadless":
        browser = "Chrome"
        options = selenium.webdriver.chrome.options.Options()
        options.add_argument("--headless")
        # uncomment this if "DevToolsActivePort" error
        # options.add_argument("--remote-debugging-port=9222")
    elif BROWSER == "FirefoxHeadless":
        browser = "Firefox"
        options = selenium.webdriver.firefox.options.Options()
        options.add_argument("-headless")
    else:
        browser = BROWSER
        options = None
    browser = getattr(webdriver, browser)(options=options)
    browser.implicitly_wait(3)
    request.addfinalizer(lambda: browser.quit())
    return browser


def test_atest(browser):
    browser.get("http://localhost:5000/")
    organisations_link = browser.find_element(By.LINK_TEXT, "Organisations »")
    organisations_link.click()

    organisations_table = browser.find_element(By.ID, "organisations")
    organisation_links = organisations_table.find_elements(By.TAG_NAME, "a")
    # This should work with 0 instead of -1, but currently doesn't
    organisation_links[-1].click()

    browser.find_element(By.ID, "username").send_keys(config.APP_ADMIN_USERNAME)
    browser.find_element(By.ID, "password").send_keys(config.APP_ADMIN_PASSWORD)
    browser.find_element(By.ID, "password").send_keys(Keys.ENTER)
    time.sleep(1)

    browser.find_element(By.ID, "showindicator-16").find_element(
        By.TAG_NAME, "i"
    ).click()

    browser.find_element(By.LINK_TEXT, "Title is present").click()
    time.sleep(1)

    assert (
        "`title/narrative/text()` should be present"
        in browser.find_element(By.TAG_NAME, "body").text
    )
