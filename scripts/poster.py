import csv
import os
from datetime import datetime
from pathlib import Path

import pytz
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from dotenv import load_dotenv

# -----------------------------
# ★ 1. ローカル実行では .env を読む
#    GitHub Actions では Secrets が優先される
# -----------------------------
load_dotenv()  # .env があれば読み込む

# 投稿予定 CSV ファイル
csv_path = Path("data/posts.csv")

def find_matching_post():
    """CSV から「今」±5分に一致する投稿文を返す"""
    now = datetime.now(pytz.timezone("Asia/Tokyo"))
    tolerance_minutes = 5

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            post_time = datetime.strptime(
                row["datetime"], "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=pytz.timezone("Asia/Tokyo"))

            delta = abs((post_time - now).total_seconds() / 60)
            if delta <= tolerance_minutes:
                print(f"[INFO] 投稿対象一致: {row['datetime']} -> {row['text']}")
                return row["text"]
    return None

def post_to_x(text: str):
    """auth_token Cookie を使って X へツイートする"""
    # -----------------------------
    # ★ 2. AUTH_TOKEN を Secrets / .env から取得
    # -----------------------------
    auth_token = os.getenv("AUTH_TOKEN")
    if not auth_token:
        print("[FATAL] AUTH_TOKEN が未設定です")
        return

    print("[INFO] auth_token による投稿開始")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(locale="en-US")

        # -----------------------------
        # ★ 3. Cookie として auth_token を追加
        # -----------------------------
        context.add_cookies([{
            "name": "auth_token",
            "value": auth_token,
            "domain": ".twitter.com",
            "path": "/",
            "httpOnly": True,
            "secure": True,
            "sameSite": "Lax"
        }])

        page = context.new_page()

        try:
            print("[STEP] ツイートページへアクセス")
            page.goto("https://twitter.com/compose/tweet", timeout=30000)

            # ツイート入力欄が現れるまで待機
            page.wait_for_selector("div[aria-label='Tweet text']", timeout=15000)

            print(f"[STEP] 投稿内容入力: {text}")
            page.fill("div[aria-label='Tweet text']", text)

            page.click("div[data-testid='tweetButton']")
            page.wait_for_timeout(3000)

            print("[SUCCESS] 投稿完了")

        except PWTimeout:
            print("[ERROR] ツイート入力欄が見つかりません（Cookie 失効の可能性）")
            page.screenshot(path="tweet_error.png")
        except Exception as e:
            print(f"[FATAL] 予期せぬエラー: {e}")
            page.screenshot(path="fatal_error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    text = find_matching_post()
    if text:
        post_to_x(text)
    else:
        print("[INFO] 今回投稿する内容はありませんでした。")
