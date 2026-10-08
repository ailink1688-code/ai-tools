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

## note 下書き自動保存（おうえん）

`note/queue/*.md` の記事を、ファイル名順に1日1本 note の**下書き**として保存します（公開は note 上で手動）。保存済みは `note/posted/` へ移動します。

- 記事の書式: 1行目 `# タイトル`、以降は Markdown（`##`/`###` 見出しと段落に対応）
- 実行: `.github/workflows/note-draft.yml`（毎日 07:00 JST / 手動実行も可）
- 必要な Secret: `NOTE_COOKIE` — ブラウザで note にログインし、開発者ツールから `note.com` への API リクエストの `Cookie` ヘッダー値（`_note_session_v5` を含む）をコピーして登録
- ローカル確認: `python note/post_draft.py --dry-run`
- 注意: 非公式 API を使うため、note 側の仕様変更で動かなくなる場合があります。Cookie は定期的に失効します
