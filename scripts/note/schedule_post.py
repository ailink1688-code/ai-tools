"""
noteに記事を作成し、「予約投稿」として公開日時をセットする。

ワークフロー想定:
  1. Claudeがタイトルから本文を作成し、ユーザーがチャット上でレビュー・承認する
  2. 承認後、本スクリプトを --confirm 付きで実行し、次に空いている
     毎日06:30/12:00/18:00(JST)の枠に予約投稿として登録する

使い方:
    python schedule_post.py --title "タイトル" --body-file body.md --confirm
    python schedule_post.py --title "タイトル" --body-file body.md          # dry-run(最終確定クリックはしない)
    python schedule_post.py --title "タイトル" --body-file body.md \
        --slot "2026-09-20 06:30" --confirm                                # 枠を手動指定

注意:
  note.comのUI(プレースホルダー文言・ボタン名)は本実装時点(2026-09)の
  公開情報をもとにしており、Playwrightでの実際の動作確認はしていない
  (このスクリプトを書いた実行環境からnote.comへのネットワークアクセスが
  ポリシーでブロックされていたため)。初回はheadedモードで実行し、
  --confirmなしのdry-runでスクリーンショットを確認してから本番実行すること。
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from playwright.sync_api import Page, TimeoutError as PWTimeoutError, sync_playwright

from slots import JST, compute_next_slot, load_booked_slots, record_slot

HERE = Path(__file__).parent
STATE_PATH = HERE / "state.json"
LOG_PATH = HERE / "scheduled_log.json"
SCREENSHOT_DIR = HERE / "screenshots"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True)
    body_group = parser.add_mutually_exclusive_group(required=True)
    body_group.add_argument("--body-file", type=Path)
    body_group.add_argument("--body", type=str)
    parser.add_argument(
        "--slot",
        type=str,
        default="auto",
        help='"auto" (既定) か "YYYY-MM-DD HH:MM" 形式で予約日時を指定',
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="指定しない場合は最終確定(予約投稿ボタン)クリック前で停止するdry-run",
    )
    parser.add_argument("--headed", action="store_true", help="ブラウザを表示して実行")
    return parser.parse_args()


def resolve_slot(slot_arg: str) -> datetime:
    if slot_arg == "auto":
        booked = load_booked_slots(LOG_PATH)
        return compute_next_slot(datetime.now(JST), booked)
    naive = datetime.strptime(slot_arg, "%Y-%m-%d %H:%M")
    return naive.replace(tzinfo=JST)


def dump_debug(page: Page, name: str) -> None:
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    png_path = SCREENSHOT_DIR / f"{stamp}_{name}.png"
    html_path = SCREENSHOT_DIR / f"{stamp}_{name}.html"
    try:
        page.screenshot(path=str(png_path), full_page=True)
        html_path.write_text(page.content(), encoding="utf-8")
        print(f"デバッグ情報を保存しました: {png_path} / {html_path}", file=sys.stderr)
    except Exception as exc:  # noqa: BLE001
        print(f"デバッグ情報の保存に失敗: {exc}", file=sys.stderr)


def click_first(page: Page, names: list[str], *, timeout: int = 5000):
    last_error: Exception | None = None
    for name in names:
        try:
            locator = page.get_by_role("button", name=name).first
            locator.wait_for(state="visible", timeout=timeout)
            locator.click()
            return
        except PWTimeoutError as exc:  # noqa: PERF203
            last_error = exc
            continue
    raise RuntimeError(f"次のボタンが見つかりませんでした: {names}") from last_error


def fill_new_post(page: Page, title: str, body: str) -> None:
    page.goto("https://note.com/notes/new", wait_until="networkidle")

    title_candidates = ["記事タイトル", "タイトル"]
    title_field = None
    for placeholder in title_candidates:
        loc = page.get_by_placeholder(placeholder)
        if loc.count() > 0:
            title_field = loc.first
            break
    if title_field is None:
        dump_debug(page, "title_field_not_found")
        raise RuntimeError("タイトル入力欄が見つかりませんでした")
    title_field.click()
    title_field.fill(title)

    body_candidates = ["本文を入力してください", "本文を書く", "ここから記事を書きはじめてください"]
    body_field = None
    for placeholder in body_candidates:
        loc = page.get_by_placeholder(placeholder)
        if loc.count() > 0:
            body_field = loc.first
            break
    if body_field is None:
        dump_debug(page, "body_field_not_found")
        raise RuntimeError("本文入力欄が見つかりませんでした")
    body_field.click()
    body_field.type(body)


def set_schedule(page: Page, slot: datetime, confirm: bool) -> None:
    click_first(page, ["公開に進む", "投稿に進む"])

    schedule_toggle_candidates = ["日時を設定", "公開日時を設定"]
    toggled = False
    for name in schedule_toggle_candidates:
        loc = page.get_by_text(name).first
        if loc.count() > 0:
            loc.click()
            toggled = True
            break
    if not toggled:
        dump_debug(page, "schedule_toggle_not_found")
        raise RuntimeError("「日時を設定」の操作項目が見つかりませんでした")

    date_str = slot.strftime("%Y-%m-%d")
    time_str = slot.strftime("%H:%M")

    date_input = page.locator('input[type="date"]').first
    time_input = page.locator('input[type="time"]').first
    if date_input.count() == 0 or time_input.count() == 0:
        dump_debug(page, "datetime_inputs_not_found")
        raise RuntimeError("日時入力欄が見つかりませんでした")
    date_input.fill(date_str)
    time_input.fill(time_str)

    if not confirm:
        dump_debug(page, "dry_run_before_final_click")
        print(
            f"[dry-run] 「予約投稿」ボタンはクリックしていません。"
            f"予約予定日時: {slot.isoformat()}"
        )
        return

    click_first(page, ["予約投稿"])
    page.wait_for_timeout(1500)
    dump_debug(page, "after_confirm")


def main() -> None:
    args = parse_args()
    load_dotenv(HERE / ".env")

    body = args.body if args.body is not None else args.body_file.read_text(encoding="utf-8")
    slot = resolve_slot(args.slot)

    if not STATE_PATH.exists():
        raise SystemExit(
            f"{STATE_PATH} がありません。先に login_and_save_session.py を実行してください。"
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        context = browser.new_context(storage_state=str(STATE_PATH))
        page = context.new_page()
        try:
            fill_new_post(page, args.title, body)
            set_schedule(page, slot, args.confirm)
        except Exception:
            dump_debug(page, "error")
            raise
        finally:
            browser.close()

    if args.confirm:
        record_slot(LOG_PATH, args.title, slot)
        print(f"予約投稿を設定しました: {args.title} -> {slot.isoformat()}")
    else:
        print("dry-runのため scheduled_log.json への記録は行っていません。")


if __name__ == "__main__":
    main()
