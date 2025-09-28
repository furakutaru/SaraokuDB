#!/bin/bash

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# Python仮想環境をアクティベート
if [ -d "../.venv" ]; then
    source ../.venv/bin/activate
elif [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# 依存関係をインストール
pip install -r ../backend/requirements.txt

# スクレイピングスクリプトを実行
python scrape_and_save.py

# エラーが発生した場合は終了コード1で終了
if [ $? -ne 0 ]; then
    echo "Error: スクリプトの実行中にエラーが発生しました"
    exit 1
fi

echo "スクリプトが正常に完了しました"
exit 0
