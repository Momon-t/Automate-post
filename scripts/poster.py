import csv
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
import os

# CSVのパス（GitHub Actionsルートから見て）
csv_path = Path("data/posts.csv")
import pytz
now = datetime.now(pytz.timezone("Asia/Tokyo")).replace(second=0, microsecond=0)


def find_matching_post():
    now = datetime.now(pytz.timezone("Asia/Tokyo"))
    tolerance_minutes = 5  # ←許容範囲を5分に設定

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = datetime.strptime(row["datetime"], "%Y-%m-%d %H:%M:%S")
            dt = pytz.timezone("Asia/Tokyo").localize(dt)

            delta = abs((dt - now).total_seconds() / 60)
            if delta <= tolerance_minutes:
                return row["text"]

    return None

def post_to_x(text):
    email = os.environ["X_EMAIL"]
    password = os.environ["X_PASSWORD"]

    print(f"[INFO] ログイン開始: {email}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print("[STEP] ページ遷移: ログイン画面へ")
        page.goto("https://twitter.com/login")
        page.wait_for_timeout(2000)

        print("[STEP] メールアドレス入力")
        page.fill("input[name='text']", email)
        page.click("div[role='button'][data-testid='LoginForm_Login_Button']")
        page.wait_for_timeout(2000)

        print("[STEP] パスワード入力")
        page.fill("input[name='password']", password)
        page.click("div[role='button'][data-testid='LoginForm_Login_Button']")
        page.wait_for_timeout(3000)

        print("[STEP] ツイートページへ遷移")
        page.goto("https://twitter.com/compose/tweet")
        page.wait_for_timeout(2000)

        print(f"[STEP] 投稿内容入力: {text}")
        page.fill("div[aria-label='ツイートテキストを入力']", text)
        page.click("div[data-testid='tweetButton']")
        page.wait_for_timeout(3000)

        print("[SUCCESS] 投稿完了")
        browser.close()

if __name__ == "__main__":
    text = find_matching_post()
    if text:
        post_to_x(text)
    else:
        print("[INFO] 今回投稿する内容はありませんでした。")
