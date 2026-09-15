"""
note.comに一度だけヘッドあり(headed)ブラウザでログインし、
セッションをstate.jsonに保存する。以降はschedule_post.pyがこれを再利用する。

2段階認証や確認コードが出た場合は、開いたブラウザ上で手動対応してから
ターミナルでEnterを押す。

使い方:
    python login_and_save_session.py
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
STATE_PATH = HERE / "state.json"


def main() -> None:
    load_dotenv(HERE / ".env")
    email = os.environ.get("NOTE_EMAIL")
    password = os.environ.get("NOTE_PASSWORD")
    if not email or not password:
        raise SystemExit(
            "NOTE_EMAIL / NOTE_PASSWORD が未設定です。"
            f"{HERE / '.env'} を作成するか環境変数で指定してください。"
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://note.com/login")

        page.get_by_placeholder("メールアドレス").fill(email)
        page.get_by_placeholder("パスワード").fill(password)
        page.get_by_role("button", name="ログイン").click()

        print(
            "ブラウザでログイン状態を確認してください"
            "（確認コード・2段階認証が出た場合は手動で完了させてください）。"
        )
        input("ログインが完了したらEnterを押してください... ")

        browser.contexts[0].storage_state(path=str(STATE_PATH))
        browser.close()

    print(f"セッションを保存しました: {STATE_PATH}")


if __name__ == "__main__":
    main()
