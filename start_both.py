#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同時啟動廣播引擎和GUI的腳本
- 廣播引擎: telegram_bot_standalone.py (後台自動排程)
- GUI界面: working_gui.py (完整功能管理界面)
"""
import subprocess
import sys
import os
import time
from pathlib import Path

def start_both():
    """啟動廣播系統（建議分別啟動避免衝突）"""
    print("🚀 正在啟動 RG Telegram 廣播系統...")
    print("⚠️  警告：由於 Telegram Session 衝突問題")
    print("📋 建議操作方式：")
    print("  1️⃣ 只啟動 GUI 界面 (working_gui.py) - 包含排程功能")
    print("  2️⃣ 或分別啟動：先關閉GUI，再啟動 telegram_bot_standalone.py")
    print()
    print("🔄 目前將啟動 GUI 界面...")
    print()
    
    # 確保在正確目錄
    app_dir = Path(__file__).parent
    os.chdir(app_dir)
    
    # Python 執行檔路徑
    python_path = sys.executable
    print(f"使用 Python: {python_path}")
    
    try:
        print("🖥️  啟動GUI管理界面...")
        
        # 直接啟動 GUI（前景執行）
        gui_process = subprocess.run([
            python_path, "working_gui.py"
        ])
        
        print("✅ GUI 已關閉")
        print()
        print("💡 如需純排程功能（無GUI），請執行：")
        print("   python3 telegram_bot_standalone.py")
        
    except KeyboardInterrupt:
        print("\n⚠️  收到中斷信號，正在停止...")
        print("✅ 程式已停止")
        
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")
        print("💡 建議：請嘗試直接執行 python3 working_gui.py")

if __name__ == "__main__":
    start_both()