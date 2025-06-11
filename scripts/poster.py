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
            # 修正点："%Y-%m-%d %H:%M:%S" に対応
            post_time = datetime.strptime(row["datetime"], "%Y-%m-%d %H:%M:%S")
            post_time = pytz.timezone("Asia/Tokyo").localize(post_time)

            delta = abs((post_time - now).total_seconds() / 60)
            if delta <= tolerance_minutes:
                print(f"[INFO] 投稿対象一致: {row['datetime']} -> {row['text']}")
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

        #――――――――――――――――――――――――――――――――――――――#
        # ① メールアドレス入力フェーズ
        #――――――――――――――――――――――――――――――――――――――#
        print("[STEP] メールアドレス入力")
        page.fill("input[name='text']", email)

        # 🔴 ここから追加 -----------
        login_btn = page.locator("div[role='button'][data-testid='LoginForm_Login_Button']")
        login_btn.wait_for(state="visible", timeout=10000)  # 最大10秒待つ
        login_btn.click()
        # 🔴 追加ここまで ----------

        #――――――――――――――――――――――――――――――――――――――#
        # ② パスワード入力フェーズ
        #――――――――――――――――――――――――――――――――――――――#
        print("[STEP] パスワード入力")
        page.fill("input[name='password']", password)

        # 🔴 ここから追加 -----------
        pw_login_btn = page.locator("div[role='button'][data-testid='LoginForm_Login_Button']")
        pw_login_btn.wait_for(state="visible", timeout=10000)
        pw_login_btn.click()
        # 🔴 追加ここまで ----------

        print("[STEP] ツイートページへ遷移")
        page.wait_for_timeout(3000)  # 認証完了待ち
        page.goto("https://twitter.com/compose/tweet")

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
