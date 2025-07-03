# 🏗️ RG Telegram 廣播系統 - 程式碼架構說明

## 📋 系統概覽

本系統採用模組化設計，分為核心引擎、GUI界面、和啟動器三大部分，支援多種運行模式和擴展需求。

## 🔧 核心架構

### 系統分層
```
┌─────────────────────────────────────────┐
│             用戶界面層                    │
├─────────────────────────────────────────┤
│   GUI 界面        │    Telegram 指令      │
│  working_gui.py   │   command_handler.py  │
├─────────────────────────────────────────┤
│             業務邏輯層                    │
├─────────────────────────────────────────┤
│  broadcast_manager.py │ scheduler.py     │
│  message_manager.py   │ permissions.py   │
├─────────────────────────────────────────┤
│             基礎服務層                    │
├─────────────────────────────────────────┤
│  telegram_client.py   │   config.py      │
├─────────────────────────────────────────┤
│             數據持久層                    │
└─────────────────────────────────────────┘
│         JSON 配置文件 & 日誌系統          │
└─────────────────────────────────────────┘
```

## 📁 核心模組詳解

### 🔧 基礎服務層

#### `config.py` - 配置管理器
```python
class ConfigManager:
    """統一配置管理"""
    
    主要功能：
    - API 配置管理 (api_id, api_hash, phone)
    - 廣播配置管理 (target_groups, schedules)
    - 管理員權限管理
    - 配置文件自動備份與恢復
    - 動態配置重載
    
    核心方法：
    - get_api_config()      # 獲取 API 配置
    - get_target_groups()   # 獲取廣播目標群組
    - get_schedules()       # 獲取排程配置
    - add_broadcast_history() # 記錄廣播歷史
```

#### `telegram_client.py` - Telegram 客戶端管理
```python
class TelegramClientManager:
    """Telegram 連接管理"""
    
    主要功能：
    - Telethon 客戶端封裝
    - 自動連接與重連機制
    - Session 管理
    - 群組資訊獲取
    - 消息發送接口
    
    核心方法：
    - start_client()        # 啟動客戶端連接
    - is_authorized()       # 檢查認證狀態
    - send_message()        # 發送消息
    - get_dialogs()         # 獲取群組列表
```

### 💼 業務邏輯層

#### `broadcast_manager.py` - 廣播管理引擎
```python
class BroadcastManager:
    """廣播引擎核心"""
    
    組件結構：
    ├── ContentLoader       # 內容載入器
    ├── BroadcastSender    # 發送引擎
    └── BroadcastManager   # 管理協調器
    
    主要功能：
    - 多媒體內容載入與驗證
    - 批量群組廣播
    - 發送狀態追蹤
    - 錯誤處理與重試
    - 廣播歷史記錄
    
    核心流程：
    1. 載入活動內容 (load_campaign_content)
    2. 驗證內容完整性 (validate_campaign_content)  
    3. 執行批量廣播 (execute_broadcast)
    4. 記錄執行結果
```

#### `scheduler.py` - 排程系統
```python
class BroadcastScheduler:
    """智能排程引擎"""
    
    主要功能：
    - 精確到分鐘的排程控制
    - 防重複執行機制
    - 排程結果通知
    - 執行狀態持久化
    - 異步排程循環
    
    核心邏輯：
    1. 排程循環監控 (_scheduler_loop)
    2. 時間匹配檢查
    3. 重複執行防護 (_is_already_executed_today)
    4. 廣播執行委派
    5. 結果記錄與通知
```

#### `message_manager.py` - 消息管理器
```python
class MessageManager:
    """消息處理中心"""
    
    主要功能：
    - 消息格式化
    - 批量消息發送
    - 發送隊列管理
    - 速率限制控制
    - 發送結果統計
```

#### `permissions.py` - 權限管理器
```python
class PermissionManager:
    """權限控制系統"""
    
    主要功能：
    - 管理員身份驗證
    - 指令權限檢查
    - 動態權限更新
    - 權限繼承機制
```

#### `command_handler.py` - 指令處理器
```python
class CommandHandler:
    """Telegram 指令處理"""
    
    指令分類：
    ├── 系統指令 (/help, /status, /restart)
    ├── 群組管理 (/add_groups, /list_groups)
    ├── 廣播操作 (/broadcast, /q)
    ├── 排程管理 (/add_schedule, /list_schedules)
    └── 管理員管理 (/add_admin, /list_admins)
    
    處理流程：
    1. 指令解析與驗證
    2. 權限檢查
    3. 參數處理
    4. 業務邏輯調用
    5. 結果反饋
```

### 🖥️ 用戶界面層

#### `working_gui.py` - 主 GUI 界面
```python
class TelegramBotGUI:
    """圖形化管理界面"""
    
    界面結構：
    ├── 連接設定頁面 (ConnectionTab)
    ├── 廣播控制頁面 (BroadcastTab)  
    ├── 系統管理頁面 (ManagementTab)
    └── 系統狀態頁面 (StatusTab)
    
    核心功能：
    - 即時狀態顯示
    - 可視化操作界面
    - 配置管理
    - 日誌監控
    - 系統控制
```

## 🚀 啟動器系統

### 啟動器分類
```python
# 1. 主要啟動器
start_both.py           # 統一啟動器（推薦）
telegram_bot_standalone.py  # 純後台廣播引擎
working_gui.py          # 純 GUI 界面

# 2. 輔助啟動器  
start_app.py           # 交互式選擇啟動
simple_launcher.py     # 簡化啟動選項
quick_start.py         # 快速啟動腳本
```

### 啟動流程
```python
def startup_sequence():
    """標準啟動序列"""
    
    1. 環境檢查
       - Python 版本驗證
       - 依賴套件檢查
       - 配置文件存在性
    
    2. 配置載入
       - API 配置驗證
       - 廣播配置載入
       - 權限配置初始化
    
    3. 組件初始化
       - Telegram 客戶端連接
       - 廣播引擎初始化
       - 排程器啟動
       - GUI 界面載入 (如適用)
    
    4. 系統就緒
       - 狀態監控啟動
       - 指令處理器註冊
       - 排程循環開始
```

## 📊 數據流向

### 廣播數據流
```
活動內容 (content_databases/)
    ↓
ContentLoader (內容載入)
    ↓  
BroadcastManager (廣播管理)
    ↓
BroadcastSender (批量發送)
    ↓
TelegramClient (Telegram API)
    ↓
目標群組 (廣播接收)
```

### 排程數據流
```
排程配置 (broadcast_config.json)
    ↓
BroadcastScheduler (排程檢查)
    ↓
BroadcastManager (廣播執行)
    ↓
執行記錄 (scheduler_execution_records.json)
    ↓
通知發送 (控制群組)
```

### 指令數據流
```
Telegram 指令
    ↓
CommandHandler (指令解析)
    ↓
PermissionManager (權限驗證)
    ↓
業務邏輯模組 (具體操作)
    ↓
結果反饋 (Telegram 回應)
```

## 🔄 異步處理架構

### 異步任務分類
```python
# 1. 長期運行任務
- 排程循環監控 (scheduler_loop)
- GUI 事件循環 (tkinter mainloop)
- Telegram 事件監聽 (client.run_until_disconnected)

# 2. 週期性任務
- 配置文件重載
- 連接狀態檢查
- 日誌文件輪轉

# 3. 即時響應任務
- 指令處理
- 廣播發送
- GUI 操作響應
```

### 並發控制
```python
# 廣播排他鎖
self.is_broadcasting = False  # 防止重複廣播

# 排程重複執行防護
execution_records = load_execution_records()

# 配置文件併發保護
with file_lock:
    save_config(data)
```

## 🔧 錯誤處理機制

### 多層錯誤處理
```python
# 1. 業務邏輯層錯誤
try:
    result = execute_broadcast(campaign)
except BroadcastError as e:
    log_error(e)
    return error_response(e)

# 2. 網路層錯誤
try:
    await client.send_message(group_id, message)
except NetworkError as e:
    retry_with_backoff(send_message, max_retries=3)

# 3. 系統層錯誤
try:
    load_config_file()
except FileNotFoundError:
    create_default_config()
except PermissionError:
    request_admin_privileges()
```

### 自動恢復機制
```python
# 連接自動重建
async def ensure_connection():
    if not client.is_connected():
        await client.connect()

# 配置自動備份
def save_config_with_backup():
    backup_config()
    save_config()

# 排程狀態恢復
def restore_scheduler_state():
    load_execution_records()
    resume_pending_schedules()
```

## 📈 性能優化策略

### 1. 內存管理
```python
# 日誌文件大小控制
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# 廣播歷史限制
MAX_HISTORY_RECORDS = 1000

# 配置緩存機制
config_cache = {}
cache_expiry = 300  # 5分鐘
```

### 2. 網路優化
```python
# 批量操作
async def send_batch_messages(messages):
    tasks = [send_message(msg) for msg in messages]
    results = await asyncio.gather(*tasks, return_exceptions=True)

# 速率限制
RATE_LIMIT = {
    'messages_per_second': 1,
    'messages_per_minute': 20
}

# 連接池管理
client_pool = TelegramClientPool(max_connections=5)
```

### 3. 存儲優化
```python
# 配置文件壓縮
def save_compressed_config(data):
    compressed = gzip.compress(json.dumps(data).encode())
    with open(config_file, 'wb') as f:
        f.write(compressed)

# 日誌輪轉
from logging.handlers import RotatingFileHandler
handler = RotatingFileHandler(
    'bot.log', maxBytes=10*1024*1024, backupCount=5
)
```

## 🔍 除錯與監控

### 日誌系統
```python
# 多級日誌記錄
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),           # 控制台輸出
        logging.FileHandler('bot.log'),    # 文件記錄
        logging.handlers.SMTPHandler(...)  # 錯誤郵件通知
    ]
)

# 結構化日誌
def log_broadcast_result(campaign, result):
    logger.info("廣播完成", extra={
        'campaign': campaign,
        'success_count': result['success_count'],
        'total_count': result['total_count'],
        'success_rate': result['success_rate']
    })
```

### 狀態監控
```python
# 系統健康檢查
def health_check():
    return {
        'telegram_connected': client.is_connected(),
        'scheduler_running': scheduler.is_running,
        'last_broadcast': get_last_broadcast_time(),
        'error_count': get_recent_error_count(),
        'memory_usage': get_memory_usage()
    }

# 性能指標
def get_performance_metrics():
    return {
        'broadcast_success_rate': calculate_success_rate(),
        'average_send_time': calculate_avg_send_time(),
        'scheduler_accuracy': calculate_scheduler_accuracy(),
        'system_uptime': get_uptime()
    }
```

## 🚀 擴展指南

### 添加新指令
```python
# 1. 在 CommandHandler 中註冊
@client.on(events.NewMessage(pattern='/new_command'))
async def handle_new_command(event):
    # 權限檢查
    if not is_admin(event.sender_id):
        return
    
    # 業務邏輯
    result = execute_new_feature()
    
    # 回應用戶
    await event.respond(f"執行結果: {result}")

# 2. 添加幫助資訊
COMMAND_HELP['new_command'] = "新指令說明"
```

### 添加新廣播類型
```python
# 1. 擴展內容載入器
def load_new_content_type(self, campaign):
    """載入新類型內容"""
    content_path = self.get_content_path(campaign)
    
    # 新格式解析邏輯
    new_content = parse_new_format(content_path)
    
    return new_content

# 2. 擴展發送引擎
async def send_new_content_type(self, group_id, content):
    """發送新類型內容"""
    await self.client.send_file(
        group_id, 
        content,
        attributes=[DocumentAttributeFilename("custom.ext")]
    )
```

### 添加新界面組件
```python
# 1. 創建新標籤頁
class NewFeatureTab:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.setup_widgets()
    
    def setup_widgets(self):
        # 界面組件配置
        pass

# 2. 註冊到主界面
def add_tabs(self):
    # 現有標籤頁
    self.add_existing_tabs()
    
    # 新功能標籤頁
    self.new_feature_tab = NewFeatureTab(self.notebook)
    self.notebook.add(self.new_feature_tab.frame, text="新功能")
```

## 📋 開發規範

### 代碼結構
```python
# 1. 文件組織
module_name.py
├── 導入區域 (標準庫 -> 第三方 -> 本地模組)
├── 常量定義
├── 類別定義 (主類 -> 輔助類)
├── 函數定義 (公共 -> 私有)
└── 主程序入口 (if __name__ == "__main__")

# 2. 類別結構
class ClassName:
    """類別說明文檔"""
    
    def __init__(self):
        """初始化方法"""
        pass
    
    def public_method(self):
        """公共方法"""
        pass
    
    def _private_method(self):
        """私有方法"""
        pass
```

### 命名規範
```python
# 變數和函數: snake_case
user_count = 0
def get_user_list():
    pass

# 類別: PascalCase
class ConfigManager:
    pass

# 常量: UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30

# 文件名: snake_case
telegram_client.py
broadcast_manager.py
```

### 註解規範
```python
def complex_function(param1: str, param2: int = 0) -> Dict[str, Any]:
    """
    複雜函數的詳細說明
    
    Args:
        param1 (str): 參數1說明
        param2 (int, optional): 參數2說明. Defaults to 0.
    
    Returns:
        Dict[str, Any]: 返回值說明
    
    Raises:
        ValueError: 異常情況說明
    
    Example:
        >>> result = complex_function("test", 5)
        >>> print(result)
        {'success': True, 'data': ...}
    """
    pass
```

---

這份架構說明涵蓋了系統的核心設計思想、模組關係、數據流向和擴展機制，為開發者提供全面的技術參考。