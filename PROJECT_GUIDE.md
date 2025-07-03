# RG Telegram 廣播系統 - 專案說明

## 📋 專案概述

這是一個功能完整的 Telegram 自動廣播系統，支援定時排程、多群組廣播、內容管理等功能。

## 🚀 主要程式與功能

### 1. `telegram_bot_standalone.py` - 核心廣播引擎
**功能**：
- ✅ 自動排程廣播
- ✅ 多群組同步發送
- ✅ 廣播歷史記錄
- ✅ 錯誤處理與重試
- ✅ 排程執行監控

**啟動方式**：
```bash
# 前台運行（推薦測試時使用）
python3 telegram_bot_standalone.py

# 後台運行（推薦正式使用）
nohup python3 telegram_bot_standalone.py > telegram_bot.log 2>&1 &
```

**適用場景**：
- 純後台自動排程廣播
- 伺服器部署
- 無需圖形界面操作

---

### 2. `working_gui.py` - 圖形管理界面
**功能**：
- 🖥️ 完整的圖形化管理界面
- ⚙️ 排程設定與管理
- 📊 廣播歷史查看
- 🎯 群組管理
- 📁 內容管理
- 🔧 系統設定

**啟動方式**：
```bash
python3 working_gui.py
```

**適用場景**：
- 日常管理與設定
- 手動廣播操作
- 監控系統狀態
- 排程管理

---

### 3. `start_both.py` - 便捷啟動腳本
**功能**：
- 🔄 統一啟動入口
- ⚠️ 避免 Session 衝突
- 💡 使用建議提示

**啟動方式**：
```bash
python3 start_both.py
```

**注意事項**：
- 由於 Telegram Session 衝突問題，建議只使用一個程式
- 預設啟動 GUI 界面

---

## 📁 重要檔案說明

### 配置檔案
- `data/settings.json` - API 設定
- `data/broadcast_config.json` - 廣播與排程設定
- `data/admins.json` - 管理員清單
- `.env` - 環境變數設定

### 內容資料庫
- `data/content_databases/A/` - 活動 A 的廣播內容
- `data/content_databases/B/` - 活動 B 的廣播內容
- `data/content_databases/C/` - 活動 C 的廣播內容
- `data/content_databases/D/` - 活動 D 的廣播內容
- `data/content_databases/E/` - 活動 E 的廣播內容

### 日誌檔案
- `data/logs/bot.log` - 機器人運行日誌
- `data/logs/scheduler.log` - 排程執行日誌
- `data/logs/error.log` - 錯誤日誌

### 記錄檔案
- `data/broadcast_history.json` - 廣播歷史記錄
- `data/scheduler_execution_records.json` - 排程執行記錄

---

## 🎯 使用建議

### 💡 推薦配置

**日常管理使用**：
```bash
python3 working_gui.py
```
- 提供完整的圖形化管理功能
- 可設定排程、管理內容、監控狀態

**伺服器部署使用**：
```bash
nohup python3 telegram_bot_standalone.py > telegram_bot.log 2>&1 &
```
- 純後台運行，穩定可靠
- 適合長期無人值守運行

### ⚠️ 注意事項

1. **避免同時運行**：
   - 不要同時啟動 `telegram_bot_standalone.py` 和 `working_gui.py`
   - 會造成 Telegram Session 衝突

2. **Session 管理**：
   - 系統使用 `userbot.session` 檔案
   - 確保只有一個程式使用該 Session

3. **權限確認**：
   - 確保機器人在目標群組中
   - 確保機器人有發送訊息權限

---

## 🔧 系統要求

### 依賴套件
```bash
pip install -r requirements.txt
```

### 主要依賴
- `telethon` - Telegram 客戶端
- `tkinter` - GUI 界面
- `asyncio` - 異步處理
- `json` - 配置管理

### Python 版本
- 需要 Python 3.8 或更高版本

---

## 📊 功能特色

### ✅ 已實現功能
- 🤖 自動排程廣播
- 📱 多群組同時發送
- 🖼️ 支援文字、圖片、影片、GIF
- 📊 詳細的執行統計
- 🔄 自動重試機制
- 📝 完整的日誌記錄
- 🎮 圖形化管理界面
- ⚙️ 靈活的排程設定

### 🎯 廣播內容支援
- 📝 純文字訊息
- 🖼️ 圖片（JPG, PNG, WebP）
- 🎬 影片（MP4, AVI, MOV）
- 🎭 GIF 動圖
- 📎 其他檔案

---

## 🚀 快速開始

1. **設定 API 資訊**：
   編輯 `data/settings.json` 或 `.env` 檔案

2. **設定目標群組**：
   在 GUI 或配置檔中設定廣播目標群組

3. **準備廣播內容**：
   在 `data/content_databases/` 目錄下準備內容

4. **設定排程**：
   使用 GUI 或編輯配置檔設定排程時間

5. **啟動系統**：
   ```bash
   # GUI 模式
   python3 working_gui.py
   
   # 或純後台模式
   python3 telegram_bot_standalone.py
   ```

---

## 📞 支援與維護

### 日誌查看
```bash
# 查看運行日誌
tail -f data/logs/bot.log

# 查看錯誤日誌
tail -f data/logs/error.log
```

### 狀態檢查
```bash
# 檢查程式是否運行
ps aux | grep python | grep telegram

# 檢查最新廣播記錄
cat data/broadcast_history.json | tail -20
```

### 重啟系統
```bash
# 停止現有程式
pkill -f telegram_bot_standalone

# 重新啟動
python3 telegram_bot_standalone.py
```

---

## 🎉 總結

這個 Telegram 廣播系統提供了完整的自動化廣播解決方案，支援圖形化管理和純後台運行兩種模式，適合不同的使用場景。系統穩定可靠，功能豐富，是進行 Telegram 群組管理的理想工具。