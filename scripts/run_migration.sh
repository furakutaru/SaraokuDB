#!/bin/bash

# エラーが発生したら即時終了
set -e

# 色の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 現在の日時を取得
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# ディレクトリの設定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${SCRIPT_DIR}/../static-frontend/public/data"
BACKUP_DIR="${SCRIPT_DIR}/../data_backup"
OUTPUT_DIR="${SCRIPT_DIR}/../static-frontend/public/data/migrated"

# 必要なディレクトリを作成
mkdir -p "${BACKUP_DIR}" "${OUTPUT_DIR}"

# バックアップファイルのパス
HORSES_BACKUP="${BACKUP_DIR}/horses_${TIMESTAMP}.json"
AUCTION_BACKUP="${BACKUP_DIR}/auction_history_${TIMESTAMP}.json"
MIGRATED_BACKUP="${BACKUP_DIR}/migrated_${TIMESTAMP}.json"

# 入力ファイルのパス
HORSES_SRC="${DATA_DIR}/horses.json"
AUCTION_SRC="${DATA_DIR}/auction_history.json"

# 出力ファイルのパス
OUTPUT_FILE="${OUTPUT_DIR}/horses_unified_${TIMESTAMP}.json"
LATEST_FILE="${OUTPUT_DIR}/horses_latest.json"

# バージョン情報
SCRIPT_VERSION="1.0.0"

# ヘルプメッセージ
function show_help {
    echo "使用方法: $0 [オプション]"
    echo ""
    echo "オプション:"
    echo "  -h, --help     このヘルプを表示"
    echo "  -v, --version  バージョン情報を表示"
    echo "  --dry-run      実際の変更を行わずに実行"
    echo ""
    echo "このスクリプトは、馬データを新しい統合スキーマに移行します。"
    echo "移行前に自動的にバックアップが作成されます。"
}

# バージョン情報を表示
function show_version {
    echo "run_migration.sh バージョン ${SCRIPT_VERSION}"
    echo "移行スクリプト バージョン 1.1.0"
    exit 0
}

# オプションの解析
DRY_RUN=false
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--version)
            show_version
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "エラー: 不明なオプション: $1"
            show_help
            exit 1
            ;;
    esac
done

# ヘッダーを表示
echo -e "${GREEN}=== 馬データ移行ツール ===${NC}"
echo -e "開始時刻: $(date)"
echo -e "バージョン: ${SCRIPT_VERSION}"
echo -e "ドライラン: ${DRY_RUN}"
echo ""

# 入力ファイルの存在確認
for file in "${HORSES_SRC}" "${AUCTION_SRC}"; do
    if [[ ! -f "${file}" ]]; then
        echo -e "${RED}エラー: ファイルが見つかりません: ${file}${NC}"
        exit 1
    fi
done

# バックアップを作成
function create_backup {
    echo -e "${YELLOW}バックアップを作成しています...${NC}"
    
    if [[ "${DRY_RUN}" = false ]]; then
        cp "${HORSES_SRC}" "${HORSES_BACKUP}"
        cp "${AUCTION_SRC}" "${AUCTION_BACKUP}"
        echo -e "バックアップが作成されました:"
        echo -e "  - ${HORSES_BACKUP}"
        echo -e "  - ${AUCTION_BACKUP}"
    else
        echo -e "[ドライラン] バックアップが作成されます:"
        echo -e "  - ${HORSES_BACKUP}"
        echo -e "  - ${AUCTION_BACKUP}"
    fi
}

# 移行を実行
function run_migration {
    echo -e "\n${YELLOW}データの移行を開始します...${NC}"
    
    if [[ "${DRY_RUN}" = false ]]; then
        python3 "${SCRIPT_DIR}/migrate_to_unified_schema.py" \
            "${HORSES_SRC}" \
            "${AUCTION_SRC}" \
            "${OUTPUT_FILE}"
        
        # 最新のファイルとしてコピー
        cp "${OUTPUT_FILE}" "${LATEST_FILE}"
        
        echo -e "\n${GREEN}移行が完了しました:${NC}"
        echo -e "  - 出力ファイル: ${OUTPUT_FILE}"
        echo -e "  - 最新ファイル: ${LATEST_FILE}"
    else
        echo -e "[ドライラン] 以下のコマンドが実行されます:"
        echo "python3 \"${SCRIPT_DIR}/migrate_to_unified_schema.py\" \"${HORSES_SRC}\" \"${AUCTION_SRC}\" \"${OUTPUT_FILE}\""
        echo "cp \"${OUTPUT_FILE}\" \"${LATEST_FILE}\""
    fi
}

# データを検証
function validate_data {
    echo -e "\n${YELLOW}データを検証しています...${NC}"
    
    if [[ "${DRY_RUN}" = false ]]; then
        if [[ -f "${OUTPUT_FILE}" ]]; then
            python3 "${SCRIPT_DIR}/validate_migrated_data.py" "${OUTPUT_FILE}"
            if [[ $? -ne 0 ]]; then
                echo -e "${RED}エラー: データの検証に失敗しました${NC}"
                exit 1
            fi
        else
            echo -e "${RED}エラー: 出力ファイルが見つかりません: ${OUTPUT_FILE}${NC}"
            exit 1
        fi
    else
        echo -e "[ドライラン] 以下のコマンドが実行されます:"
        echo "python3 \"${SCRIPT_DIR}/validate_migrated_data.py\" \"${OUTPUT_FILE}\""
    fi
}

# メイン処理
function main {
    # バックアップを作成
    create_backup
    
    # 移行を実行
    run_migration
    
    # データを検証
    validate_data
    
    echo -e "\n${GREEN}=== 移行が完了しました ===${NC}"
    echo -e "完了時刻: $(date)"
}

# メイン処理を実行
main
