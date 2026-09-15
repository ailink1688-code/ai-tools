# ai-tools

Claude Code から使う各種ツール連携をまとめるリポジトリです。

## Metricool 連携

Metricool 公式の MCP サーバー（`https://mcp.metricool.ai/mcp`）をプロジェクトスコープで登録済みです（`.mcp.json`）。API トークンの発行は不要で、Metricool アカウントに対する OAuth 認可だけで使えます。

### 初回接続（OAuth 認可）

このリポジトリを Claude Code で開いた状態で、以下のいずれかを実行してください。

- Claude Code (CLI/Web) の場合: `/mcp` を実行し、`metricool` を選択して認可フローを完了する
- Claude Desktop の場合: 初回に Metricool のツールを呼び出すとブラウザで OAuth 認可画面が開く

認可時に付与するスコープ:

- `mcp:read` — ブランド設定・アナリティクスの参照
- `mcp:write` — 投稿の作成・スケジュール変更

### 使える主なツール

| ツール | 用途 |
|---|---|
| `get_brand_settings` | 連携済みブランド・SNSアカウント一覧の取得 |
| `get_scheduled_posts` | 指定期間内の予約投稿一覧の取得 |
| `get_best_time_to_post_by_network` | ネットワークごとの投稿最適時間の提案 |
| `get_analytics_available_metrics` | 取得可能な分析指標IDの一覧 |
| `get_analytics_data_by_metrics` | 指定した指標のアナリティクスデータ取得 |
| `create_scheduled_post` | Instagram / Facebook / X / LinkedIn / TikTok / YouTube / Pinterest / Threads / Bluesky / GBP などへの投稿予約作成 |
| `update_scheduled_post` | 既存の予約投稿の更新 |

### 使い方の例（Claude への指示）

- 「来週分の予約投稿一覧を見せて」
- 「〇〇ブランドのInstagramに『新商品のお知らせ』という投稿を明日10時に予約して」
- 「LinkedInの投稿に最適な曜日・時間帯を教えて」

### 参考

- [Metricool MCP について（公式）](https://metricool.com/metricool-mcp-claude/)
- [Metricool MCP 接続方法（ヘルプセンター）](https://help.metricool.com/how-to-connect-metricools-mcp-eqp9h)
- [Metricool MCP FAQ](https://help.metricool.com/faqs-about-the-metricool-mcp-1i3w0)

## note 予約投稿ワークフロー（`scripts/note/`）

note.com に公式の投稿APIは無いため、Playwright によるブラウザ自動操作で「予約投稿」を設定するスクリプトです（note の予約投稿機能自体は note プレミアム会員限定・Web版のみ）。

想定するワークフロー:

1. ユーザーが記事タイトルをClaudeに渡す
2. Claudeが本文を作成し、チャット上でユーザーがレビュー・修正
3. 承認後、Claudeが `schedule_post.py` を実行し、毎日 **06:30 / 12:00 / 18:00（JST）** の枠のうち直近の空き枠に予約投稿として登録する（`slots.py` が既存の予約と重複しないよう自動計算）

### セットアップ

```bash
cd scripts/note
pip install -r requirements.txt
cp .env.example .env   # NOTE_EMAIL / NOTE_PASSWORD を設定（.envはコミットしない）
python login_and_save_session.py   # 初回のみ。headedブラウザでログインし state.json を保存
```

### 使い方

```bash
# dry-run（最終確定クリックはせず、動作確認用スクリーンショットを screenshots/ に保存）
python schedule_post.py --title "タイトル" --body-file body.md

# 本番実行（次の空き枠に予約投稿を確定）
python schedule_post.py --title "タイトル" --body-file body.md --confirm

# 枠を手動指定したい場合
python schedule_post.py --title "タイトル" --body-file body.md --slot "2026-09-20 06:30" --confirm
```

### 既知の制約

- **この Claude Code 環境からは note.com への通信がネットワークポリシーでブロックされており、動作未検証**です。note.com に到達できる環境（ご自身のPCなど）で実行してください。
- UIのボタン名・入力欄は公開情報ベースの実装のため、note側の画面変更で選択できなくなる可能性があります。失敗時は `scripts/note/screenshots/` にスクリーンショットとHTMLを保存するので、それを見てセレクタを調整してください。
- ログイン情報（`.env`）とセッション（`state.json`）、予約履歴（`scheduled_log.json`）はコミットしない設定（`.gitignore`）にしています。
