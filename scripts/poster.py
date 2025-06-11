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


from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
import os
import pytz
from datetime import datetime

def post_to_x(text):
    email = os.environ["X_EMAIL"]
    password = os.environ["X_PASSWORD"]
    print(f"[INFO] ログイン開始: {email}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            # ログインページへ
            print("[STEP] ページ遷移: ログイン画面へ")
            page.goto("https://twitter.com/login", timeout=20000)
            page.wait_for_timeout(3000)

            # ユーザー名入力
            print("[STEP] ユーザー名入力")
            page.fill("input[name='text']", email)
            page.click("div[role='button']:has-text('次へ')")
            page.wait_for_timeout(2000)

            # パスワード入力
            print("[STEP] パスワード入力")
            page.fill("input[name='password']", password)
            page.click("div[role='button']:has-text('ログイン')")
            page.wait_for_timeout(3000)

            # ホーム画面到達確認（重要！）
            print("[STEP] ホーム遷移確認")
            page.wait_for_url("https://twitter.com/home", timeout=15000)

            # 投稿ページへ遷移
            print("[STEP] ツイートページへ")
            page.goto("https://twitter.com/compose/tweet", timeout=15000)

            try:
                page.wait_for_selector("div[aria-label='ツイートテキストを入力']", timeout=15000)
            except PWTimeout:
                print("[ERROR] ツイート入力欄が見つかりませんでした")
                page.screenshot(path="tweet_error.png")  # デバッグ用スクショ
                return

            print(f"[STEP] 投稿内容入力: {text}")
            page.fill("div[aria-label='ツイートテキストを入力']", text)
            page.click("div[data-testid='tweetButton']")
            page.wait_for_timeout(3000)

            print("[SUCCESS] 投稿完了")

        except Exception as e:
            print(f"[FATAL] 予期せぬエラー: {e}")
        finally:
            browser.close()


if __name__ == "__main__":
    text = find_matching_post()
    if text:
        post_to_x(text)
    else:
        print("[INFO] 今回投稿する内容はありませんでした。")
