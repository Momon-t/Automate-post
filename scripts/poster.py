import csv
from datetime import datetime
from pathlib import Path
import pytz
from playwright.sync_api import sync_playwright, TimeoutError

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
            post_time = datetime.strptime(row["datetime"], "%Y-%m-%d %H:%M:%S")
            post_time = pytz.timezone("Asia/Tokyo").localize(post_time)
            delta = abs((post_time - now).total_seconds() / 60)
            if delta <= tolerance_minutes:
                print(f"[INFO] 投稿対象一致: {row['datetime']} -> {row['text']}")
                return row["text"]

    return None

def post_to_x(text):
    print("[INFO] ログイン済みセッションで投稿を開始します")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="auth.json")  # ← ここでログイン状態を読み込む
        page = context.new_page()

        try:
            print("[STEP] ツイートページへアクセス")
            page.goto("https://twitter.com/compose/tweet", timeout=20000)

            print("[STEP] ツイート入力欄を待機中...")
            page.wait_for_selector("div[aria-label='Tweet text']", timeout=15000)

            print(f"[STEP] 投稿内容入力: {text}")
            page.fill("div[aria-label='Tweet text']", text)
            page.click("div[data-testid='tweetButton']")
            page.wait_for_timeout(3000)

            print("[SUCCESS] 投稿完了")

        except TimeoutError:
            print("[FATAL] ツイート入力欄が見つかりません（Cookieが切れた可能性）")
            page.screenshot(path="error.png")
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
