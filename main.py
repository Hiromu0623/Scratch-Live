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
        
        conn = session.connect_cloud(project_id=PROJECT_ID)
        conn.connect()
        
        print("✅ クラウド接続成功！24時間送信ループを開始します。\n" + "-" * 40)
    except Exception as e:
        print(f"【初期化エラー】: {e}")
        return

    tick_count = 0

    while True:
        try:
            # 最新のユーザー情報を取得
            user.update()
            follower_count = user.follower_count()
            message_count = user.message_count()
            
            tick_count = (tick_count + 1) % 1000

            # 3つの変数を順番に送信（0.2秒あけて連投エラー防止）
            conn.set_var("followers", follower_count)
            time.sleep(0.2)
            conn.set_var("messages", message_count)
            time.sleep(0.2)
            conn.set_var("cloud_check", tick_count)

            current_time = time.strftime('%H:%M:%S')
            print(f"[{current_time}] 恒常送信成功 | フォロワー: {follower_count} | メッセージ: {message_count} | check: {tick_count}")

        except Exception as e:
            print(f"【送信エラー】: {e}")
            try:
                conn = session.connect_cloud(project_id=PROJECT_ID)
                conn.connect()
            except:
                pass

        # 15秒間隔で実行
        time.sleep(15)

if __name__ == "__main__":
    threading.Thread(target=scratch_loop, daemon=True).start()
    run_flask()
