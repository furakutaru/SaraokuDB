# サラブレッドオークション データベース

楽天サラブレッドオークションからデータをスクレイピングし、分析用のデータベースを構築するシステムです。

## 機能

- 楽天サラブレッドオークションからの自動データ取得
- netkeibaとの連携による賞金情報の更新
- SQLiteデータベースでのデータ保存
- Web APIによるデータアクセス
- 分析用のダッシュボード

## セットアップ

### 1. 依存関係のインストール

```bash
# macOS/Linux
python3 setup.py

# Windows
python setup.py
```

### 2. 環境変数の設定

```bash
cp .env.example .env
# .envファイルを編集して必要な設定を行う
```

### 3. データベースの初期化

```bash
# macOS/Linux
python3 -m backend.database.init_db

# Windows
python -m backend.database.init_db
```

### 4. サーバーの起動

```bash
# バックエンド
# macOS/Linux
python3 -m uvicorn backend.main:app --reload

# Windows
python -m uvicorn backend.main:app --reload

# フロントエンド（別ターミナル）
cd frontend
npm install
npm start
```

## 使用方法

1. スクレイピングの実行
   - 木曜オークション: 火曜18:00以降
   - 日曜オークション: 土曜18:00以降

2. データの確認
   - Web API: http://localhost:8000/docs
   - ダッシュボード: http://localhost:3000

## プロジェクト構造

```
SaraokuDB/
├── backend/
│   ├── database/
│   ├── models/
│   ├── scrapers/
│   ├── services/
│   └── main.py
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
├── data/
│   └── horses.db
└── requirements.txt
``` 