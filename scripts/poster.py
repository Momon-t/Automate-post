import csv
from datetime import datetime
from playwright.sync_api import sync_playwright
import os

from pathlib import Path
csv_path = Path("data") / "posts.csv"
now = datetime.now().replace(second=0, microsecond=0)

def find_matching_post():
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            post_time = datetime.strptime(row["datetime"], "%Y-%m-%d %H:%M")
            if post_time == now:
                return row["text"]
    return None

def post_to_x(text):
    email = os.environ["X_EMAIL"]
    password = os.environ["X_PASSWORD"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://twitter.com/login")
        page.fill("input[name='text']", email)
        page.click("div[role='button'][data-testid='LoginForm_Login_Button']")
        page.wait_for_timeout(2000)

        page.fill("input[name='password']", password)
        page.click("div[role='button'][data-testid='LoginForm_Login_Button']")
        page.wait_for_timeout(3000)

        page.goto("https://twitter.com/compose/tweet")
        page.fill("div[aria-label='ツイートテキストを入力']", text)
        page.click("div[data-testid='tweetButton']")
        page.wait_for_timeout(3000)

        browser.close()

if __name__ == "__main__":
    text = find_matching_post()
    if text:
        post_to_x(text)
