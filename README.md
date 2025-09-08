# ArXiv Webhook Service

Notion の webhook から arXiv の論文 URL を受け取り、論文の情報を取得して Notion ページを自動更新する FastAPI サービスです。

## 機能

- Notion の webhook ペイロードから arXiv の URL を抽出
- arXiv ライブラリを使用して論文のタイトルと著者を取得
- Notion ページの title と author プロパティを自動更新

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env`ファイルを作成し、以下の環境変数を設定してください：

```bash
# Notion Integration Token
NOTION_TOKEN=secret_your_notion_integration_token_here
```

Notion Integration Token の取得方法：

1. https://www.notion.so/my-integrations にアクセス
2. 新しい integration を作成
3. 生成されたトークンをコピー
4. 対象の Notion データベース/ページに integration を招待

### 3. ローカル実行

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API エンドポイント

### GET /

ヘルスチェック用エンドポイント

### POST /webhook

Notion からの webhook を受け取るエンドポイント

期待されるペイロード形式：

```json
{
  "data": {
    "id": "page_id",
    "properties": {
      "Link": {
        "url": "https://arxiv.org/abs/XXXX.XXXXX"
      }
    }
  }
}
```

## Render へのデプロイ

1. GitHub リポジトリを作成
2. Render で新しい Web Service を作成
3. リポジトリを指定
4. 環境変数`NOTION_TOKEN`を設定
5. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

## 使用方法

1. Notion でデータベースを作成し、以下のプロパティを追加：

   - `Link`（URL 型）: arXiv の URL 用
   - `Title`（タイトル型）: 論文タイトル用（自動更新）
   - `Authors`（リッチテキスト型）: 著者名用（自動更新）
   - `Summary`（リッチテキスト型）: 論文要約用（自動更新）
   - `Publication Year`（数値型）: 出版年用（自動更新）

2. Notion の automation または webhook で arXiv の URL が入力されたときにこのサービスの webhook エンドポイントに送信するよう設定

3. サービスが自動的に論文情報を取得してページを更新します
