from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os

load_dotenv()





with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.twitch.tv/")
    page.wait_for_timeout(10000)
    browser.close()



