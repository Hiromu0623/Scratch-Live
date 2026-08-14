import os
import time
import threading
import warnings
import scratchattach as scratch3
from dotenv import load_dotenv
from flask import Flask

# 警告メッセージを非表示
warnings.filterwarnings('ignore', category=scratch3.LoginDataWarning)

# .env ファイルを読み込む
load_dotenv()

SESSION_ID = os.getenv("SCRATCH_SESSION_ID")
USERNAME = os.getenv("SCRATCH_USERNAME")
PROJECT_ID = os.getenv("SCRATCH_PROJECT_ID")

# --- Renderのスリープ防止用Webサーバー ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Scratch Worker is Running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- Scratch監視メイン処理（テスト版） ---
def scratch_loop():
    if not SESSION_ID or not USERNAME or not PROJECT_ID:
        print("【エラー】環境変数の設定が不足しています。")
        return

    print("Scratchにログイン中...")
    try:
        session = scratch3.login_by_id(SESSION_ID, username=USERNAME)
        conn = session.connect_cloud(project_id=PROJECT_ID)
        print("ログイン成功！送信テストループを開始します。\n" + "-" * 40)
    except Exception as e:
        print(f"【エラー】初期ログインに失敗しました: {e}")
        return

    tick_count = 0

    while True:
        try:
            tick_count += 1
            print(f"送信テスト中... ({tick_count}回目)")
            conn.set_var("cloud_check", tick_count)
            print(f"-> 送信完了コマンドを実行しました (値: {tick_count})")
        except Exception as e:
            print(f"【送信エラー発生】: {e}")

        time.sleep(10)

# --- メイン実行 ---
if __name__ == "__main__":
    threading.Thread(target=scratch_loop, daemon=True).start()
    run_flask()
