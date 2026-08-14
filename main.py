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

INTERVAL = 15  # 基本の更新間隔（秒）

# --- Renderのスリープ防止用Webサーバー ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Scratch Worker is Running!"

def run_flask():
    # Renderから割り当てられるポート番号を取得して起動
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- Scratch監視メイン処理 ---
def scratch_loop():
    if not SESSION_ID or not USERNAME or not PROJECT_ID:
        print("【エラー】環境変数の設定が不足しています。")
        return

    print("Scratchにログイン中...")
    try:
        session = scratch3.login_by_id(SESSION_ID, username=USERNAME)
        conn = session.connect_cloud(project_id=PROJECT_ID)
        user = session.get_linked_user()

        print("ログイン成功！クラウド変数の定期更新を開始します。\n" + "-" * 40)

    except Exception as e:
        print(f"【エラー】初期ログインに失敗しました: {e}")
        return

    tick_count = 0
    last_followers = -1
    last_messages = -1

   while True:
        try:
            tick_count += 1
            print(f"送信テスト中... ({tick_count}回目)")
            conn.set_var("cloud_check", tick_count)
            print(f"-> 送信成功！ cloud_check = {tick_count}")
        except Exception as e:
            print(f"【エラー発生】: {e}")

        time.sleep(10)

        except Exception as e:
            print(f"【エラー】通信失敗 (再接続を試みます): {e}")
            time.sleep(5)
            try:
                conn = session.connect_cloud(project_id=PROJECT_ID)
                print("-> クラウドへ再接続しました。")
            except Exception as re_err:
                print(f"-> 再接続失敗: {re_err}")

        elapsed_time = time.time() - start_time
        target_sleep = INTERVAL - elapsed_time
        actual_sleep = max(10, target_sleep)
        time.sleep(actual_sleep)

# --- メイン実行 ---
if __name__ == "__main__":
    # 1. 関数が定義された「後」でスレッドを起動
    threading.Thread(target=scratch_loop, daemon=True).start()
    # 2. Flaskを起動してポートを開放
    run_flask()
