# teacher-data

OpenAI Whisper と Google Gemini の2モデルで音声を文字起こしし、比較・マージして Fine-tuning 用教師データ（JSONL）を生成するツールです。

## セットアップ

### 1. 依存インストール

**Mac / Linux**
```bash
uv sync
cd apps/web && npm install && cd ../..
```

**Windows**
```bat
uv sync
cd apps\web && npm install && cd ..\..
```

> `uv` がない場合: https://docs.astral.sh/uv/getting-started/installation/

### 2. 環境変数

```bash
cp .env.example .env
# .env を編集して API キーを設定
```

```env
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
```

## 起動

**Mac / Linux**
```bash
./start.sh
```

**Windows**
```bat
start.bat
```

- Web UI: http://localhost:3000
- API: http://localhost:8000

## Tailscale 経由で別PCからアクセスする場合

`start.sh` はすでに `0.0.0.0` でバインドしています。

1. サーバーPC・クライアントPCの両方で Tailscale にログイン
2. `.env` に以下を追記（`100.x.x.x` はサーバーの Tailscale IP）

```env
NEXT_PUBLIC_API_URL=http://100.x.x.x:8000/api/v1
```

3. サーバーPCで `./start.sh` を実行
4. クライアントPCから `http://100.x.x.x:3000` にアクセス

## CLI 単体で使う場合

```bash
# 音声ファイルを指定してデータセット生成
uv run teacher-data build path/to/audio/

# 結果確認
uv run teacher-data stats output/
```

## ディレクトリ構成

```
.
├── src/teacher_data/   # CLI パイプライン（Whisper・Gemini・マージ）
├── apps/api/           # FastAPI バックエンド
├── apps/web/           # Next.js フロントエンド
├── storage/            # アップロード音声・DB（gitignore）
└── .env.example        # 環境変数テンプレート
```
