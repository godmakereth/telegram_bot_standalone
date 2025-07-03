# 🤖 RG Telegram 廣播系統 - 完整版

一個功能完整的 Telegram 廣播機器人系統，支援 GUI 圖形界面和 Telegram 指令雙重控制方式，具備智能排程、多媒體廣播、群組管理等功能。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

## ✨ 功能特色

- 🖥️ **雙重控制介面**: GUI 圖形界面 + Telegram 指令控制
- ⏰ **智能排程系統**: 支援多時間點自動廣播，防重複執行
- 📱 **多媒體支援**: 文字、圖片、影片、GIF 混合廣播
- 👥 **群組管理**: 批量管理廣播目標群組
- 🔐 **權限控制**: 多重管理員權限管理
- 📊 **即時監控**: 廣播狀態、歷史記錄、系統日誌追蹤
- 🛡️ **容錯設計**: 重試機制、連接重建、錯誤恢復
- 📋 **活動管理**: 支援多個廣播活動（A、B、C、D、E）

## 🚀 快速開始

### 1. 系統需求

- Python 3.8 或更高版本
- Telegram API 憑證（API ID、API Hash）
- 已驗證的 Telegram 帳號

### 2. 安裝依賴

```bash
pip install -r requirements.txt
```

### 3. 啟動方式

#### 選項 1：GUI + 後台服務（推薦）
```bash
# 同時啟動 GUI 和排程服務
python start_both.py
```

#### 選項 2：僅 GUI 界面
```bash
# 僅啟動 GUI 管理界面
python working_gui.py
```

#### 選項 3：僅後台服務
```bash
# 僅啟動排程服務（命令行模式）
python telegram_bot_standalone.py
```

#### 選項 4：交互式啟動
```bash
# 選擇啟動方式的菜單
python simple_launcher.py
```

### 4. 初始設置

1. **配置 API 憑證**
   - 在 GUI 的「🔗 連接設定」標籤頁輸入：
     - API ID（從 https://my.telegram.org 獲取）
     - API Hash
     - 手機號碼（包含國碼，如：+886912345678）
   - 點擊「🔗 連接Telegram」完成驗證

2. **準備廣播內容**
   ```
   content_databases/
   ├── A/
   │   ├── message.txt      # 文字內容
   │   ├── image1.jpg       # 圖片（可選）
   │   └── video.mp4        # 影片（可選）
   ├── B/
   │   ├── message.txt
   │   └── animation.gif    # GIF（可選）
   └── ...
   ```

3. **設定廣播群組**
   - 在 GUI 的「⚙️ 系統管理」標籤頁掃描群組
   - 或使用 Telegram 指令 `/add_groups`

4. **配置自動排程**
   - 在 GUI 的「📡 廣播控制」標籤頁設定排程
   - 或使用指令 `/add_schedule 09:00 A`

## 🖥️ GUI 界面詳解

### 主要標籤頁

#### 🔗 連接設定
- **連接狀態顯示**: 實時顯示 Telegram 連接狀態
- **🔗 連接Telegram**: 建立 Telegram 連接
- **🔌 斷開連接**: 斷開 Telegram 連接
- **🔄 重新載入配置**: 重新載入所有配置文件
- **API 設定資訊**: 顯示當前 API 配置（僅顯示）

#### 📡 廣播控制
**手動廣播區域:**
- **活動選擇**: 選擇要廣播的活動（A、B、C、D、E）
- **🚀 立即廣播**: 立即執行選定活動的廣播
- **👁️ 預覽內容**: 預覽活動內容和目標群組
- **🧪 測試廣播**: 測試廣播功能（不實際發送）
- **🔄 刷新活動**: 重新載入活動列表

**排程控制區域:**
- **啟用自動排程**: 開關自動排程功能
- **📅 查看排程**: 查看所有已設定的排程
- **➕ 新增排程**: 新增新的廣播排程
- **➖ 移除排程**: 移除現有排程
- **🔄 重新載入**: 刷新排程狀態

#### ⚙️ 系統管理
**群組管理區域:**
- **群組列表顯示**: 顯示所有目標群組和控制群組
- **群組計數**: 顯示已配置的群組數量
- **➕ 添加群組**: 新增廣播目標群組
- **➖ 移除群組**: 移除現有群組
- **📋 管理群組**: 進階群組管理對話框
- **🔄 重新載入**: 刷新群組列表
- **🌐 掃描群組**: 掃描所有可用群組
- **📊 群組詳情**: 顯示詳細群組資訊

**活動內容區域:**
- **內容摘要顯示**: 顯示所有活動的內容摘要
- **🔄 重新載入內容**: 刷新活動內容

#### 📋 系統狀態
- **即時日誌顯示**: 顯示系統運行日誌
- **🗑️ 清空日誌**: 清空當前顯示的日誌
- **💾 保存日誌**: 將日誌保存到文件
- **🔄 系統重啟**: 重啟整個系統

## 🤖 Telegram Bot 指令

### 基本指令
```
/help - 顯示所有可用指令
/status - 顯示當前系統狀態
/restart - 重啟機器人系統
/logs [數量] - 顯示最近的日誌條目
/config - 顯示當前配置
```

### 群組管理指令
```
📋 群組資訊
/list_groups 或 /lg - 列出所有廣播目標群組
/scan_groups 或 /sg - 掃描可用群組
/my_groups 或 /mg - 顯示機器人所在的群組

➕ 新增群組
/add_groups - 互動式群組新增
/add_groups <群組ID> - 透過ID新增群組
/add_target - 新增廣播目標群組（別名）
/add_target <群組ID> - 透過ID新增目標群組

➖ 移除群組
/remove_groups - 互動式群組移除
/remove_groups <群組ID> - 透過ID移除群組
/remove_target - 移除廣播目標群組
/remove_target <群組ID> - 透過ID移除目標群組
```

### 廣播操作指令
```
📢 立即廣播
/broadcast <活動> 或 /bc <活動> - 廣播指定活動（A-E）
/q <活動> - 快速廣播（跳過確認）

📊 廣播歷史
/broadcast_history [數量] 或 /bh [數量] - 查看廣播歷史
/history [數量] - 查看廣播歷史（別名）
```

### 排程管理指令
```
⏰ 排程操作
/add_schedule <時間> <活動> - 新增排程（格式：HH:MM）
/as <時間> <活動> - 新增排程（快捷別名）
/list_schedules 或 /ls - 列出所有排程
/remove_schedule - 互動式移除排程
/remove_schedule <編號> - 透過編號移除排程

🔧 排程控制
/enable - 啟用自動排程
/disable - 停用自動排程
```

### 管理員管理指令
```
👤 管理員操作
/add_admin <用戶> - 新增管理員用戶
/remove_admin <用戶> - 移除管理員用戶
/sync_admins - 同步管理員列表
/list_admins - 列出所有管理員用戶
```

### 快速指令
```
⚡ 快速操作
/s - 快速狀態檢查
/c - 快速活動列表
/q <活動> - 快速廣播指定活動
```

## 📁 專案架構

### 核心組件
```
├── 核心模組
│   ├── config.py                    # 配置管理器
│   ├── telegram_client.py           # Telegram 客戶端管理
│   ├── broadcast_manager.py         # 廣播管理引擎
│   ├── scheduler.py                 # 排程系統
│   ├── message_manager.py           # 消息管理器
│   ├── command_handler.py           # 指令處理器
│   ├── permissions.py               # 權限管理器
│   └── content_manager.py           # 內容管理器
│
├── GUI 應用
│   ├── working_gui.py               # 主要 GUI 界面
│   ├── integrated_app.py            # 整合應用
│   ├── gui.py                       # 基礎 GUI
│   └── ultimate_gui_app.py          # 完整 GUI 應用
│
├── 後台服務
│   ├── telegram_bot_standalone.py   # 獨立機器人服務
│   ├── broadcast_system.py          # 廣播系統
│   └── gui_broadcast_bridge.py      # GUI 橋接器
│
├── 啟動器
│   ├── start_app.py                 # 主啟動器
│   ├── start_both.py                # 雙服務啟動器
│   ├── simple_launcher.py           # 簡化啟動器
│   └── quick_start.py               # 快速啟動器
│
└── 工具模組
    ├── utils/
    │   ├── logger.py                # 日誌管理
    │   └── helpers.py               # 輔助函數
    └── tests/                       # 測試模組
```

### 數據結構
```
data/
├── 配置文件
│   ├── settings.json                # 系統設定和 API 配置
│   ├── broadcast_config.json        # 廣播和排程配置
│   ├── admins.json                  # 管理員列表
│   ├── broadcast_history.json       # 廣播歷史記錄
│   └── scheduler_execution_records.json # 排程執行記錄
│
├── 內容數據庫
│   └── content_databases/
│       ├── A/                       # 活動 A 內容
│       │   ├── message.txt          # 文字內容
│       │   ├── image.jpg            # 圖片文件
│       │   └── video.mp4            # 影片文件
│       ├── B/                       # 活動 B 內容
│       └── ...
│
└── 日誌文件
    └── logs/
        ├── bot.log                  # 主程序日誌
        ├── broadcast.log            # 廣播操作日誌
        ├── error.log                # 錯誤日誌
        └── scheduler.log            # 排程日誌
```

## 🔧 運行模式

### 1. GUI 模式
- **用途**: 圖形界面管理和監控
- **特點**: 即時狀態顯示、點選操作、視覺化管理
- **啟動**: `python working_gui.py`

### 2. 命令行模式
- **用途**: 純後台運行，適合服務器部署
- **特點**: 24/7 自動排程、Telegram 指令控制
- **啟動**: `python telegram_bot_standalone.py`

### 3. 混合模式（推薦）
- **用途**: 同時享有 GUI 管理和自動排程
- **特點**: 最完整的功能體驗
- **啟動**: `python start_both.py`

## 🛠️ 高級配置

### API 憑證設定
在 `data/settings.json` 中配置：
```json
{
  "api_id": "您的_API_ID",
  "api_hash": "您的_API_HASH",
  "phone": "+886912345678",
  "session_file": "userbot.session"
}
```

### 廣播配置
在 `data/broadcast_config.json` 中配置：
```json
{
  "schedules": [
    {"time": "09:00", "campaign": "A"},
    {"time": "15:00", "campaign": "B"}
  ],
  "target_groups": [-1001234567890, -1009876543210],
  "control_group": -1001122334455,
  "enabled": true,
  "broadcast_delay": 5,
  "max_retries": 3
}
```

### 管理員設定
在 `data/admins.json` 中配置：
```json
{
  "admins": [123456789, 987654321],
  "auto_sync": true,
  "last_sync": "2025-01-01T00:00:00"
}
```

## 🔍 故障排除

### 常見問題

#### 1. 連接問題
**問題**: 無法連接 Telegram
**解決方案**:
- 檢查網路連接
- 確認 API 憑證正確
- 手機號碼包含國碼（如：+886912345678）
- 確認 Telegram 帳號已驗證

#### 2. 排程不執行
**問題**: 設定的排程沒有執行
**解決方案**:
- 確認已啟動 `telegram_bot_standalone.py`
- 檢查排程是否已啟用（`/enable` 指令）
- 確認排程時間格式正確（HH:MM）
- 檢查活動內容是否存在

#### 3. 廣播失敗
**問題**: 廣播無法發送到群組
**解決方案**:
- 確認機器人已加入目標群組
- 檢查群組權限設定
- 確認活動內容文件存在
- 查看日誌文件錯誤訊息

#### 4. 指令無響應
**問題**: Telegram 指令沒有回應
**解決方案**:
- 確認用戶已設為管理員
- 檢查是否在控制群組中使用指令
- 重新啟動機器人服務
- 檢查權限設定

### 日誌分析

系統提供多層次的日誌記錄：

- **`data/logs/bot.log`**: 主程序運行日誌
- **`data/logs/broadcast.log`**: 廣播操作詳細記錄
- **`data/logs/error.log`**: 錯誤和異常記錄
- **`data/logs/scheduler.log`**: 排程執行記錄

## 📊 監控和維護

### 狀態監控
- GUI 即時狀態顯示
- Telegram 指令 `/status` 查看系統狀態
- 日誌文件追蹤詳細操作記錄

### 定期維護
- 定期備份配置文件
- 清理過舊的日誌文件
- 檢查排程執行記錄
- 更新管理員列表

### 性能優化
- 調整廣播間隔 (`broadcast_delay`)
- 設定合適的重試次數 (`max_retries`)
- 定期清理歷史記錄

## 🔐 安全注意事項

1. **API 憑證保護**
   - 不要將 API 憑證分享給他人
   - 定期更改 API Hash（如有必要）
   - 安全存儲 session 文件

2. **權限管理**
   - 謹慎設定管理員權限
   - 定期檢查管理員列表
   - 使用私人群組作為控制群組

3. **數據備份**
   - 定期備份配置文件
   - 保存廣播歷史記錄
   - 備份重要的活動內容

## 📈 更新日誌

### v3.0 (完整版) - 2025.01
- ✨ 完整的雙組件架構（GUI + 後台服務）
- ✨ 修復排程邏輯錯誤（只有成功才標記完成）
- ✨ 新增 `start_both.py` 統一啟動器
- ✨ 改進 GUI 界面和功能完整性
- ✨ 增強錯誤處理和容錯機制
- ✨ 完善的文檔和使用說明

### v2.0 (整合版)
- ✨ 新增 GUI 圖形界面
- ✨ 整合 GUI 和 Telegram 指令控制
- ✨ 改進錯誤處理和用戶體驗
- ✨ 新增整合測試功能

### v1.0 (指令版)
- ✅ 基本 Telegram 指令功能
- ✅ 排程廣播系統
- ✅ 多媒體內容支援
- ✅ 管理員權限控制

## 📞 技術支援

如果遇到問題或需要協助：

1. 查閱本 README 文件
2. 檢查 `data/logs/` 目錄下的日誌文件
3. 使用 GUI 狀態監控功能
4. 透過 Telegram 指令 `/help` 獲取即時幫助

## 📄 許可證

MIT License - 詳見 LICENSE 文件

---

**開發者**: RG Team  
**版本**: v3.0  
**最後更新**: 2025-01-03