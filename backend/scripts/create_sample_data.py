#!/usr/bin/env python3
"""
テスト用サンプルデータ作成スクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.models import SessionLocal, Horse
from datetime import datetime, timedelta
import random
import json

def create_sample_data():
    pass

if __name__ == "__main__":
    create_sample_data() 