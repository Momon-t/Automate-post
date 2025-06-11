import csv
import os
from datetime import datetime
from pathlib import Path
import pytz
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from dotenv import load_dotenv

# .env ファイルから環境変数を読み込む（ローカル用）
load_dotenv()

# 投稿予定CSVファイルのパス
csv_path = Path("data/posts.csv")

# 現在時刻（日本時間、秒切り捨て）
now = datetime.now(pytz.timezone("Asia/Tokyo")).replace(second=0, microsecond=0)

def find_matching_post():
    now = datetime.now(pytz.timezone("Asia/Tokyo"))
    tolerance_minutes = 5  # 許容誤差5分

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 秒まで一致させる形式に変更
            post_time = datetime.strptime(row["datetime"], "%Y-%m-%d %H:%M:%S")
            post_time = pytz.timezone("Asia/Tokyo").localize(post_time)

            delta = abs((post_time - now).total_seconds() / 60)
            if delta <= tolerance_minutes:
                print(f"[INFO] 投稿対象一致: {row['datetime']} -> {row['text']}")
                return row["text"]

    return None

def post_to_x(text):
    # 認証情報を環境変数から取得（GitHub Secrets または .env）
    auth_token = os.getenv("AUTH_TOKEN")
    if not auth_token:
        print("[FATAL] AUTH_TOKEN が未設定です")
        return

    print("[INFO] トークンによる投稿開始")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            locale='en-US',
            storage_state=None,  # 認証情報は手動ログイン方式なら cookie 読み込みに切り替える
        )
        page = context.new_page()

        try:
            # Twitterの投稿ページへ直接遷移（ログイン不要な場合）
            page.goto("https://twitter.com/compose/tweet", timeout=20000)
            page.add_init_script(f"""
                document.cookie = "auth_token={auth_token}; path=/; domain=.twitter.com; Secure";
            """)
            page.reload()

            print("[STEP] ツイート入力欄を待機中...")
            page.wait_for_selector("div[aria-label='Tweet text']", timeout=15000)

            print(f"[STEP] 投稿内容入力: {text}")
            page.fill("div[aria-label='Tweet text']", text)
            page.click("div[data-testid='tweetButton']")
            page.wait_for_timeout(3000)

            print("[SUCCESS] 投稿完了")

        except Exception as e:
            print(f"[FATAL] エラー発生: {e}")
            page.screenshot(path="error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    text = find_matching_post()
    if text:
        post_to_x(text)
    else:
        print("[INFO] 今回投稿する内容はありませんでした。")
