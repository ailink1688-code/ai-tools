#!/usr/bin/env python3
"""note.com へ「おうえん」の記事を下書き保存する。

note/queue/*.md のうち、ファイル名順で最初の1本を下書きとして保存し、
note/posted/ へ移動する。公開ボタンは note 上で手動で押す運用。

注意: note には公式の投稿 API がなく、ここで使うのは Web 版が内部で使う
非公式エンドポイントです。仕様変更で動かなくなる可能性があります。

環境変数:
  NOTE_COOKIE  ブラウザの note.com ログイン済み Cookie 文字列（_note_session_v5 を含む）
"""
import argparse
import html
import os
import re
import shutil
import sys
import uuid
from pathlib import Path

import requests

BASE = "https://note.com"
ROOT = Path(__file__).parent
QUEUE = ROOT / "queue"
POSTED = ROOT / "posted"


def parse_article(path: Path) -> tuple[str, str]:
    """1行目の `# タイトル` を題名、残りを本文(Markdown)として返す。"""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or not lines[0].startswith("# "):
        sys.exit(f"{path.name}: 1行目は '# タイトル' にしてください")
    return lines[0][2:].strip(), "\n".join(lines[1:]).strip()


def to_note_html(md: str) -> str:
    """段落・見出しだけを扱う簡易変換。note のエディタは要素ごとに uuid を要求する。"""
    out = []
    for block in re.split(r"\n{2,}", md):
        block = block.strip()
        if not block:
            continue
        uid = str(uuid.uuid4())
        m = re.match(r"(#{2,3})\s+(.*)", block)
        if m:
            tag = "h2" if len(m.group(1)) == 2 else "h3"
            text = html.escape(m.group(2))
        else:
            tag = "p"
            text = "<br>".join(html.escape(l) for l in block.splitlines())
        out.append(f'<{tag} name="{uid}" id="{uid}">{text}</{tag}>')
    return "".join(out)


def save_draft(title: str, body_html: str, cookie: str) -> str:
    s = requests.Session()
    s.headers.update({
        "Cookie": cookie,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Referer": f"{BASE}/",
    })
    r = s.post(f"{BASE}/api/v1/text_notes", json={"template_key": None}, timeout=30)
    r.raise_for_status()
    data = r.json()["data"]
    note_id, key = data["id"], data["key"]

    r = s.post(
        f"{BASE}/api/v1/text_notes/draft_save",
        params={"id": note_id, "is_temp_saved": "true"},
        json={"name": title, "body": body_html, "body_length": len(body_html), "index": False},
        timeout=30,
    )
    r.raise_for_status()
    return f"{BASE}/notes/{key}/edit"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="送信せず変換結果だけ表示")
    args = ap.parse_args()

    queue = sorted(QUEUE.glob("*.md"))
    if not queue:
        print("queue が空です。note/queue/ に記事を追加してください。")
        return
    path = queue[0]
    title, md = parse_article(path)
    body = to_note_html(md)

    if args.dry_run:
        print(f"[dry-run] {path.name}\ntitle: {title}\n{body}")
        return

    cookie = os.environ.get("NOTE_COOKIE")
    if not cookie:
        sys.exit("NOTE_COOKIE が未設定です")
    url = save_draft(title, body, cookie)
    POSTED.mkdir(exist_ok=True)
    shutil.move(str(path), POSTED / path.name)
    print(f"下書きを保存しました: {url}")


if __name__ == "__main__":
    main()
