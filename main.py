import os
import time
import threading
import warnings
import scratchattach as scratch3
from dotenv import load_dotenv
from flask import Flask

# 警告メッセージを非表示
warnings.filterwarnings('ignore', category=scratch3.LoginDataWarning)

load_dotenv()

SESSION_ID = os.getenv("SCRATCH_SESSION_ID")
USERNAME = os.getenv("SCRATCH_USERNAME")
PROJECT_ID = os.getenv("SCRATCH_PROJECT_ID")

# --- Render用Webサーバー ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Scratch Worker is Running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- Scratch監視メイン処理 ---
def scratch_loop():
    if not SESSION_ID or not USERNAME or not PROJECT_ID:
        print("【エラー】環境変数の設定が不足しています。")
        return

    print("Scratchへログイン＆接続を開始します...")
    
    try:
        session = scratch3.login_by_id(SESSION_ID, username=USERNAME)
        user = session.get_linked_user()
        
        # 本家Scratchクラウド接続
        conn = session.connect_cloud(project_id=PROJECT_ID)
        
        print("✅ ログイン＆接続手続き完了！監視ループに入ります。\n" + "-" * 40)
    except Exception as e:
        print(f"【初期化エラー】: {e}")
        return

    last_followers = -1
    last_messages = -1
    tick_count = 0

    while True:
        try:
            # 1. アカウント情報の更新
            user.update()
            follower_count = user.follower_count()
            message_count = user.message_count()
            
            tick_count = (tick_count + 1) % 1000

            # 2. cloud_check の送信
            try:
                conn.set_var("cloud_check", tick_count)
            except Exception as ve:
                print(f"⚠️ cloud_check 送信スキップ/失敗: {ve}")

            # 3. フォロワー・メッセージ数変化の検知と送信
            if follower_count != last_followers or message_count != last_messages:
                print(f"[{time.strftime('%H:%M:%S')}] 🔔更新検出！ | フォロワー: {follower_count} | メッセージ: {message_count}")
                try:
                    conn.set_var("followers", follower_count)
                    conn.set_var("messages", message_count)
                except Exception as ve:
                    print(f"⚠️ ステータス変数 送信失敗: {ve}")

                last_followers = follower_count
                last_messages = message_count
            else:
                print(f"[{time.strftime('%H:%M:%S')}] 監視稼働中... (cloud_check={tick_count})")

        except Exception as e:
            print(f"【ループエラー】: {e}")

        # 15秒待機
        time.sleep(15)

if __name__ == "__main__":
    threading.Thread(target=scratch_loop, daemon=True).start()
    run_flask()
