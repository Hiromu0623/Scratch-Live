import os
import time
import threading  # ← これが抜けていたので追加！
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


def main():
    if not SESSION_ID or not USERNAME or not PROJECT_ID:
        print("【エラー】.env ファイルの設定が不足しています。")
        return

    print("Scratchにログイン中...")
    try:
        session = scratch3.login_by_id(SESSION_ID, username=USERNAME)
        conn = session.connect_cloud(project_id=PROJECT_ID)
        user = session.get_linked_user()

        print("ログイン成功！クラウド変数の定期更新を開始します。")
        print("※これ以降は、数値に変化があった時だけログが表示されます。\n" + "-" * 40)

    except Exception as e:
        print(f"【エラー】初期ログインに失敗しました: {e}")
        return

    tick_count = 0
    # 前回の数値を記憶するための変数
    last_followers = -1
    last_messages = -1

    while True:
        start_time = time.time()

        try:
            tick_count += 1

            # 生存確認（cloud_check）だけは裏で毎回送信する
            conn.set_var("cloud_check", tick_count)

            # 最新のデータを取得
            follower_count = user.follower_count()
            message_count = user.message_count()

            # 前回と数値が「違う」場合のみ、Scratchに送信してログを出す
            if follower_count != last_followers or message_count != last_messages:
                conn.set_var("followers", follower_count)
                conn.set_var("messages", message_count)

                current_time = time.strftime('%H:%M:%S')
                print(f"[{current_time}] 🔔数値が更新されました！ | フォロワー: {follower_count} | メッセージ: {message_count}")
                
                # 記憶している数値を最新のものに書き換える
                last_followers = follower_count
                last_messages = message_count

        except Exception as e:
            print(f"【エラー】通信失敗 (再接続を試みます): {e}")
            time.sleep(5)
            try:
                conn = session.connect_cloud(project_id=PROJECT_ID)
                print("-> クラウドへ再接続しました。")
            except Exception as re_err:
                print(f"-> 再接続失敗: {re_err}")

        # --- 連投防止ガード付きの待機処理 ---
        elapsed_time = time.time() - start_time
        target_sleep = INTERVAL - elapsed_time
        actual_sleep = max(10, target_sleep)
        time.sleep(actual_sleep)

if __name__ == "__main__":
    # 1. 先にScratch監視処理をバックグラウンド（裏側）で動かす
    threading.Thread(target=scratch_loop, daemon=True).start()
    # 2. メインでWebサーバー（Flask）を起動してポートを即座に開放する
    run_flask()
