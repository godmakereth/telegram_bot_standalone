# 📋 GitHub 上傳前檢查清單

## ✅ 上傳前必須完成的項目

### 🔒 隱私和安全檢查

#### 敏感資料移除
- [ ] ❌ 移除所有 `.session` 檔案
- [ ] ❌ 移除個人 API 憑證（.env, settings.json）
- [ ] ❌ 移除個人群組 ID 和用戶 ID
- [ ] ❌ 移除真實手機號碼
- [ ] ❌ 移除廣播歷史記錄
- [ ] ❌ 移除日誌檔案
- [ ] ❌ 移除備份檔案

#### 範例檔案準備
- [ ] ✅ 建立 `.env.example`
- [ ] ✅ 建立 `data/settings.example.json`
- [ ] ✅ 建立範例內容檔案
- [ ] ✅ 建立 `README.md`
- [ ] ✅ 建立 `.gitignore`

### 📝 文檔完整性檢查

#### 核心文檔
- [ ] ✅ `README.md` - 完整的專案說明
- [ ] ✅ `PROJECT_GUIDE.md` - 詳細專案指南
- [ ] ✅ `LICENSE` - 授權條款
- [ ] ✅ `requirements.txt` - 依賴清單

#### 技術文檔
- [ ] ✅ `docs/ARCHITECTURE.md` - 程式碼架構說明
- [ ] ✅ `docs/USER_GUIDE.md` - 使用者操作指南
- [ ] ✅ `docs/COMMANDS.md` - 指令完整參考

#### 設定文檔
- [ ] ✅ `.gitignore` - Git 忽略規則
- [ ] ✅ 範例配置檔案

### 🔧 程式碼品質檢查

#### 程式碼清理
- [ ] ✅ 移除無用的程式檔案到 tests/ 資料夾
- [ ] ✅ 補充程式碼註解
- [ ] ✅ 修正 import 錯誤
- [ ] ✅ 統一程式碼風格

#### 功能驗證
- [ ] ✅ 確認主要程式能正常啟動
- [ ] ✅ 確認 GUI 界面正常
- [ ] ✅ 確認排程功能正常

## 🚫 絕對不能上傳的檔案

### 個人資料檔案
```
❌ 禁止上傳：
- userbot.session (任何 .session 檔案)
- userbot.session-journal
- .env (包含真實 API 資訊)
- data/settings.json (包含真實設定)
```

### 敏感配置檔案
```
❌ 禁止上傳：
- data/admins.json (真實管理員列表)
- data/broadcast_config.json (真實群組 ID)
- data/broadcast_history.json (真實廣播記錄)
- data/scheduler_execution_records.json (執行記錄)
```

### 日誌和臨時檔案
```
❌ 禁止上傳：
- data/logs/*.log (所有日誌檔案)
- *.backup.* (所有備份檔案)
- __pycache__/ (Python 緩存)
- *.pyc (編譯檔案)
- .DS_Store (macOS 系統檔案)
```

## ✅ 應該上傳的檔案

### 核心程式檔案
```
✅ 必須上傳：
- telegram_bot_standalone.py (主要廣播引擎)
- working_gui.py (GUI 管理界面)
- start_both.py (啟動腳本)
- broadcast_manager.py (廣播管理器)
- telegram_client.py (Telegram 客戶端)
- config.py (配置管理)
- scheduler.py (排程器)
- command_handler.py (指令處理)
- message_manager.py (訊息管理)
- permissions.py (權限管理)
```

### 配置和文檔
```
✅ 必須上傳：
- README.md
- PROJECT_GUIDE.md
- LICENSE
- requirements.txt
- .gitignore
- .env.example
- data/settings.example.json
```

### 目錄結構
```
✅ 必須上傳：
- docs/ (文檔目錄)
- data/content_databases/ (範例內容目錄)
- utils/ (工具模組)
- tests/ (測試和舊檔案)
```

## 🔍 上傳前最終檢查

### 1. 安全檢查指令
```bash
# 檢查是否有敏感檔案
find . -name "*.session*" -o -name ".env" -o -name "*.log"

# 檢查是否有個人資訊
grep -r "api_id.*[0-9]" . --exclude-dir=.git
grep -r "+886" . --exclude-dir=.git
grep -r "-100" . --exclude-dir=.git
```

### 2. Git 狀態檢查
```bash
# 查看將要上傳的檔案
git status

# 查看 .gitignore 是否生效
git check-ignore -v userbot.session
git check-ignore -v .env
```

### 3. 文檔完整性檢查
```bash
# 檢查重要文檔是否存在
ls README.md LICENSE requirements.txt
ls docs/ARCHITECTURE.md docs/USER_GUIDE.md docs/COMMANDS.md
```

## 🚀 GitHub 上傳步驟

### 1. 初始化 Git 倉庫
```bash
git init
git add .gitignore
git commit -m "Add .gitignore"
```

### 2. 添加文件到 Git
```bash
# 添加核心檔案
git add *.py
git add README.md LICENSE requirements.txt
git add docs/
git add data/settings.example.json
git add .env.example

# 檢查暫存區檔案
git status --cached
```

### 3. 提交更改
```bash
git commit -m "Initial commit: RG Telegram Broadcasting System

- Complete broadcasting system with GUI and CLI
- Auto-scheduling functionality  
- Multi-group broadcasting support
- Comprehensive documentation
- Example configuration files"
```

### 4. 連接遠程倉庫
```bash
git remote add origin https://github.com/YOUR_USERNAME/rg-telegram-bot.git
git branch -M main
git push -u origin main
```

## ⚠️ 上傳後注意事項

### 1. 檢查倉庫內容
- 確認沒有敏感資料被上傳
- 檢查 README 在 GitHub 上的顯示效果
- 確認 .gitignore 檔案正常工作

### 2. 設定倉庫
- 添加適當的標籤（tags）
- 設定倉庫描述
- 啟用 Issues 和 Discussions（如需要）

### 3. 更新文檔
- 在 README 中更新正確的 GitHub URL
- 確認所有連結都能正常工作
- 添加 badges（徽章）顯示狀態

## 📞 緊急情況處理

### 如果不小心上傳了敏感資料

#### 1. 立即移除敏感檔案
```bash
git rm --cached userbot.session
git rm --cached .env
git commit -m "Remove sensitive files"
git push origin main
```

#### 2. 清理歷史記錄（如果必要）
```bash
# 警告：這會重寫 Git 歷史
git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch userbot.session' \
--prune-empty --tag-name-filter cat -- --all

git push origin --force --all
```

#### 3. 更新 API 憑證
- 撤銷已暴露的 API 金鑰
- 生成新的 API 憑證
- 通知相關用戶更改密碼

---

**最後提醒：上傳前請仔細檢查每一個項目，確保沒有個人或敏感資料被包含在內！**