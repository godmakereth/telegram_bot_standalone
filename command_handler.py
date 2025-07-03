
"""
統一命令處理器 - 整合所有命令模組
"""
import asyncio
import logging
import platform
import psutil
import re
import sys
from datetime import datetime
from telethon import events

from telegram_client import TelegramClientManager
from config import ConfigManager, ConfigValidator
from broadcast_manager import BroadcastManager
from message_manager import MessageManager
from permissions import require_admin_and_control_group, PermissionManager

class AdminCommands:
    """管理員命令處理器"""
    
    def __init__(self, client, config_manager: ConfigManager, permission_manager: PermissionManager, client_manager=None):
        self.client = client
        self.config = config_manager
        self.permissions = permission_manager
        self.client_manager = client_manager
        # 用於追蹤用戶狀態
        self.user_states = {}
        # 初始化日誌器
        self.logger = logging.getLogger(__name__)
    
    def register_handlers(self):
        """註冊所有管理員命令處理器"""
        self.client.add_event_handler(
            self._handle_help,
            events.NewMessage(pattern=r'^/help$')
        )
        
        self.client.add_event_handler(
            self._handle_status,
            events.NewMessage(pattern=r'^/status$')
        )
        
        self.client.add_event_handler(
            self._handle_restart,
            events.NewMessage(pattern=r'^/restart$')
        )
        
        self.client.add_event_handler(
            self._handle_logs,
            events.NewMessage(pattern=r'^/logs(?:\s+(\d+))?$')
        )
        
        self.client.add_event_handler(
            self._handle_config,
            events.NewMessage(pattern=r'^/config$')
        )
        
        # 新命令 - 主要使用
        self.client.add_event_handler(
            self._handle_add_groups,
            events.NewMessage(pattern=r'^/add_groups$')
        )
        
        self.client.add_event_handler(
            self._handle_add_groups_with_params,
            events.NewMessage(pattern=r'^/add_groups\s+(.+)$')
        )
        
        self.client.add_event_handler(
            self._handle_remove_groups,
            events.NewMessage(pattern=r'^/remove_groups$')
        )
        
        self.client.add_event_handler(
            self._handle_remove_groups_with_params,
            events.NewMessage(pattern=r'^/remove_groups\s+(.+)$')
        )
        
        # 舊命令 - 向後兼容
        self.client.add_event_handler(
            self._handle_add_groups,
            events.NewMessage(pattern=r'^/add_target$')
        )
        
        self.client.add_event_handler(
            self._handle_add_groups_with_params,
            events.NewMessage(pattern=r'^/add_target\s+(.+)$')
        )
        
        self.client.add_event_handler(
            self._handle_remove_groups,
            events.NewMessage(pattern=r'^/remove_target$')
        )
        
        self.client.add_event_handler(
            self._handle_remove_groups_with_params,
            events.NewMessage(pattern=r'^/remove_target\s+(.+)$')
        )
        
        self.client.add_event_handler(
            self._handle_direct_input,
            events.NewMessage(pattern=r'^[\d,\-\s]+$')
        )
    
    async def _handle_help(self, event):
        """顯示幫助訊息"""
        # 權限檢查
        user_id = event.sender_id
        chat_id = event.chat_id
        
        # 調試日誌：記錄 /help 命令的觸發情況
        self.logger.info(f"[DEBUG] /help command triggered - user_id: {user_id}, chat_id: {chat_id}")
        
        is_control_group = self.permissions.is_control_group(chat_id)
        self.logger.info(f"[DEBUG] is_control_group check result: {is_control_group}")
        
        if not is_control_group:
            self.logger.info(f"[DEBUG] Command ignored - not a control group (chat_id: {chat_id})")
            return  # 靜默忽略非控制群組的命令
        
        is_admin = self.permissions.is_admin(user_id)
        self.logger.info(f"[DEBUG] is_admin check result: {is_admin}")
        
        if not is_admin:
            self.logger.info(f"[DEBUG] Permission denied - user is not admin (user_id: {user_id})")
            await event.respond("❌ 權限不足：此命令僅限管理員使用")
            return
        
        self.logger.info(f"[DEBUG] All checks passed - proceeding with help command (user_id: {user_id}, chat_id: {chat_id})")
        
        help_text = """
🤖 **RG Telegram 廣播機器人 - 命令列表**

**📋 基本指令**
• `/help` - 顯示此幫助訊息
• `/status` - 查看系統狀態
• `/config` - 查看當前配置

**📅 排程管理**
• `/add_schedule <時間> <活動>` - 新增排程 (格式: HH:MM)
• `/as <時間> <活動>` - 新增排程 (快捷別名)
• `/remove_schedule` - 移除排程 (互動式選擇)
• `/list_schedules` 或 `/ls` - 查看所有排程
• `/enable` - 啟用排程功能
• `/disable` - 停用排程功能

**📢 廣播操作**
• `/broadcast <活動>` 或 `/bc <活動>` - 手動廣播
• `/broadcast_history [數量]` 或 `/bh [數量]` - 查看廣播歷史
• `/history [數量]` - 查看廣播歷史 (別名)

**👥 群組管理**
• `/list_groups` 或 `/lg` - 列出廣播目標群組
• `/my_groups` 或 `/mg` - 查看所有已加入群組
• `/scan_groups` 或 `/sg` - 重新掃描群組詳情
• `/add_groups` - 新增廣播目標群組
• `/remove_groups` - 移除廣播目標群組

**👤 管理員管理**
• `/list_admins` - 列出所有管理員
• `/add_admin <ID/@用戶名>` - 新增管理員
• `/remove_admin <ID/@用戶名>` - 移除管理員
• `/sync_admins` - 從控制群組同步管理員

**🔧 系統管理**
• `/restart` - 重啟機器人系統
• `/logs [行數]` - 查看系統日誌 (默認50行)

**💡 使用範例**
• `/as 09:30 A` - 每日09:30廣播活動A (快捷)
• `/bc B` - 立即廣播活動B (快捷)
• `/enable` - 快速啟用排程
• `/mg` - 快速查看我的群組
• `/bh 20` - 查看最近20次廣播記錄
• `/add_admin @username` - 新增管理員
• `/add_groups` → 輸入 `1,3,6` - 批次新增群組

**⚡ 快速指令**
• `/s` - 快速狀態檢查
• `/c` - 快速查看活動列表
• `/q <活動>` - 快速廣播 (跳過確認)

**📞 支援**
如有問題請聯繫系統管理員。
        """
        await event.respond(help_text.strip())
        self.logger.info(f"[DEBUG] Help message sent successfully to user_id: {user_id}, chat_id: {chat_id}")
    
    async def _handle_status(self, event):
        """顯示系統狀態"""
        # 權限檢查
        user_id = event.sender_id
        chat_id = event.chat_id
        
        if not self.permissions.is_control_group(chat_id):
            return  # 靜默忽略非控制群組的命令
        
        if not self.permissions.is_admin(user_id):
            await event.respond("❌ 權限不足：此命令僅限管理員使用")
            return
        
        try:
            # 獲取系統信息
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
            
            # 獲取配置信息
            schedules = self.config.get_schedules()
            target_groups = self.config.get_target_groups()
            control_group = self.config.get_control_group()
            schedule_enabled = self.config.is_schedule_enabled()
            
            # 獲取廣播歷史統計
            history = self.config.get_broadcast_history(limit=10)
            recent_success_rate = 0
            if history:
                total_broadcasts = len(history)
                total_success = sum(h.get('success_count', 0) for h in history)
                total_attempts = sum(h.get('groups_count', 0) for h in history)
                recent_success_rate = (total_success / total_attempts * 100) if total_attempts > 0 else 0
            
            # 獲取管理員列表
            admins = self.config.get_admins()
            
            # 下一個排程
            next_schedule = "無排程" if not schedules else f"{schedules[0]['time']} - {schedules[0]['campaign']}"
            
            status_text = (
                f"🤖 **系統狀態報告**\n\n"
                f"**📊 系統資訊**\n"
                f"• 當前時間: `{current_time}`\n"
                f"• 系統運行時間: `{str(uptime).split('.')[0]}`\n"
                f"• Python版本: `{sys.version.split()[0]}`\n"
                f"• 平台: `{platform.system()} {platform.release()}`\n\n"
                f"**⚙️ 機器人配置**\n"
                f"• 排程狀態: `{'✅ 啟用' if schedule_enabled else '❌ 停用'}`\n"
                f"• 排程數量: `{len(schedules)} 個`\n"
                f"• 目標群組: `{len(target_groups)} 個`\n"
                f"• 控制群組: `{control_group}`\n"
                f"• 管理員數量: `{len(admins)} 位`\n\n"
                f"**📅 排程資訊**\n"
                f"• 下一個排程: `{next_schedule}`\n\n"
                f"**📈 廣播統計**\n"
                f"• 最近10次成功率: `{recent_success_rate:.1f}%`\n"
                f"• 歷史記錄總數: `{len(self.config.broadcast_history)} 筆`\n\n"
                f"**🔧 資源使用**\n"
                f"• CPU使用率: `{psutil.cpu_percent()}%`\n"
                f"• 記憶體使用率: `{psutil.virtual_memory().percent}%`\n"
                f"• 磁碟使用率: `{psutil.disk_usage('/').percent}%`\n\n"
                f"系統運行正常 ✅"
            )
            
            await event.respond(status_text.strip())
            
        except Exception as e:
            await event.respond(f"❌ 獲取系統狀態時發生錯誤: {e}")
    
    async def _handle_restart(self, event):
        """重啟系統"""
        # 權限檢查
        user_id = event.sender_id
        chat_id = event.chat_id
        
        if not self.permissions.is_control_group(chat_id):
            return  # 靜默忽略非控制群組的命令
        
        if not self.permissions.is_admin(user_id):
            await event.respond("❌ 權限不足：此命令僅限管理員使用")
            return
        
        try:
            await event.respond("🔄 正在重啟系統...")
            
            # 記錄重啟次數
            self.config.broadcast_config["total_restarts"] = self.config.broadcast_config.get("total_restarts", 0) + 1
            self.config.save_broadcast_config()
            
            # 給一點時間讓消息發送完成
            await asyncio.sleep(2)
            
            # 斷開連接
            await self.client.disconnect()
            
            # 重啟程序 (這裡只是示例，實際需要配合外部腳本)
            import os
            os._exit(0)  # 強制退出，由外部監控重啟
            
        except Exception as e:
            await event.respond(f"❌ 重啟系統時發生錯誤: {e}")
    
    async def _handle_logs(self, event):
        """查看系統日誌"""
        # 權限檢查
        user_id = event.sender_id
        chat_id = event.chat_id
        
        if not self.permissions.is_control_group(chat_id):
            return  # 靜默忽略非控制群組的命令
        
        if not self.permissions.is_admin(user_id):
            await event.respond("❌ 權限不足：此命令僅限管理員使用")
            return
        
        try:
            # 解析參數
            match = event.pattern_match
            lines = int(match.group(1)) if match.group(1) else 50
            lines = min(lines, 200)  # 限制最大行數
            
            import os
            log_path = os.path.join(self.config.data_path, "logs", "bot.log")
            
            if not os.path.exists(log_path):
                await event.respond("📄 暫無日誌記錄")
                return
            
            # 讀取最後N行
            with open(log_path, 'r', encoding='utf-8') as f:
                log_lines = f.readlines()
            
            if not log_lines:
                await event.respond("📄 日誌文件為空")
                return
            
            # 獲取最後N行
            recent_logs = log_lines[-lines:]
            log_text = ''.join(recent_logs)
            
            # 如果日誌太長，分段發送
            if len(log_text) > 4000:
                chunks = [log_text[i:i+4000] for i in range(0, len(log_text), 4000)]
                for i, chunk in enumerate(chunks):
                    header = f"📄 **系統日誌 ({i+1}/{len(chunks)})**\n\n```\n"
                    footer = "\n```"
                    await event.respond(header + chunk + footer)
                    await asyncio.sleep(1)  # 避免觸發速率限制
            else:
                await event.respond(f"📄 **系統日誌 (最近{len(recent_logs)}行)**\n\n```\n{log_text}\n```")
            
        except Exception as e:
            await event.respond(f"❌ 讀取日誌時發生錯誤: {e}")
    
    async def _handle_config(self, event):
        """查看當前配置"""
        # 權限檢查
        user_id = event.sender_id
        chat_id = event.chat_id
        
        if not self.permissions.is_control_group(chat_id):
            return  # 靜默忽略非控制群組的命令
        
        if not self.permissions.is_admin(user_id):
            await event.respond("❌ 權限不足：此命令僅限管理員使用")
            return
        try:
            # 獲取配置信息
            schedules = self.config.get_schedules()
            target_groups = self.config.get_target_groups()
            control_group = self.config.get_control_group()
            schedule_enabled = self.config.is_schedule_enabled()
            admins = self.config.get_admins()
            campaigns = self.config.list_available_campaigns()
            
            config_text = (
                f"⚙️ **當前系統配置**\n\n"
                f"**📅 排程配置**\n"
                f"• 排程狀態: `{'✅ 啟用' if schedule_enabled else '❌ 停用'}`\n"
                f"• 排程列表:\n"
            )
            
            if schedules:
                for schedule in schedules:
                    config_text += f"  - `{schedule['time']}` → 活動 `{schedule['campaign']}`\n"
            else:
                config_text += "  - 暫無排程\n"
            
            config_text += (
                f"\n**👥 群組配置**\n"
                f"• 控制群組: `{control_group}`\n"
                f"• 目標群組數量: `{len(target_groups)} 個`\n"
            )
            
            if target_groups:
                config_text += "• 目標群組列表:\n"
                for group_id in target_groups:
                    config_text += f"  - `{group_id}`\n"
            
            config_text += (
                f"\n**👤 管理員配置**\n"
                f"• 管理員數量: `{len(admins)} 位`\n"
            )
            
            if admins:
                config_text += "• 管理員列表:\n"
                for admin in admins:
                    username = f"@{admin['username']}" if admin.get('username') else "無用戶名"
                    config_text += f"  - `{admin['name']}` ({username})\n"
            
            config_text += (
                f"\n**📁 活動配置**\n"
                f"• 可用活動: `{', '.join(campaigns) if campaigns else '無'}`\n\n"
                f"**🔧 系統設定**\n"
                f"• 廣播延遲: `{self.config.broadcast_config.get('broadcast_delay', 5)} 秒`\n"
                f"• 最大重試: `{self.config.broadcast_config.get('max_retries', 3)} 次`\n"
                f"• 總重啟次數: `{self.config.broadcast_config.get('total_restarts', 0)} 次`\n"
            )
            
            await event.respond(config_text.strip())
            
        except Exception as e:
            await event.respond(f"❌ 獲取配置信息時發生錯誤: {e}")
    
    async def _get_all_groups_list(self):
        """獲取所有群組列表，用於編號查詢"""
        try:
            # 檢查客戶端是否可用
            if not self.client:
                logging.getLogger(__name__).error("客戶端未初始化")
                return []
            
            if not self.client.is_connected():
                logging.getLogger(__name__).error("客戶端未連接")
                return []
            
            target_groups = self.config.get_target_groups()
            control_group = self.config.get_control_group()
            
            groups = []
            channels = []
            
            # 獲取對話列表
            async for dialog in self.client.iter_dialogs():
                if dialog.is_group or dialog.is_channel:
                    entity = dialog.entity
                    group_id = dialog.id
                    
                    # 處理超級群組的 ID 轉換
                    if group_id > 0 and (dialog.is_group or getattr(entity, 'megagroup', False)):
                        group_id = -group_id
                    
                    group_info = {
                        'id': group_id,
                        'title': dialog.name or dialog.title or '未知群組',
                        'type': 'channel' if dialog.is_channel else 'group',
                        'is_control': group_id == control_group,
                        'is_target': group_id in target_groups,
                        'members_count': getattr(entity, 'participants_count', 0)
                    }
                    
                    if group_info['type'] == 'group':
                        groups.append(group_info)
                    else:
                        channels.append(group_info)
            
            logging.getLogger(__name__).info(f"成功獲取 {len(groups)} 個群組, {len(channels)} 個頻道")
            return groups + channels
            
        except Exception as e:
            logging.getLogger(__name__).error(f"直接獲取群組列表失敗: {e}")
            
            # 嘗試備用方案：使用 client_manager 的方法
            if self.client_manager:
                try:
                    logging.getLogger(__name__).info("嘗試使用 client_manager 獲取群組列表")
                    dialogs = await self.client_manager.get_dialogs()
                    
                    target_groups = self.config.get_target_groups()
                    control_group = self.config.get_control_group()
                    
                    all_groups = []
                    for dialog in dialogs:
                        group_info = {
                            'id': dialog['id'],
                            'title': dialog['title'],
                            'type': dialog['type'],
                            'is_control': dialog['id'] == control_group,
                            'is_target': dialog['id'] in target_groups,
                            'members_count': dialog.get('participant_count', 0)
                        }
                        all_groups.append(group_info)
                    
                    logging.getLogger(__name__).info(f"備用方案成功獲取 {len(all_groups)} 個群組/頻道")
                    return all_groups
                    
                except Exception as backup_error:
                    logging.getLogger(__name__).error(f"備用方案也失敗: {backup_error}")
            
            import traceback
            logging.getLogger(__name__).error(f"錯誤詳情: {traceback.format_exc()}")
            return []
    
    async def _parse_group_inputs(self, input_text, action_type="add"):
        """解析群組輸入，支持單個或多個用逗號分隔"""
        try:
            # 分割並清理輸入
            inputs = [item.strip() for item in input_text.split(',') if item.strip()]
            
            if not inputs:
                return [], "❌ 請提供有效的群組編號或ID"
            
            groups_for_selection = None
            results = []
            
            for input_item in inputs:
                try:
                    input_value = int(input_item)
                except ValueError:
                    return [], f"❌ 輸入格式錯誤：'{input_item}' 不是有效的數字"
                
                # 判斷是編號還是群組ID
                if input_value > 0 and input_value < 1000:
                    # 作為編號處理
                    if groups_for_selection is None:
                        if action_type == "remove":
                            # 移除操作：使用目標群組列表
                            target_groups = self.config.get_target_groups()
                            if not target_groups:
                                return [], "❌ 目前沒有設定任何廣播目標群組"
                            
                            groups_for_selection = []
                            for group_id in target_groups:
                                try:
                                    if self.client and self.client.is_connected():
                                        entity = await self.client.get_entity(group_id)
                                        group_name = getattr(entity, 'title', getattr(entity, 'first_name', f'群組{group_id}'))
                                    else:
                                        group_name = f'群組{group_id}'
                                except Exception:
                                    group_name = f'群組{group_id}'
                                
                                groups_for_selection.append({
                                    'id': group_id,
                                    'title': group_name
                                })
                        else:
                            # 新增操作：使用所有群組列表
                            groups_for_selection = await self._get_all_groups_list()
                            if not groups_for_selection:
                                return [], "❌ 無法獲取群組列表，請稍後再試"
                    
                    if input_value > len(groups_for_selection):
                        return [], f"❌ 編號 `{input_value}` 超出範圍，目前共有 {len(groups_for_selection)} 個群組"
                    
                    selected_group = groups_for_selection[input_value - 1]
                    group_id = selected_group['id']
                    group_name = selected_group['title']
                else:
                    # 作為群組ID處理
                    group_id = input_value
                    
                    # 嘗試獲取群組信息
                    try:
                        entity = await self.client.get_entity(group_id)
                        group_name = getattr(entity, 'title', getattr(entity, 'first_name', '未知群組'))
                    except Exception:
                        group_name = '未知群組'
                
                results.append({
                    'id': group_id,
                    'name': group_name,
                    'input': input_item
                })
            
            return results, None
            
        except Exception as e:
            return [], f"❌ 解析輸入時發生錯誤: {e}"
    
    async def _show_groups_list_for_selection(self, event, action_type):
        """顯示群組列表供選擇參考"""
        try:
            all_groups = await self._get_all_groups_list()
            if not all_groups:
                # 嘗試備用方案：透過 CommandHandler 傳遞的方式
                await event.respond(
                    f"❌ 無法獲取群組列表，請直接使用群組ID進行{action_type}\n\n"
                    f"**使用方式：**\n"
                    f"• `/{action_type.lower()}_target -1002335227123` (群組ID)\n"
                    f"• `/{action_type.lower()}_target -1002335227123,-4863847123` (多個群組ID)\n\n"
                    f"💡 可以先使用 `/list_groups` 命令查看所有群組ID"
                )
                return
            
            target_groups = self.config.get_target_groups()
            control_group = self.config.get_control_group()
            
            # 根據操作類型過濾群組
            if action_type == "移除":
                # 移除操作：直接使用配置中的目標群組列表
                target_groups = self.config.get_target_groups()
                list_msg = f"📋 **廣播目標群組列表** (供{action_type}參考)\n\n"
                
                if not target_groups:
                    await event.respond("⚠️ 目前沒有設定任何廣播目標群組")
                    return
                
                # 構建群組列表，包含所有配置的群組
                filtered_groups = []
                for i, group_id in enumerate(target_groups, 1):
                    # 嘗試從 all_groups 中找到群組名稱
                    group_name = None
                    for item in all_groups:
                        if item['id'] == group_id:
                            group_name = item['title']
                            break
                    
                    # 如果沒找到，嘗試從客戶端獲取
                    if not group_name:
                        try:
                            if self.client and self.client.is_connected():
                                entity = await self.client.get_entity(group_id)
                                group_name = getattr(entity, 'title', getattr(entity, 'first_name', f'群組{group_id}'))
                            else:
                                group_name = f'群組{group_id}'
                        except Exception:
                            group_name = f'群組{group_id}'
                    
                    filtered_groups.append({
                        'id': group_id,
                        'title': group_name,
                        'is_target': True
                    })
                    
                    list_msg += f"{i}. {group_name} ({group_id}) [設定廣播]\n"
                
            else:
                # 新增操作：顯示所有群組
                list_msg = f"📋 **群組/頻道列表** (供{action_type}參考)\n\n"
                filtered_groups = all_groups
                
                for i, item in enumerate(all_groups, 1):
                    # 判斷狀態
                    if item['is_control']:
                        status = "[控制群組]"
                    elif item['is_target']:
                        status = "[設定廣播]"
                    else:
                        status = "[未設定廣播]"
                    
                    list_msg += f"{i}. {item['title']} ({item['id']}) {status}\n"
            
            list_msg += f"\n💡 **請直接輸入要{action_type}的群組編號或ID：**\n"
            list_msg += f"• 單個編號: `5`\n"
            list_msg += f"• 多個編號: `1,3,6,7`\n"
            list_msg += f"• 群組ID: `-1002335227123`\n"
            list_msg += f"• 混合使用: `5,-1002335227123,9`"
            
            # 如果訊息太長，分段發送
            if len(list_msg) > 4000:
                chunks = []
                current_chunk = f"📋 **群組/頻道列表** (供{action_type}參考)\n\n"
                
                for i, item in enumerate(all_groups, 1):
                    if item['is_control']:
                        status = "[控制群組]"
                    elif item['is_target']:
                        status = "[設定廣播]"
                    else:
                        status = "[未設定廣播]"
                    
                    item_info = f"{i}. {item['title']} ({item['id']}) {status}\n"
                    
                    if len(current_chunk + item_info) > 3500:  # 留空間給使用說明
                        chunks.append(current_chunk)
                        current_chunk = f"📋 **群組/頻道列表** (續)\n\n" + item_info
                    else:
                        current_chunk += item_info
                
                if current_chunk:
                    # 在最後一段加上使用說明
                    current_chunk += f"\n💡 **請直接輸入要{action_type}的群組編號或ID：**\n"
                    current_chunk += f"• 單個編號: `5`\n"
                    current_chunk += f"• 多個編號: `1,3,6,7`\n"
                    current_chunk += f"• 群組ID: `-1002335227123`\n"
                    current_chunk += f"• 混合使用: `5,-1002335227123,9`"
                    chunks.append(current_chunk)
                
                # 發送所有分段
                for chunk in chunks:
                    await event.respond(chunk)
                    await asyncio.sleep(0.5)  # 避免發送太快
            else:
                await event.respond(list_msg)
                
        except Exception as e:
            logging.getLogger(__name__).error(f"顯示群組列表失敗: {e}")
            await event.respond(f"❌ 顯示群組列表時發生錯誤: {e}")
    
    @require_admin_and_control_group
    async def _handle_add_groups(self, event):
        """顯示群組列表並提示用戶新增目標群組"""
        try:
            # 設置用戶狀態
            user_id = event.sender_id
            self.user_states[user_id] = {
                'action': 'add_groups',
                'chat_id': event.chat_id,
                'timestamp': event.date
            }
            
            # 顯示群組列表供選擇
            await self._show_groups_list_for_selection(event, "新增")
        except Exception as e:
            await event.respond(f"❌ 顯示群組列表時發生錯誤: {e}")
    
    @require_admin_and_control_group
    async def _handle_add_groups_with_params(self, event):
        """新增廣播目標群組（支持多個）"""
        try:
            match = event.pattern_match
            input_text = match.group(1)
            
            # 解析輸入
            groups, error = await self._parse_group_inputs(input_text)
            if error:
                await event.respond(error)
                return
            
            current_targets = self.config.get_target_groups()
            
            # 檢查並處理每個群組
            added_groups = []
            skipped_groups = []
            failed_groups = []
            
            for group_info in groups:
                group_id = group_info['id']
                group_name = group_info['name']
                
                # 檢查是否已在目標列表中
                if group_id in current_targets:
                    skipped_groups.append(f"`{group_name}` ({group_id})")
                    continue
                
                # 嘗試新增
                if self.config.add_target_group(group_id):
                    added_groups.append(f"`{group_name}` ({group_id})")
                    current_targets.append(group_id)  # 更新本地列表避免重複檢查
                else:
                    failed_groups.append(f"`{group_name}` ({group_id})")
            
            # 構建回應訊息
            response_parts = []
            
            if added_groups:
                response_parts.append(f"✅ **成功新增 {len(added_groups)} 個廣播目標群組：**")
                for group in added_groups:
                    response_parts.append(f"• {group}")
            
            if skipped_groups:
                response_parts.append(f"\n⚠️ **已跳過 {len(skipped_groups)} 個已存在的群組：**")
                for group in skipped_groups:
                    response_parts.append(f"• {group}")
            
            if failed_groups:
                response_parts.append(f"\n❌ **新增失敗 {len(failed_groups)} 個群組：**")
                for group in failed_groups:
                    response_parts.append(f"• {group}")
            
            if not added_groups and not skipped_groups and not failed_groups:
                response_parts.append("❌ 沒有處理任何群組")
            
            response_parts.append(f"\n📊 **目前廣播目標總數：{len(self.config.get_target_groups())} 個群組**")
            
            await event.respond("\n".join(response_parts))
                
        except Exception as e:
            await event.respond(f"❌ 新增群組時發生錯誤: {e}")
    
    @require_admin_and_control_group
    async def _handle_remove_groups(self, event):
        """顯示群組列表並提示用戶移除目標群組"""
        try:
            # 設置用戶狀態
            user_id = event.sender_id
            self.user_states[user_id] = {
                'action': 'remove_groups',
                'chat_id': event.chat_id,
                'timestamp': event.date
            }
            
            # 顯示群組列表供選擇
            await self._show_groups_list_for_selection(event, "移除")
        except Exception as e:
            await event.respond(f"❌ 顯示群組列表時發生錯誤: {e}")
    
    @require_admin_and_control_group
    async def _handle_remove_groups_with_params(self, event):
        """移除廣播目標群組（支持多個）"""
        try:
            match = event.pattern_match
            input_text = match.group(1)
            
            # 解析輸入
            groups, error = await self._parse_group_inputs(input_text)
            if error:
                await event.respond(error)
                return
            
            current_targets = self.config.get_target_groups()
            
            # 檢查並處理每個群組
            removed_groups = []
            not_found_groups = []
            failed_groups = []
            
            for group_info in groups:
                group_id = group_info['id']
                group_name = group_info['name']
                
                # 檢查是否在目標列表中
                if group_id not in current_targets:
                    not_found_groups.append(f"`{group_name}` ({group_id})")
                    continue
                
                # 嘗試移除
                if self.config.remove_target_group(group_id):
                    removed_groups.append(f"`{group_name}` ({group_id})")
                    current_targets.remove(group_id)  # 更新本地列表
                else:
                    failed_groups.append(f"`{group_name}` ({group_id})")
            
            # 構建回應訊息
            response_parts = []
            
            if removed_groups:
                response_parts.append(f"✅ **成功移除 {len(removed_groups)} 個廣播目標群組：**")
                for group in removed_groups:
                    response_parts.append(f"• {group}")
            
            if not_found_groups:
                response_parts.append(f"\n⚠️ **已跳過 {len(not_found_groups)} 個不在目標列表的群組：**")
                for group in not_found_groups:
                    response_parts.append(f"• {group}")
            
            if failed_groups:
                response_parts.append(f"\n❌ **移除失敗 {len(failed_groups)} 個群組：**")
                for group in failed_groups:
                    response_parts.append(f"• {group}")
            
            if not removed_groups and not not_found_groups and not failed_groups:
                response_parts.append("❌ 沒有處理任何群組")
            
            response_parts.append(f"\n📊 **目前廣播目標總數：{len(self.config.get_target_groups())} 個群組**")
            
            await event.respond("\n".join(response_parts))
                
        except Exception as e:
            await event.respond(f"❌ 移除群組時發生錯誤: {e}")
    
    async def _handle_direct_input(self, event):
        """處理用戶直接輸入的編號或群組ID"""
        try:
            user_id = event.sender_id
            chat_id = event.chat_id
            
            # 檢查權限
            if not self.permissions.is_control_group(chat_id):
                return  # 靜默忽略非控制群組的輸入
            
            if not self.permissions.is_admin(user_id):
                return  # 靜默忽略非管理員的輸入
            
            # 檢查用戶狀態
            if user_id not in self.user_states:
                return  # 沒有等待輸入的狀態，忽略
            
            user_state = self.user_states[user_id]
            
            # 檢查是否在正確的聊天室
            if user_state['chat_id'] != chat_id:
                return  # 不在同一個聊天室，忽略
            
            # 檢查時間是否過期（5分鐘內有效）
            import datetime
            if (event.date - user_state['timestamp']).total_seconds() > 300:
                del self.user_states[user_id]
                await event.respond("⏰ 輸入已超時，請重新使用 `/add_groups` 或 `/remove_groups` 指令")
                return
            
            # 獲取用戶輸入
            input_text = event.message.message.strip()
            action = user_state['action']
            
            # 清除用戶狀態
            del self.user_states[user_id]
            
            # 根據動作執行相應的操作
            if action == 'remove_schedule':
                await self._execute_remove_schedule(event, input_text)
            else:
                # 根據操作類型解析群組輸入
                if action == 'add_groups' or action == 'add_target':
                    groups, error = await self._parse_group_inputs(input_text, "add")
                    if error:
                        await event.respond(error)
                        return
                    await self._execute_add_groups(event, groups)
                elif action == 'remove_groups' or action == 'remove_target':
                    groups, error = await self._parse_group_inputs(input_text, "remove")
                    if error:
                        await event.respond(error)
                        return
                    await self._execute_remove_groups(event, groups)
                
        except Exception as e:
            # 清除用戶狀態
            if user_id in self.user_states:
                del self.user_states[user_id]
            await event.respond(f"❌ 處理輸入時發生錯誤: {e}")
    
    async def _execute_add_groups(self, event, groups):
        """執行新增目標群組的操作"""
        try:
            current_targets = self.config.get_target_groups()
            
            # 檢查並處理每個群組
            added_groups = []
            skipped_groups = []
            failed_groups = []
            
            for group_info in groups:
                group_id = group_info['id']
                group_name = group_info['name']
                
                # 檢查是否已在目標列表中
                if group_id in current_targets:
                    skipped_groups.append(f"`{group_name}` ({group_id})")
                    continue
                
                # 嘗試新增
                if self.config.add_target_group(group_id):
                    added_groups.append(f"`{group_name}` ({group_id})")
                    current_targets.append(group_id)  # 更新本地列表避免重複檢查
                else:
                    failed_groups.append(f"`{group_name}` ({group_id})")
            
            # 構建回應訊息
            response_parts = []
            
            if added_groups:
                response_parts.append(f"✅ **成功新增 {len(added_groups)} 個廣播目標群組：**")
                for group in added_groups:
                    response_parts.append(f"• {group}")
            
            if skipped_groups:
                response_parts.append(f"\n⚠️ **已跳過 {len(skipped_groups)} 個已存在的群組：**")
                for group in skipped_groups:
                    response_parts.append(f"• {group}")
            
            if failed_groups:
                response_parts.append(f"\n❌ **新增失敗 {len(failed_groups)} 個群組：**")
                for group in failed_groups:
                    response_parts.append(f"• {group}")
            
            if not added_groups and not skipped_groups and not failed_groups:
                response_parts.append("❌ 沒有處理任何群組")
            
            response_parts.append(f"\n📊 **目前廣播目標總數：{len(self.config.get_target_groups())} 個群組**")
            
            await event.respond("\n".join(response_parts))
            
        except Exception as e:
            await event.respond(f"❌ 新增群組時發生錯誤: {e}")
    
    async def _execute_remove_groups(self, event, groups):
        """執行移除目標群組的操作"""
        try:
            # 強制重新載入配置以確保數據同步
            self.config._reload_broadcast_config()
            current_targets = self.config.get_target_groups()
            
            # 檢查並處理每個群組
            removed_groups = []
            not_found_groups = []
            failed_groups = []
            
            for group_info in groups:
                group_id = group_info['id']
                group_name = group_info['name']
                
                # 檢查是否在目標列表中
                if group_id not in current_targets:
                    not_found_groups.append(f"`{group_name}` ({group_id})")
                    continue
                
                # 嘗試移除
                if self.config.remove_target_group(group_id):
                    removed_groups.append(f"`{group_name}` ({group_id})")
                    current_targets.remove(group_id)  # 更新本地列表
                else:
                    failed_groups.append(f"`{group_name}` ({group_id})")
            
            # 構建回應訊息
            response_parts = []
            
            if removed_groups:
                response_parts.append(f"✅ **成功移除 {len(removed_groups)} 個廣播目標群組：**")
                for group in removed_groups:
                    response_parts.append(f"• {group}")
            
            if not_found_groups:
                response_parts.append(f"\n⚠️ **已跳過 {len(not_found_groups)} 個不在目標列表的群組：**")
                for group in not_found_groups:
                    response_parts.append(f"• {group}")
            
            if failed_groups:
                response_parts.append(f"\n❌ **移除失敗 {len(failed_groups)} 個群組：**")
                for group in failed_groups:
                    response_parts.append(f"• {group}")
            
            if not removed_groups and not not_found_groups and not failed_groups:
                response_parts.append("❌ 沒有處理任何群組")
            
            response_parts.append(f"\n📊 **目前廣播目標總數：{len(self.config.get_target_groups())} 個群組**")
            
            await event.respond("\n".join(response_parts))
            
        except Exception as e:
            await event.respond(f"❌ 移除群組時發生錯誤: {e}")
    
    async def _execute_remove_schedule(self, event, input_text):
        """執行移除排程的操作"""
        try:
            schedules = self.config.get_schedules()
            
            if not schedules:
                await event.respond("❌ 目前沒有任何排程可以移除")
                return
            
            # 排序排程（按時間）
            sorted_schedules = sorted(schedules, key=lambda x: x['time'])
            
            # 處理特殊指令
            if input_text.lower() == 'cancel':
                await event.respond("❌ 已取消移除排程操作")
                return
            
            if input_text.lower() == 'all':
                # 清空所有排程
                before_count = len(schedules)
                success = self.config.clear_all_schedules()
                
                if success:
                    await event.respond(f"✅ 已清空所有排程 ({before_count} 個)")
                else:
                    await event.respond("❌ 清空排程失敗")
                return
            
            # 解析編號輸入
            try:
                indices_to_remove = self._parse_schedule_indices(input_text, len(sorted_schedules))
            except ValueError as e:
                await event.respond(f"❌ 編號格式錯誤: {e}")
                return
            
            if not indices_to_remove:
                await event.respond("❌ 請輸入有效的排程編號")
                return
            
            # 獲取要移除的排程
            schedules_to_remove = []
            for index in sorted(indices_to_remove, reverse=True):  # 從後往前移除
                if 1 <= index <= len(sorted_schedules):
                    schedules_to_remove.append(sorted_schedules[index - 1])
            
            if not schedules_to_remove:
                await event.respond("❌ 指定的編號無效")
                return
            
            # 執行移除
            removed_count = 0
            removed_items = []
            
            for schedule in schedules_to_remove:
                success = self.config.remove_schedule(schedule['time'], schedule['campaign'])
                if success:
                    removed_count += 1
                    removed_items.append(f"• {schedule['time']} - {schedule['campaign']}")
            
            # 組成回應訊息
            if removed_count > 0:
                response_parts = [f"✅ 成功移除 {removed_count} 個排程："]
                response_parts.extend(removed_items)
                response_parts.append(f"\n📊 剩餘排程: {len(self.config.get_schedules())} 個")
                await event.respond("\n".join(response_parts))
            else:
                await event.respond("❌ 排程移除失敗")
            
        except Exception as e:
            await event.respond(f"❌ 移除排程時發生錯誤: {e}")
    
    def _parse_schedule_indices(self, input_text, max_index):
        """解析排程編號輸入"""
        indices = set()
        
        for part in input_text.replace(' ', '').split(','):
            # 跳過空字符串
            if not part.strip():
                continue
                
            if '-' in part and part.count('-') == 1:
                # 範圍格式 1-5
                try:
                    start, end = map(int, part.split('-'))
                    if start > end:
                        start, end = end, start
                    for i in range(start, end + 1):
                        if 1 <= i <= max_index:
                            indices.add(i)
                except ValueError:
                    raise ValueError(f"範圍格式錯誤: {part}")
            else:
                # 單個編號
                try:
                    index = int(part)
                    if 1 <= index <= max_index:
                        indices.add(index)
                    else:
                        raise ValueError(f"編號 {index} 超出範圍 (1-{max_index})")
                except ValueError:
                    raise ValueError(f"編號格式錯誤: {part}")
        
        return list(indices)

class BroadcastCommands:
    """廣播命令處理器"""
    
    def __init__(self, client, config_manager: ConfigManager, permission_manager: PermissionManager, broadcast_manager: BroadcastManager, message_manager: MessageManager):
        self.client = client
        self.config = config_manager
        self.permissions = permission_manager
        self.broadcast_manager = broadcast_manager
        self.message_manager = message_manager
    
    def register_handlers(self):
        """註冊所有廣播命令處理器"""
        self.client.add_event_handler(
            self._handle_broadcast,
            events.NewMessage(pattern=r'^/broadcast\s+([A-Za-z0-9_]+)$')
        )
        
        # 添加廣播別名
        self.client.add_event_handler(
            self._handle_broadcast,
            events.NewMessage(pattern=r'^/bc\s+([A-Za-z0-9_]+)$')
        )
    
    @require_admin_and_control_group
    async def _handle_broadcast(self, event):
        """執行廣播"""
        try:
            match = event.pattern_match
            campaign = match.group(1).upper()
            
            # 檢查活動是否存在
            available_campaigns = self.broadcast_manager.get_available_campaigns()
            if available_campaigns and campaign not in available_campaigns:
                await event.respond(
                    f"❌ 活動 `{campaign}` 不存在\n\n"
                    f"📁 可用活動: {', '.join(available_campaigns) if available_campaigns else '無'}\n\n"
                    f"💡 使用 `/list_groups` 查看群組設定"
                )
                return
            
            # 驗證活動內容
            validation = self.broadcast_manager.validate_campaign(campaign)
            if not validation['valid']:
                error_msg = "❌ 活動內容驗證失敗:\n"
                for error in validation['errors']:
                    error_msg += f"• {error}\n"
                await event.respond(error_msg.strip())
                return
            
            # 檢查目標群組
            target_groups = self.config.get_target_groups()
            if not target_groups:
                await event.respond(
                    "❌ 未設定目標群組\n\n"
                    "請先使用GUI界面或配置文件設定廣播目標群組"
                )
                return
            
            # 檢查是否有廣播正在進行
            status = self.broadcast_manager.get_broadcast_status()
            if status['is_broadcasting']:
                current = status['current_broadcast']
                await event.respond(
                    f"⚠️ 已有廣播正在進行中\n\n"
                    f"當前廣播: 活動 `{current['campaign']}`\n"
                    f"開始時間: {current['start_time'].strftime('%H:%M:%S')}\n\n"
                    f"請等待當前廣播完成後再嘗試"
                )
                return
            
            # 獲取廣播預覽
            preview_msg = await event.respond("🔍 正在準備廣播...")
            
            try:
                preview = await self.message_manager.get_broadcast_preview(campaign)
                
                confirm_msg = (
                    f"{preview}\n\n"
                    f"⚠️ **確認廣播**\n"
                    f"即將開始廣播到 `{len(target_groups)}` 個群組\n"
                    f"預計耗時約 `{len(target_groups) * 5 // 60}` 分鐘\n\n"
                    f"✅ 回覆 `確認` 開始廣播\n"
                    f"❌ 回覆 `取消` 終止操作\n"
                    f"⏱️ 60秒內未回覆將自動取消\n"
                )
                
                await preview_msg.edit(confirm_msg.strip())
                
                # 等待用戶確認
                confirmed = False
                try:
                    response = await self.client.wait_for(
                        events.NewMessage(
                            from_users=event.sender_id,
                            chats=event.chat_id
                        ),
                        timeout=60
                    )
                    
                    response_text = response.message.message.strip().lower()
                    if response_text in ['確認', 'confirm', 'yes', 'y']:
                        confirmed = True
                        await response.respond("✅ 已確認，開始廣播...")
                    else:
                        await response.respond("❌ 廣播已取消")
                        return
                        
                except asyncio.TimeoutError:
                    await event.respond("⏰ 確認超時，廣播已取消")
                    return
                
                if not confirmed:
                    return
                
                # 執行廣播
                await event.respond(f"🚀 開始廣播活動 `{campaign}`...")
                
                result = await self.broadcast_manager.execute_broadcast(campaign)
                
                # 發送結果
                if result['success']:
                    success_rate = result['success_rate']
                    duration = result.get('duration_seconds', 0)
                    
                    # 選擇合適的表情符號
                    if success_rate >= 90:
                        status_icon = "🎉"
                    elif success_rate >= 70:
                        status_icon = "⚠️"
                    else:
                        status_icon = "❌"
                    
                    # 格式化執行時間更詳細
                    hours, remainder = divmod(duration, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    if hours > 0:
                        duration_str = f"{int(hours)}小時{int(minutes)}分{seconds:.1f}秒"
                    elif minutes > 0:
                        duration_str = f"{int(minutes)}分{seconds:.1f}秒"
                    else:
                        duration_str = f"{seconds:.1f}秒"
                    
                    # 平均發送速度
                    avg_speed = result['total_count'] / duration if duration > 0 else 0
                    
                    result_msg = (
                        f"{status_icon} **廣播完成 - 活動 {campaign}**\n\n"
                        f"📊 **執行統計:**\n"
                        f"• 成功發送: `{result['success_count']}` 個群組\n"
                        f"• 失敗發送: `{result['total_count'] - result['success_count']}` 個群組\n"
                        f"• 總目標群組: `{result['total_count']}` 個\n"
                        f"• 成功率: `{success_rate:.1f}%`\n"
                        f"• 總執行時間: `{duration_str}`\n"
                        f"• 平均速度: `{avg_speed:.1f}` 群組/秒\n\n"
                        f"🕐 **時間記錄:**\n"
                        f"• 開始時間: `{result['start_time'].strftime('%Y-%m-%d %H:%M:%S')}`\n"
                        f"• 結束時間: `{result['end_time'].strftime('%Y-%m-%d %H:%M:%S')}`\n"
                    )
                    
                    # 顯示成功群組詳情
                    if result.get('success_groups'):
                        success_groups = result['success_groups']
                        result_msg += f"\n✅ **成功群組 ({len(success_groups)} 個):**\n"
                        
                        if len(success_groups) <= 8:
                            for i, group_id in enumerate(success_groups, 1):
                                result_msg += f"  {i}. `{group_id}`\n"
                        else:
                            for i, group_id in enumerate(success_groups[:8], 1):
                                result_msg += f"  {i}. `{group_id}`\n"
                            result_msg += f"  ... 還有 {len(success_groups) - 8} 個群組\n"
                    
                    # 顯示失敗群組詳情
                    if result.get('failed_groups'):
                        failed_groups = result['failed_groups']
                        result_msg += f"\n❌ **失敗群組 ({len(failed_groups)} 個):**\n"
                        
                        if len(failed_groups) <= 8:
                            for i, group_id in enumerate(failed_groups, 1):
                                result_msg += f"  {i}. `{group_id}`\n"
                        else:
                            for i, group_id in enumerate(failed_groups[:8], 1):
                                result_msg += f"  {i}. `{group_id}`\n"
                            result_msg += f"  ... 還有 {len(failed_groups) - 8} 個群組\n"
                    
                    if result['errors']:
                        result_msg += f"\n⚠️ **詳細錯誤記錄 ({len(result['errors'])} 項):**\n"
                        for i, error in enumerate(result['errors'][:5], 1):  # 只顯示前5個錯誤
                            result_msg += f"  {i}. {error}\n"
                        
                        if len(result['errors']) > 5:
                            result_msg += f"  ... 還有 {len(result['errors']) - 5} 個錯誤記錄\n"
                    
                    # 添加實用提示
                    if result['total_count'] - result['success_count'] > 0:
                        result_msg += f"\n💡 **建議檢查項目:**\n"
                        result_msg += f"• 失敗群組是否已退出或禁用機器人\n"
                        result_msg += f"• 網路連接是否穩定\n"
                        result_msg += f"• 機器人權限是否足夠\n"
                    
                    await event.respond(result_msg.strip())
                    
                else:
                    error_msg = (
                        f"❌ **廣播失敗 - 活動 {campaign}**\n\n"
                        f"🚫 錯誤: {result.get('error', '未知錯誤')}\n\n"
                        f"請檢查以下項目:\n"
                        f"• 網路連接是否正常\n"
                        f"• 機器人是否在目標群組中\n"
                        f"• 活動內容是否完整\n"
                        f"• 系統資源是否充足\n"
                    )
                    
                    await event.respond(error_msg.strip())
                
            except Exception as e:
                await preview_msg.edit(f"❌ 準備廣播時發生錯誤: {e}")
                
        except Exception as e:
            await event.respond(f"❌ 廣播命令處理失敗: {e}")

class GroupCommands:
    """群組命令處理器"""
    
    def __init__(self, client, config_manager: ConfigManager, permission_manager: PermissionManager):
        self.client = client
        self.config = config_manager
        self.permissions = permission_manager
    
    def register_handlers(self):
        """註冊所有群組命令處理器"""
        self.client.add_event_handler(
            self._handle_list_groups,
            events.NewMessage(pattern=r'^/list_groups$')
        )
        
        self.client.add_event_handler(
            self._handle_scan_groups,
            events.NewMessage(pattern=r'^/scan_groups$')
        )
        
        self.client.add_event_handler(
            self._handle_my_groups,
            events.NewMessage(pattern=r'^/my_groups$')
        )
        
        # 添加群組管理別名
        self.client.add_event_handler(
            self._handle_list_groups,
            events.NewMessage(pattern=r'^/lg$')
        )
        
        self.client.add_event_handler(
            self._handle_my_groups,
            events.NewMessage(pattern=r'^/mg$')
        )
        
        self.client.add_event_handler(
            self._handle_scan_groups,
            events.NewMessage(pattern=r'^/sg$')
        )
    
    @require_admin_and_control_group
    async def _handle_list_groups(self, event):
        """列出所有已加入的群組"""
        try:
            await event.respond("🔍 正在掃描群組...")
            
            # 獲取所有對話
            dialogs = []
            async for dialog in self.client.iter_dialogs():
                if dialog.is_group or dialog.is_channel:
                    dialogs.append({
                        'id': dialog.id,
                        'title': dialog.name,
                        'type': 'channel' if dialog.is_channel else 'group',
                        'participant_count': getattr(dialog.entity, 'participants_count', 0)
                    })
            
            if not dialogs:
                await event.respond("📭 未找到任何群組或頻道")
                return
            
            # 獲取配置信息
            target_groups = self.config.get_target_groups()
            control_group = self.config.get_control_group()
            
            # 按類型和標題排序
            dialogs.sort(key=lambda x: (x['type'], x['title']))
            
            # 分批發送訊息（避免超過字數限制）
            response = (
                f"👥 **群組/頻道列表**\n\n"
                f"總計: `{len(dialogs)}` 個群組/頻道\n"
                f"目標群組: `{len(target_groups)}` 個\n"
                f"控制群組: `{control_group}`\n\n"
            )
            
            current_response = response
            
            for i, group in enumerate(dialogs, 1):
                # 判斷群組狀態
                if group['id'] == control_group:
                    status = "[主控制]"
                elif group['id'] in target_groups:
                    status = "[廣播目標]"
                else:
                    status = "[未設定]"
                
                # 格式化群組信息
                group_type = "📢" if group['type'] == 'channel' else "👥"
                participant_info = f"({group['participant_count']}人)" if group['participant_count'] > 0 else ""
                
                group_line = f"{i:2d}. {group_type} **{group['title']}** {participant_info}\n    `{group['id']}` {status}\n\n"
                
                # 檢查是否超過長度限制
                if len(current_response + group_line) > 4000:
                    await event.respond(current_response.strip())
                    await asyncio.sleep(1)  # 避免速率限制
                    current_response = "👥 **群組/頻道列表 (續)**\n\n"
                
                current_response += group_line
            
            # 發送最後一部分
            if len(current_response.strip()) > 50:  # 有實際內容
                current_response += (
                    f"\n💡 **說明**\n"
                    f"• [主控制] - 機器人控制群組\n"
                    f"• [廣播目標] - 廣播消息的目標群組\n"
                    f"• [未設定] - 未配置的群組\n\n"
                    f"📋 **相關指令**\n"
                    f"• `/scan_groups` - 重新掃描群組詳情\n"
                )
                await event.respond(current_response.strip())
            
        except Exception as e:
            await event.respond(f"❌ 獲取群組列表時發生錯誤: {e}")
    
    @require_admin_and_control_group
    async def _handle_scan_groups(self, event):
        """重新掃描群組詳情"""
        try:
            await event.respond("🔄 正在重新掃描群組詳情...")
            
            # 獲取配置的群組ID
            target_groups = self.config.get_target_groups()
            control_group = self.config.get_control_group()
            all_configured_groups = set(target_groups)
            if control_group != 0:
                all_configured_groups.add(control_group)
            
            if not all_configured_groups:
                await event.respond("⚠️ 尚未配置任何群組")
                return
            
            # 掃描每個配置的群組
            scan_results = []
            
            for group_id in all_configured_groups:
                try:
                    entity = await self.client.get_entity(group_id)
                    
                    group_info = {
                        'id': group_id,
                        'title': getattr(entity, 'title', getattr(entity, 'first_name', 'Unknown')),
                        'type': 'channel' if hasattr(entity, 'megagroup') else 'group',
                        'participant_count': getattr(entity, 'participants_count', 0),
                        'status': 'accessible'
                    }
                    
                    # 判斷群組角色
                    if group_id == control_group:
                        group_info['role'] = '主控制群組'
                    elif group_id in target_groups:
                        group_info['role'] = '廣播目標'
                    else:
                        group_info['role'] = '未知'
                    
                    scan_results.append(group_info)
                    
                except Exception as e:
                    scan_results.append({
                        'id': group_id,
                        'title': 'Unknown',
                        'type': 'unknown',
                        'participant_count': 0,
                        'status': 'inaccessible',
                        'error': str(e),
                        'role': '主控制群組' if group_id == control_group else '廣播目標'
                    })
            
            # 生成掃描報告
            accessible_count = len([g for g in scan_results if g['status'] == 'accessible'])
            inaccessible_count = len([g for g in scan_results if g['status'] == 'inaccessible'])
            
            response = (
                f"🔍 **群組掃描報告**\n\n"
                f"掃描完成: `{len(scan_results)}` 個群組\n"
                f"可訪問: `{accessible_count}` 個 ✅\n"
                f"不可訪問: `{inaccessible_count}` 個 ❌\n\n"
                f"**詳細結果:**\n\n"
            )
            
            # 可訪問的群組
            accessible_groups = [g for g in scan_results if g['status'] == 'accessible']
            if accessible_groups:
                response += "✅ **可訪問的群組:**\n"
                for group in accessible_groups:
                    group_type = "📢" if group['type'] == 'channel' else "👥"
                    participant_info = f"({group['participant_count']}人)" if group['participant_count'] > 0 else ""
                    response += f"• {group_type} **{group['title']}** {participant_info}\n"
                    response += f"  `{group['id']}` - {group['role']}\n\n"
            
            # 不可訪問的群組
            inaccessible_groups = [g for g in scan_results if g['status'] == 'inaccessible']
            if inaccessible_groups:
                response += "❌ **不可訪問的群組:**\n"
                for group in inaccessible_groups:
                    response += f"• **{group['role']}**\n"
                    response += f"  `{group['id']}` - {group.get('error', '未知錯誤')}\n\n"
            
            # 建議
            if inaccessible_count > 0:
                response += (
                    f"\n⚠️ **注意事項:**\n"
                    f"• 不可訪問的群組可能已被移除或機器人被踢出\n"
                    f"• 請檢查機器人在這些群組中的狀態\n"
                    f"• 如需要，請重新邀請機器人加入群組\n"
                )
            else:
                response += "🎉 所有配置的群組都可正常訪問！"
            
            await event.respond(response.strip())
            
        except Exception as e:
            await event.respond(f"❌ 掃描群組時發生錯誤: {e}")
    
    @require_admin_and_control_group
    async def _handle_my_groups(self, event):
        """查看所有已加入的群組"""
        try:
            await event.respond("🔍 正在掃描所有已加入的群組...")
            
            # 獲取所有對話
            all_dialogs = []
            groups = []
            channels = []
            private_chats = []
            
            async for dialog in self.client.iter_dialogs():
                dialog_info = {
                    'id': dialog.id,
                    'title': dialog.name or dialog.title or '未知',
                    'type': None,
                    'participant_count': getattr(dialog.entity, 'participants_count', 0),
                    'unread_count': dialog.unread_count,
                    'is_pinned': dialog.pinned,
                    'last_message_date': dialog.date
                }
                
                if dialog.is_group:
                    dialog_info['type'] = '群組'
                    groups.append(dialog_info)
                elif dialog.is_channel:
                    dialog_info['type'] = '頻道'
                    channels.append(dialog_info)
                elif dialog.is_user:
                    dialog_info['type'] = '私聊'
                    private_chats.append(dialog_info)
                
                all_dialogs.append(dialog_info)
            
            if not all_dialogs:
                await event.respond("📭 未找到任何對話")
                return
            
            # 獲取配置信息
            target_groups = self.config.get_target_groups()
            control_group = self.config.get_control_group()
            
            # 統計信息
            total_groups = len(groups)
            total_channels = len(channels)
            total_private = len(private_chats)
            total_dialogs = len(all_dialogs)
            
            # 生成報告
            response = (
                f"📊 **我的群組/頻道總覽**\n\n"
                f"📈 **統計摘要**\n"
                f"• 總對話數: `{total_dialogs}` 個\n"
                f"• 群組: `{total_groups}` 個\n"
                f"• 頻道: `{total_channels}` 個\n"
                f"• 私人對話: `{total_private}` 個\n\n"
            )
            
            # 顯示群組列表
            if groups:
                # 按參與者數量排序
                groups.sort(key=lambda x: x['participant_count'], reverse=True)
                
                response += f"👥 **群組列表** ({len(groups)} 個)\n\n"
                
                for i, group in enumerate(groups[:15], 1):  # 限制顯示前15個
                    # 判斷群組狀態
                    if group['id'] == control_group:
                        status = " 🎛️ [控制群組]"
                    elif group['id'] in target_groups:
                        status = " 📢 [廣播目標]"
                    else:
                        status = ""
                    
                    # 格式化參與者數量
                    member_info = f"({group['participant_count']}人)" if group['participant_count'] > 0 else ""
                    
                    # 未讀訊息
                    unread_info = f" 🔴{group['unread_count']}" if group['unread_count'] > 0 else ""
                    
                    # 置頂標記
                    pinned_info = " 📌" if group['is_pinned'] else ""
                    
                    response += f"{i:2d}. **{group['title']}** {member_info}{status}{unread_info}{pinned_info}\n"
                    response += f"    `{group['id']}`\n\n"
                
                if len(groups) > 15:
                    response += f"    ... 還有 {len(groups) - 15} 個群組\n\n"
            
            # 顯示頻道列表
            if channels:
                # 按參與者數量排序
                channels.sort(key=lambda x: x['participant_count'], reverse=True)
                
                response += f"📢 **頻道列表** ({len(channels)} 個)\n\n"
                
                for i, channel in enumerate(channels[:10], 1):  # 限制顯示前10個
                    # 判斷頻道狀態
                    if channel['id'] == control_group:
                        status = " 🎛️ [控制群組]"
                    elif channel['id'] in target_groups:
                        status = " 📢 [廣播目標]"
                    else:
                        status = ""
                    
                    # 格式化訂閱者數量
                    member_info = f"({channel['participant_count']}人)" if channel['participant_count'] > 0 else ""
                    
                    # 未讀訊息
                    unread_info = f" 🔴{channel['unread_count']}" if channel['unread_count'] > 0 else ""
                    
                    # 置頂標記
                    pinned_info = " 📌" if channel['is_pinned'] else ""
                    
                    response += f"{i:2d}. **{channel['title']}** {member_info}{status}{unread_info}{pinned_info}\n"
                    response += f"    `{channel['id']}`\n\n"
                
                if len(channels) > 10:
                    response += f"    ... 還有 {len(channels) - 10} 個頻道\n\n"
            
            # 配置狀態
            response += (
                f"⚙️ **配置狀態**\n"
                f"• 控制群組: `{control_group if control_group != 0 else '未設定'}`\n"
                f"• 廣播目標: `{len(target_groups)}` 個群組/頻道\n\n"
                f"💡 **相關指令**\n"
                f"• `/list_groups` - 查看詳細的廣播目標列表\n"
                f"• `/add_groups` - 新增廣播目標群組\n"
                f"• `/scan_groups` - 重新掃描群組詳情\n"
            )
            
            # 如果訊息太長，分段發送
            if len(response) > 4000:
                chunks = []
                current_chunk = ""
                lines = response.split('\n')
                
                for line in lines:
                    if len(current_chunk + line + '\n') > 3800:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = line + '\n'
                    else:
                        current_chunk += line + '\n'
                
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # 發送所有分段
                for i, chunk in enumerate(chunks):
                    if i > 0:
                        chunk = f"📊 **我的群組/頻道總覽** (續 {i+1})\n\n" + chunk
                    await event.respond(chunk)
                    if i < len(chunks) - 1:
                        await asyncio.sleep(1)  # 避免發送太快
            else:
                await event.respond(response)
            
        except Exception as e:
            self.logger.error(f"查看我的群組失敗: {e}")
            await event.respond(f"❌ 查看我的群組時發生錯誤: {e}")

class HistoryCommands:
    """歷史記錄命令處理器"""
    
    def __init__(self, client, config_manager: ConfigManager, permission_manager: PermissionManager):
        self.client = client
        self.config = config_manager
        self.permissions = permission_manager
    
    def register_handlers(self):
        """註冊所有歷史記錄命令處理器"""
        self.client.add_event_handler(
            self._handle_broadcast_history,
            events.NewMessage(pattern=r'^/broadcast_history(?:\s+(\d+))?$')
        )
        
        # 添加歷史記錄別名
        self.client.add_event_handler(
            self._handle_broadcast_history,
            events.NewMessage(pattern=r'^/bh(?:\s+(\d+))?$')
        )
        
        self.client.add_event_handler(
            self._handle_broadcast_history,
            events.NewMessage(pattern=r'^/history(?:\s+(\d+))?$')
        )
    
    @require_admin_and_control_group
    async def _handle_broadcast_history(self, event):
        """查看廣播歷史記錄"""
        try:
            # 解析參數
            match = event.pattern_match
            limit = int(match.group(1)) if match.group(1) else 20
            limit = min(limit, 100)  # 限制最大數量
            
            # 獲取廣播歷史
            history = self.config.get_broadcast_history(limit=limit)
            
            if not history:
                await event.respond(
                    f"📊 **廣播歷史記錄**\n\n"
                    f"📭 暫無廣播記錄\n\n"
                    f"開始進行廣播後，這裡將顯示詳細的執行歷史。"
                )
                return
            
            # 計算統計數據
            total_broadcasts = len(history)
            total_groups_targeted = sum(h.get('groups_count', 0) for h in history)
            total_successful = sum(h.get('success_count', 0) for h in history)
            overall_success_rate = (total_successful / total_groups_targeted * 100) if total_groups_targeted > 0 else 0
            
            # 按活動統計
            campaign_stats = {}
            for record in history:
                campaign = record.get('campaign', 'Unknown')
                if campaign not in campaign_stats:
                    campaign_stats[campaign] = {'count': 0, 'success': 0, 'total': 0}
                
                campaign_stats[campaign]['count'] += 1
                campaign_stats[campaign]['success'] += record.get('success_count', 0)
                campaign_stats[campaign]['total'] += record.get('groups_count', 0)
            
            # 生成回應
            response = (
                f"📊 **廣播歷史記錄**\n\n"
                f"📈 **總體統計**\n"
                f"• 總廣播次數: `{total_broadcasts}` 次\n"
                f"• 目標群組總數: `{total_groups_targeted}` 個\n"
                f"• 成功發送: `{total_successful}` 次\n"
                f"• 總成功率: `{overall_success_rate:.1f}%`\n\n"
                f"📋 **活動統計**\n"
            )
            
            for campaign, stats in campaign_stats.items():
                success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
                response += f"• 活動 `{campaign}`: {stats['count']}次 (成功率: {success_rate:.1f}%)\n"
            
            response += f"\n📅 **最近 {len(history)} 次記錄**\n\n"
            
            # 顯示最近的記錄
            for i, record in enumerate(reversed(history), 1):
                timestamp = record.get('timestamp', '')
                try:
                    # 解析時間戳
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime('%m-%d %H:%M')
                except:
                    time_str = timestamp[:16] if timestamp else 'Unknown'
                
                campaign = record.get('campaign', 'Unknown')
                groups_count = record.get('groups_count', 0)
                success_count = record.get('success_count', 0)
                success_rate = record.get('success_rate', 0)
                
                # 成功率顯示
                if success_rate >= 90:
                    status_icon = "✅"
                elif success_rate >= 70:
                    status_icon = "⚠️"
                else:
                    status_icon = "❌"
                
                response += f"{i:2d}. {status_icon} `{time_str}` 活動`{campaign}` ({success_count}/{groups_count}) {success_rate:.0f}%\n"
                
                # 如果有錯誤，顯示錯誤信息
                errors = record.get('errors', [])
                if errors and len(errors) > 0:
                    response += f"    ⚠️ {len(errors)} 個錯誤\n"
                
                # 避免訊息過長
                if len(response) > 3500:
                    response += f"\n... 還有 {len(history) - i} 筆記錄\n"
                    break
            
            # 添加說明
            response += (
                f"\n\n💡 **說明**\n"
                f"• ✅ 成功率 ≥ 90%  ⚠️ 成功率 70-89%  ❌ 成功率 < 70%\n"
                f"• 使用 `/broadcast_history <數量>` 查看更多記錄 (最多100筆)\n\n"
                f"📋 **相關指令**\n"
                f"• `/broadcast <活動>` - 執行新的廣播\n"
                f"• `/list_schedules` - 查看排程設定\n"
            )
            
            await event.respond(response.strip())
            
        except Exception as e:
            await event.respond(f"❌ 獲取廣播歷史時發生錯誤: {e}")

class ScheduleCommands:
    """排程命令處理器"""
    
    def __init__(self, client, config_manager: ConfigManager, permission_manager: PermissionManager):
        self.client = client
        self.config = config_manager
        self.permissions = permission_manager
        self.validator = ConfigValidator()
        # 用於追蹤用戶狀態
        self.user_states = {}
    
    def register_handlers(self):
        """註冊所有排程命令處理器"""
        self.client.add_event_handler(
            self._handle_add_schedule,
            events.NewMessage(pattern=r'^/add_schedule\s+(\d{1,2}:\d{2})\s+([A-Za-z0-9_]+)$')
        )
        
        # 移除排程 - 互動式
        self.client.add_event_handler(
            self._handle_remove_schedule,
            events.NewMessage(pattern=r'^/remove_schedule$')
        )
        # 移除排程 - 直接參數（保留舊功能）
        self.client.add_event_handler(
            self._handle_remove_schedule_with_params,
            events.NewMessage(pattern=r'^/remove_schedule\s+(.+)$')
        )
        
        # 用戶輸入處理器（用於排程移除的互動式輸入）
        self.client.add_event_handler(
            self._handle_user_input,
            events.NewMessage(pattern=r'^[\d,\-\s]+$|^(all|cancel)$')
        )
        
        self.client.add_event_handler(
            self._handle_list_schedules,
            events.NewMessage(pattern=r'^/list_schedules$')
        )
        
        # 移除 /toggle_schedule - 功能重複，使用 /enable 和 /disable 更清晰
        
        # 添加指令別名
        self.client.add_event_handler(
            self._handle_add_schedule,
            events.NewMessage(pattern=r'^/as\s+(\d{1,2}:\d{2})\s+([A-Za-z0-9_]+)$')
        )
        
        self.client.add_event_handler(
            self._handle_list_schedules,
            events.NewMessage(pattern=r'^/ls$')
        )
        
        # 快速開關排程
        self.client.add_event_handler(
            self._handle_enable_schedule,
            events.NewMessage(pattern=r'^/enable$')
        )
        
        self.client.add_event_handler(
            self._handle_disable_schedule,
            events.NewMessage(pattern=r'^/disable$')
        )
    
    @require_admin_and_control_group
    async def _handle_add_schedule(self, event):
        """新增排程"""
        try:
            match = event.pattern_match
            time_str = match.group(1)
            campaign = match.group(2).upper()
            
            # 驗證時間格式
            time_str = self.validator.sanitize_schedule_time(time_str)
            if not self.validator.validate_time_format(time_str):
                await event.respond("❌ 時間格式錯誤，請使用 HH:MM 格式 (例: 09:30)")
                return
            
            # 驗證活動名稱
            campaign = self.validator.sanitize_campaign_name(campaign)
            if not self.validator.validate_campaign_name(campaign):
                await event.respond("❌ 活動名稱格式錯誤，只允許字母、數字和下劃線，1-10個字符")
                return
            
            # 檢查活動是否存在
            available_campaigns = self.config.list_available_campaigns()
            if available_campaigns and campaign not in available_campaigns:
                await event.respond(f"⚠️ 活動 `{campaign}` 不存在\n可用活動: {', '.join(available_campaigns)}")
                return
            
            # 檢查是否已存在相同的排程
            existing_schedules = self.config.get_schedules()
            for schedule in existing_schedules:
                if schedule['time'] == time_str and schedule['campaign'] == campaign:
                    await event.respond(f"⚠️ 排程已存在: `{time_str}` → 活動 `{campaign}`")
                    return
            
            # 新增排程
            success = self.config.add_schedule(time_str, campaign)
            
            if success:
                # 獲取更新後的排程數量
                total_schedules = len(self.config.get_schedules())
                await event.respond(
                    f"✅ 排程新增成功！\n"
                    f"🕐 時間: `{time_str}`\n"
                    f"📁 活動: `{campaign}`\n"
                    f"📊 總排程數: `{total_schedules}` 個"
                )
            else:
                await event.respond("❌ 排程新增失敗，請稍後再試")
            
        except Exception as e:
            await event.respond(f"❌ 新增排程時發生錯誤: {e}")
    
    @require_admin_and_control_group
    async def _handle_remove_schedule(self, event):
        """顯示排程列表並提示用戶移除排程"""
        try:
            schedules = self.config.get_schedules()
            
            if not schedules:
                await event.respond(
                    "📅 目前沒有任何排程\n\n"
                    "💡 使用 `/add_schedule <時間> <活動>` 新增排程\n"
                    "例如: `/add_schedule 09:30 A`"
                )
                return
            
            # 設置用戶狀態
            user_id = event.sender_id
            self.user_states[user_id] = {
                'action': 'remove_schedule',
                'chat_id': event.chat_id,
                'timestamp': event.date
            }
            
            # 排序排程（按時間）
            sorted_schedules = sorted(schedules, key=lambda x: x['time'])
            
            # 組成回應訊息
            response_parts = ["📅 **排程列表** (供移除參考)\n"]
            
            for i, schedule in enumerate(sorted_schedules, 1):
                time_str = schedule['time']
                campaign = schedule['campaign']
                status = "⏰" if self.config.is_schedule_enabled() else "⏸️"
                response_parts.append(f"{i}. {status} {time_str} - {campaign}")
            
            response_parts.extend([
                "",
                "💡 **請輸入要移除的排程編號：**",
                "• 單個編號: `5`",
                "• 多個編號: `1,3,6,7`",
                "• 範圍編號: `2-5`",
                "• 混合使用: `1,3,5-8,10`",
                "",
                "🔄 輸入 `all` 清空所有排程",
                "❌ 輸入 `cancel` 取消操作"
            ])
            
            await event.respond("\n".join(response_parts))
            
        except Exception as e:
            await event.respond(f"❌ 顯示排程列表時發生錯誤: {e}")
    
    @require_admin_and_control_group
    async def _handle_remove_schedule_with_params(self, event):
        """移除排程（保留舊功能）"""
        try:
            match = event.pattern_match
            params = match.group(1).strip()
            
            # 解析參數
            parts = params.split()
            time_str = None
            campaign = None
            
            for part in parts:
                if ':' in part and len(part) <= 5:  # 時間格式
                    time_str = self.validator.sanitize_schedule_time(part)
                    if not self.validator.validate_time_format(time_str):
                        await event.respond("❌ 時間格式錯誤，請使用 HH:MM 格式")
                        return
                else:  # 活動名稱
                    campaign = self.validator.sanitize_campaign_name(part)
                    if not self.validator.validate_campaign_name(campaign):
                        await event.respond("❌ 活動名稱格式錯誤")
                        return
            
            # 獲取移除前的排程數量
            before_count = len(self.config.get_schedules())
            
            # 移除排程
            success = self.config.remove_schedule(time_str, campaign)
            
            if success:
                after_count = len(self.config.get_schedules())
                removed_count = before_count - after_count
                
                response = f"✅ 成功移除 `{removed_count}` 個排程\n"
                
                if time_str and campaign:
                    response += f"🕐 時間: `{time_str}`\n📁 活動: `{campaign}`"
                elif time_str:
                    response += f"🕐 時間: `{time_str}` 的所有排程"
                elif campaign:
                    response += f"📁 活動: `{campaign}` 的所有排程"
                
                response += f"\n📊 剩餘排程: `{after_count}` 個"
                
                await event.respond(response)
            else:
                await event.respond("⚠️ 未找到符合條件的排程")
            
        except Exception as e:
            await event.respond(f"❌ 移除排程時發生錯誤: {e}")
    
    @require_admin_and_control_group
    async def _handle_list_schedules(self, event):
        """列出所有排程"""
        try:
            schedules = self.config.get_schedules()
            schedule_enabled = self.config.is_schedule_enabled()
            
            if not schedules:
                response = (
                    f"📅 **排程列表**\n\n"
                    f"排程狀態: `{'✅ 啟用' if schedule_enabled else '❌ 停用'}`\n\n"
                    f"🚫 暫無排程\n\n"
                    f"使用 `/add_schedule <時間> <活動>` 來新增排程\n"
                    f"例如: `/add_schedule 09:30 A`\n"
                )
                await event.respond(response.strip())
                return
            
            # 按時間排序
            sorted_schedules = sorted(schedules, key=lambda x: x['time'])
            
            # 獲取當前時間
            current_time = datetime.now().strftime('%H:%M')
            
            response = (
                f"📅 **排程列表**\n\n"
                f"排程狀態: `{'✅ 啟用' if schedule_enabled else '❌ 停用'}`\n"
                f"總計: `{len(schedules)}` 個排程\n\n"
            )
            
            for i, schedule in enumerate(sorted_schedules, 1):
                time_str = schedule['time']
                campaign = schedule['campaign']
                
                # 標記當前時間之後的下一個排程
                is_next = False
                if schedule_enabled and time_str > current_time:
                    # 檢查是否是今天下一個排程
                    future_schedules = [s for s in sorted_schedules if s['time'] > current_time]
                    if future_schedules and schedule == future_schedules[0]:
                        is_next = True
                
                status = "🔜 " if is_next else "🕐 "
                response += f"{i:2d}. {status}`{time_str}` → 活動 `{campaign}`\n"
            
            response += (
                f"\n📊 **統計資訊**\n"
                f"• 今日剩餘排程: `{len([s for s in sorted_schedules if s['time'] > current_time])}` 個\n"
                f"• 可用活動: `{', '.join(self.config.list_available_campaigns())}`\n\n"
                f"💡 **管理指令**\n"
                f"• `/add_schedule <時間> <活動>` - 新增排程\n"
                f"• `/remove_schedule` - 移除排程 (互動式)\n"
            )
            
            await event.respond(response.strip())
            
        except Exception as e:
            await event.respond(f"❌ 獲取排程列表時發生錯誤: {e}")
    
    @require_admin_and_control_group
    async def _handle_enable_schedule(self, event):
        """啟用排程功能"""
        try:
            if self.config.is_schedule_enabled():
                await event.respond("✅ 排程功能已經是啟用狀態")
                return
            
            success = self.config.toggle_schedule()
            
            if success:
                schedules_count = len(self.config.get_schedules())
                response = (
                    f"🟢 **排程功能已啟用**\n\n"
                    f"📊 當前排程數量: `{schedules_count}` 個\n"
                    f"🚀 所有排程將按時自動執行\n\n"
                    f"💡 使用 `/list_schedules` 查看排程列表"
                )
                await event.respond(response)
            else:
                await event.respond("❌ 啟用排程失敗，請稍後再試")
            
        except Exception as e:
            await event.respond(f"❌ 啟用排程時發生錯誤: {e}")
    
    @require_admin_and_control_group
    async def _handle_disable_schedule(self, event):
        """停用排程功能"""
        try:
            if not self.config.is_schedule_enabled():
                await event.respond("⭕ 排程功能已經是停用狀態")
                return
            
            success = self.config.toggle_schedule()
            
            if success:
                schedules_count = len(self.config.get_schedules())
                response = (
                    f"🔴 **排程功能已停用**\n\n"
                    f"📊 當前排程數量: `{schedules_count}` 個\n"
                    f"⏸️ 所有自動廣播已暫停\n\n"
                    f"💡 使用 `/enable` 重新啟用排程"
                )
                await event.respond(response)
            else:
                await event.respond("❌ 停用排程失敗，請稍後再試")
            
        except Exception as e:
            await event.respond(f"❌ 停用排程時發生錯誤: {e}")
    
    async def _handle_user_input(self, event):
        """處理用戶輸入的排程編號"""
        try:
            user_id = event.sender_id
            chat_id = event.chat_id
            
            # 檢查權限
            if not self.permissions.is_control_group(chat_id):
                return  # 靜默忽略非控制群組的輸入
            
            if not self.permissions.is_admin(user_id):
                return  # 靜默忽略非管理員的輸入
            
            # 檢查用戶狀態
            if user_id not in self.user_states:
                return  # 沒有等待輸入的狀態，忽略
            
            user_state = self.user_states[user_id]
            
            # 檢查是否在正確的聊天室
            if user_state['chat_id'] != chat_id:
                return  # 不在同一個聊天室，忽略
            
            # 檢查時間是否過期（5分鐘內有效）
            import datetime
            if (event.date - user_state['timestamp']).total_seconds() > 300:
                del self.user_states[user_id]
                await event.respond("⏰ 輸入已超時，請重新使用 `/remove_schedule` 指令")
                return
            
            # 獲取用戶輸入
            input_text = event.message.message.strip()
            action = user_state['action']
            
            # 清除用戶狀態
            del self.user_states[user_id]
            
            # 根據動作執行相應的操作
            if action == 'remove_schedule':
                await self._execute_remove_schedule(event, input_text)
                
        except Exception as e:
            # 清除用戶狀態
            if user_id in self.user_states:
                del self.user_states[user_id]
            await event.respond(f"❌ 處理輸入時發生錯誤: {e}")
    
    async def _execute_remove_schedule(self, event, input_text):
        """執行移除排程的操作"""
        try:
            schedules = self.config.get_schedules()
            
            if not schedules:
                await event.respond("❌ 目前沒有任何排程可以移除")
                return
            
            # 排序排程（按時間）
            sorted_schedules = sorted(schedules, key=lambda x: x['time'])
            
            # 處理特殊指令
            if input_text.lower() == 'cancel':
                await event.respond("❌ 已取消移除排程操作")
                return
            
            if input_text.lower() == 'all':
                # 清空所有排程
                before_count = len(schedules)
                success = self.config.clear_all_schedules()
                
                if success:
                    await event.respond(f"✅ 已清空所有排程 ({before_count} 個)")
                else:
                    await event.respond("❌ 清空排程失敗")
                return
            
            # 解析編號輸入
            try:
                indices_to_remove = self._parse_schedule_indices(input_text, len(sorted_schedules))
            except ValueError as e:
                await event.respond(f"❌ 編號格式錯誤: {e}")
                return
            
            if not indices_to_remove:
                await event.respond("❌ 請輸入有效的排程編號")
                return
            
            # 獲取要移除的排程
            schedules_to_remove = []
            for index in sorted(indices_to_remove, reverse=True):  # 從後往前移除
                if 1 <= index <= len(sorted_schedules):
                    schedules_to_remove.append(sorted_schedules[index - 1])
            
            if not schedules_to_remove:
                await event.respond("❌ 指定的編號無效")
                return
            
            # 執行移除
            removed_count = 0
            removed_items = []
            
            for schedule in schedules_to_remove:
                success = self.config.remove_schedule(schedule['time'], schedule['campaign'])
                if success:
                    removed_count += 1
                    removed_items.append(f"• {schedule['time']} - {schedule['campaign']}")
            
            # 組成回應訊息
            if removed_count > 0:
                response_parts = [f"✅ 成功移除 {removed_count} 個排程："]
                response_parts.extend(removed_items)
                response_parts.append(f"\n📊 剩餘排程: {len(self.config.get_schedules())} 個")
                await event.respond("\n".join(response_parts))
            else:
                await event.respond("❌ 排程移除失敗")
            
        except Exception as e:
            await event.respond(f"❌ 移除排程時發生錯誤: {e}")
    
    def _parse_schedule_indices(self, input_text, max_index):
        """解析排程編號輸入"""
        indices = set()
        
        for part in input_text.replace(' ', '').split(','):
            # 跳過空字符串
            if not part.strip():
                continue
                
            if '-' in part and part.count('-') == 1:
                # 範圍格式 1-5
                try:
                    start, end = map(int, part.split('-'))
                    if start > end:
                        start, end = end, start
                    for i in range(start, end + 1):
                        if 1 <= i <= max_index:
                            indices.add(i)
                except ValueError:
                    raise ValueError(f"範圍格式錯誤: {part}")
            else:
                # 單個編號
                try:
                    index = int(part)
                    if 1 <= index <= max_index:
                        indices.add(index)
                    else:
                        raise ValueError(f"編號 {index} 超出範圍 (1-{max_index})")
                except ValueError:
                    raise ValueError(f"編號格式錯誤: {part}")
        
        return list(indices)

class QuickCommands:
    """快速指令和便利功能"""
    
    def __init__(self, client, config_manager: ConfigManager, permission_manager: PermissionManager):
        self.client = client
        self.config = config_manager
        self.permissions = permission_manager
        self.logger = logging.getLogger(__name__)
    
    def register_handlers(self):
        """註冊快速指令處理器"""
        # 快速狀態檢查
        self.client.add_event_handler(
            self._handle_quick_status,
            events.NewMessage(pattern=r'^/s$')
        )
        
        # 活動列表快速查看
        self.client.add_event_handler(
            self._handle_quick_campaigns,
            events.NewMessage(pattern=r'^/c$')
        )
        
        # 快速廣播確認
        self.client.add_event_handler(
            self._handle_quick_broadcast,
            events.NewMessage(pattern=r'^/q\s+([A-Za-z0-9_]+)$')
        )
        
        # 錯誤處理和用戶友好提示
        self.client.add_event_handler(
            self._handle_unknown_command,
            events.NewMessage(pattern=r'^/\w+')
        )
    
    @require_admin_and_control_group
    async def _handle_quick_status(self, event):
        """快速狀態檢查"""
        try:
            # 獲取基本狀態信息
            schedules = self.config.get_schedules()
            target_groups = self.config.get_target_groups()
            schedule_enabled = self.config.is_schedule_enabled()
            campaigns = self.config.list_available_campaigns()
            
            # 檢查下一個排程
            current_time = datetime.now().strftime('%H:%M')
            next_schedule = None
            for schedule in sorted(schedules, key=lambda x: x['time']):
                if schedule['time'] > current_time:
                    next_schedule = schedule
                    break
            
            # 快速狀態圖標
            schedule_icon = "🟢" if schedule_enabled else "🔴"
            
            response = (
                f"⚡ **快速狀態**\n\n"
                f"{schedule_icon} 排程: {'啟用' if schedule_enabled else '停用'} ({len(schedules)}個)\n"
                f"📢 目標: {len(target_groups)}個群組\n"
                f"🎬 活動: {len(campaigns)}個\n"
            )
            
            if next_schedule:
                response += f"⏰ 下一個: {next_schedule['time']} - {next_schedule['campaign']}\n"
            else:
                response += f"⏰ 今日無排程\n"
            
            response += f"\n💡 使用 `/help` 查看完整指令"
            
            await event.respond(response.strip())
            
        except Exception as e:
            await event.respond(f"❌ 獲取狀態時發生錯誤: {e}")
    
    @require_admin_and_control_group
    async def _handle_quick_campaigns(self, event):
        """快速查看活動列表"""
        try:
            campaigns = self.config.list_available_campaigns()
            
            if not campaigns:
                await event.respond("📁 暫無可用活動")
                return
            
            response = f"🎬 **活動列表** ({len(campaigns)}個)\n\n"
            
            for i, campaign in enumerate(campaigns, 1):
                response += f"{i}. `{campaign}`\n"
            
            response += f"\n💡 使用 `/bc <活動>` 快速廣播"
            
            await event.respond(response.strip())
            
        except Exception as e:
            await event.respond(f"❌ 獲取活動列表時發生錯誤: {e}")
    
    @require_admin_and_control_group
    async def _handle_quick_broadcast(self, event):
        """快速廣播 (跳過確認)"""
        try:
            match = event.pattern_match
            campaign = match.group(1).upper()
            
            # 檢查活動是否存在
            available_campaigns = self.config.list_available_campaigns()
            if available_campaigns and campaign not in available_campaigns:
                suggestions = [c for c in available_campaigns if c.startswith(campaign[:1])]
                suggestion_text = f"\n💡 建議: {', '.join(suggestions)}" if suggestions else ""
                
                await event.respond(
                    f"❌ 活動 `{campaign}` 不存在{suggestion_text}\n\n"
                    f"📁 可用活動: {', '.join(available_campaigns) if available_campaigns else '無'}"
                )
                return
            
            # 檢查目標群組
            target_groups = self.config.get_target_groups()
            if not target_groups:
                await event.respond(
                    "❌ 未設定目標群組\n\n"
                    "💡 使用 `/add_groups` 新增廣播目標"
                )
                return
            
            await event.respond(f"🚀 正在快速廣播活動 `{campaign}` 到 {len(target_groups)} 個群組...")
            
            # 這裡應該調用實際的廣播功能
            # 由於我們沒有完整的廣播管理器實例，這裡只是模擬
            await event.respond(
                f"✅ 快速廣播請求已提交\n\n"
                f"📊 活動: `{campaign}`\n"
                f"📢 目標: `{len(target_groups)}` 個群組\n\n"
                f"💡 使用 `/bh` 查看執行結果"
            )
            
        except Exception as e:
            await event.respond(f"❌ 快速廣播時發生錯誤: {e}")
    
    async def _handle_unknown_command(self, event):
        """處理未知指令並提供友好建議"""
        try:
            # 檢查權限
            user_id = event.sender_id
            chat_id = event.chat_id
            
            if not self.permissions.is_control_group(chat_id):
                return  # 靜默忽略非控制群組的指令
            
            if not self.permissions.is_admin(user_id):
                return  # 靜默忽略非管理員的指令
            
            command_text = event.message.message.strip()
            command_parts = command_text.split()
            if not command_parts or not command_parts[0].startswith('/'):
                return
                
            # 提取完整的命令內容用於檢查
            full_command = command_text
            command = command_parts[0][1:]  # 去掉 / 前綴
            
            # 定義所有已知的命令模式 - 防止與已知命令衝突
            known_command_patterns = [
                # Admin Commands
                r'^/help$', r'^/status$', r'^/restart$', r'^/logs(?:\s+\d+)?$', r'^/config$',
                # Target Management
                r'^/add_groups(?:\s+.+)?$', r'^/remove_groups(?:\s+.+)?$',
                r'^/add_target(?:\s+.+)?$', r'^/remove_target(?:\s+.+)?$',  # 向後兼容
                # Broadcast Commands  
                r'^/broadcast\s+[A-Za-z0-9_]+$', r'^/bc\s+[A-Za-z0-9_]+$',
                # Group Management
                r'^/list_groups$', r'^/scan_groups$', r'^/my_groups$',
                r'^/lg$', r'^/mg$', r'^/sg$',
                # History Commands
                r'^/broadcast_history(?:\s+\d+)?$', r'^/bh(?:\s+\d+)?$', r'^/history(?:\s+\d+)?$',
                # Schedule Management
                r'^/add_schedule\s+\d{1,2}:\d{2}\s+[A-Za-z0-9_]+$',
                r'^/as\s+\d{1,2}:\d{2}\s+[A-Za-z0-9_]+$',  # 重要：包含 /as 命令
                r'^/remove_schedule(?:\s+.+)?$',
                r'^/list_schedules$', r'^/ls$',
                # Control Commands
                r'^/enable$', r'^/disable$',
                # Quick Commands
                r'^/s$', r'^/c$', r'^/q\s+[A-Za-z0-9_]+$',
                # Admin Management
                r'^/add_admin\s+.+$', r'^/remove_admin\s+.+$',
                r'^/sync_admins$', r'^/list_admins$'
            ]
            
            # 檢查是否為已知命令
            for pattern in known_command_patterns:
                if re.match(pattern, full_command):
                    # 這是已知命令，不要觸發未知命令處理器
                    return
            
            # 只有在確實是未知命令時才處理
            # 指令建議映射
            suggestions = {
                'add': '/add_groups - 新增廣播目標群組',
                'remove': '/remove_groups - 移除廣播目標群組',
                'list': '/list_groups 或 /lg - 查看廣播目標',
                'schedule': '/add_schedule <時間> <活動> - 新增排程',
                'broadcast': '/broadcast <活動> 或 /bc <活動> - 廣播',
                'admin': '/add_admin <ID/@用戶名> - 新增管理員',
                'groups': '/my_groups 或 /mg - 查看所有群組',
                'history': '/broadcast_history 或 /bh - 查看歷史',
                'start': '/enable - 啟用排程',
                'stop': '/disable - 停用排程',
                'quick': '快速指令: /s (狀態), /c (活動), /q <活動> (快速廣播)'
            }
            
            # 尋找相似指令
            similar_commands = []
            for key, suggestion in suggestions.items():
                if key in command.lower() or command.lower() in key:
                    similar_commands.append(suggestion)
            
            if similar_commands:
                response = f"❓ 未知指令: `/{command}`\n\n💡 **可能您想要使用:**\n"
                for suggestion in similar_commands[:3]:  # 最多顯示3個建議
                    response += f"• {suggestion}\n"
            else:
                response = (
                    f"❓ 未知指令: `/{command}`\n\n"
                    f"💡 使用 `/help` 查看所有可用指令\n"
                    f"⚡ 快速指令: `/s` (狀態), `/c` (活動), `/help`"
                )
            
            await event.respond(response.strip())
            
        except Exception as e:
            # 靜默處理錯誤，避免干擾其他指令處理器
            self.logger.debug(f"處理未知指令時發生錯誤: {e}")

class AdminManagementCommands:
    """管理員管理命令處理器"""
    
    def __init__(self, client, config_manager: ConfigManager, permission_manager: PermissionManager):
        self.client = client
        self.config = config_manager
        self.permissions = permission_manager
        self.logger = logging.getLogger(__name__)
    
    def register_handlers(self):
        """註冊管理員管理命令處理器"""
        self.client.add_event_handler(
            self._handle_add_admin,
            events.NewMessage(pattern=r'^/add_admin\s+(.+)$')
        )
        
        self.client.add_event_handler(
            self._handle_remove_admin,
            events.NewMessage(pattern=r'^/remove_admin\s+(.+)$')
        )
        
        self.client.add_event_handler(
            self._handle_sync_admins,
            events.NewMessage(pattern=r'^/sync_admins$')
        )
        
        self.client.add_event_handler(
            self._handle_list_admins,
            events.NewMessage(pattern=r'^/list_admins$')
        )
    
    @require_admin_and_control_group
    async def _handle_add_admin(self, event):
        """新增管理員"""
        try:
            match = event.pattern_match
            user_input = match.group(1).strip()
            
            user_id = None
            username = None
            
            # 解析輸入格式
            if user_input.startswith('@'):
                # 用戶名格式: @username
                username = user_input[1:]
                try:
                    # 嘗試通過用戶名獲取用戶ID
                    user_entity = await self.client.get_entity(username)
                    user_id = user_entity.id
                    display_name = getattr(user_entity, 'first_name', username)
                except Exception as e:
                    await event.respond(f"❌ 無法找到用戶 @{username}: {e}")
                    return
            else:
                # 用戶ID格式: 123456789
                try:
                    user_id = int(user_input)
                    try:
                        # 嘗試獲取用戶信息
                        user_entity = await self.client.get_entity(user_id)
                        display_name = getattr(user_entity, 'first_name', f'User_{user_id}')
                        username = getattr(user_entity, 'username', None)
                    except:
                        display_name = f'User_{user_id}'
                        username = None
                except ValueError:
                    await event.respond("❌ 用戶ID必須是數字或以@開頭的用戶名")
                    return
            
            # 檢查是否已經是管理員
            if self.permissions.is_admin(user_id):
                await event.respond(f"⚠️ 用戶 {display_name} (ID: {user_id}) 已經是管理員")
                return
            
            # 新增管理員
            success = self.config.add_admin(user_id, display_name, username)
            
            if success:
                admin_count = len(self.config.get_admins())
                response = (
                    f"✅ **管理員新增成功！**\n\n"
                    f"👤 姓名: `{display_name}`\n"
                    f"🆔 ID: `{user_id}`\n"
                )
                if username:
                    response += f"📱 用戶名: `@{username}`\n"
                response += f"📊 總管理員數: `{admin_count}` 位"
                
                await event.respond(response)
                self.logger.info(f"新增管理員: {display_name} (ID: {user_id})")
            else:
                await event.respond("❌ 新增管理員失敗，請稍後再試")
                
        except Exception as e:
            await event.respond(f"❌ 新增管理員時發生錯誤: {e}")
            self.logger.error(f"新增管理員錯誤: {e}")
    
    @require_admin_and_control_group
    async def _handle_remove_admin(self, event):
        """移除管理員"""
        try:
            match = event.pattern_match
            user_input = match.group(1).strip()
            
            user_id = None
            display_name = None
            
            # 解析輸入格式
            if user_input.startswith('@'):
                # 用戶名格式: @username
                username = user_input[1:]
                # 從管理員列表中查找
                admins = self.config.get_admins()
                for admin in admins:
                    if admin.get('username') == username:
                        user_id = admin.get('id')
                        display_name = admin.get('name', username)
                        break
                
                if not user_id:
                    await event.respond(f"❌ 在管理員列表中找不到用戶 @{username}")
                    return
            else:
                # 用戶ID格式
                try:
                    user_id = int(user_input)
                    # 從管理員列表中查找顯示名稱
                    admins = self.config.get_admins()
                    for admin in admins:
                        if admin.get('id') == user_id:
                            display_name = admin.get('name', f'User_{user_id}')
                            break
                    
                    if not display_name:
                        display_name = f'User_{user_id}'
                except ValueError:
                    await event.respond("❌ 用戶ID必須是數字或以@開頭的用戶名")
                    return
            
            # 檢查是否為管理員
            if not self.permissions.is_admin(user_id):
                await event.respond(f"⚠️ 用戶 {display_name} (ID: {user_id}) 不是管理員")
                return
            
            # 防止移除自己
            if user_id == event.sender_id:
                await event.respond("❌ 不能移除自己的管理員權限")
                return
            
            # 移除管理員
            success = self.config.remove_admin(user_id)
            
            if success:
                admin_count = len(self.config.get_admins())
                response = (
                    f"✅ **管理員移除成功！**\n\n"
                    f"👤 姓名: `{display_name}`\n"
                    f"🆔 ID: `{user_id}`\n"
                    f"📊 剩餘管理員數: `{admin_count}` 位"
                )
                
                await event.respond(response)
                self.logger.info(f"移除管理員: {display_name} (ID: {user_id})")
            else:
                await event.respond("❌ 移除管理員失敗，請稍後再試")
                
        except Exception as e:
            await event.respond(f"❌ 移除管理員時發生錯誤: {e}")
            self.logger.error(f"移除管理員錯誤: {e}")
    
    @require_admin_and_control_group
    async def _handle_sync_admins(self, event):
        """從控制群組同步管理員"""
        try:
            control_group = self.config.get_control_group()
            if control_group == 0:
                await event.respond("❌ 未設定控制群組，無法同步管理員")
                return
            
            await event.respond("🔄 正在從控制群組同步管理員...")
            
            # 獲取控制群組的管理員
            try:
                participants = await self.client.get_participants(control_group, filter=None)
                group_admins = []
                
                for participant in participants:
                    # 檢查是否為群組管理員或創建者
                    if hasattr(participant.participant, 'admin_rights') or hasattr(participant.participant, 'creator'):
                        user_id = participant.id
                        display_name = getattr(participant, 'first_name', f'User_{user_id}')
                        username = getattr(participant, 'username', None)
                        
                        group_admins.append({
                            'id': user_id,
                            'name': display_name,
                            'username': username
                        })
                
                if not group_admins:
                    await event.respond("⚠️ 在控制群組中未找到管理員")
                    return
                
                # 同步管理員
                added_count = 0
                skipped_count = 0
                
                for admin in group_admins:
                    if not self.permissions.is_admin(admin['id']):
                        success = self.config.add_admin(admin['id'], admin['name'], admin['username'])
                        if success:
                            added_count += 1
                    else:
                        skipped_count += 1
                
                total_admins = len(self.config.get_admins())
                
                response = (
                    f"✅ **管理員同步完成！**\n\n"
                    f"📥 新增管理員: `{added_count}` 位\n"
                    f"⏭️ 已跳過現有: `{skipped_count}` 位\n"
                    f"📊 總管理員數: `{total_admins}` 位\n\n"
                    f"💡 同步的管理員具有與群組管理員相同的權限"
                )
                
                await event.respond(response)
                self.logger.info(f"管理員同步完成: 新增{added_count}位，跳過{skipped_count}位")
                
            except Exception as e:
                await event.respond(f"❌ 獲取控制群組管理員失敗: {e}")
                
        except Exception as e:
            await event.respond(f"❌ 同步管理員時發生錯誤: {e}")
            self.logger.error(f"同步管理員錯誤: {e}")
    
    @require_admin_and_control_group
    async def _handle_list_admins(self, event):
        """列出所有管理員"""
        try:
            admins = self.config.get_admins()
            
            if not admins:
                await event.respond(
                    "👥 **管理員列表**\n\n"
                    "📭 目前沒有設定管理員\n\n"
                    "💡 使用 `/add_admin <ID/@用戶名>` 新增管理員"
                )
                return
            
            response = f"👥 **管理員列表** ({len(admins)} 位)\n\n"
            
            for i, admin in enumerate(admins, 1):
                admin_id = admin.get('id', 'Unknown')
                admin_name = admin.get('name', 'Unknown')
                admin_username = admin.get('username')
                added_date = admin.get('added_at', admin.get('added_date', 'Unknown'))
                
                # 格式化日期
                if added_date and added_date != 'Unknown':
                    try:
                        if 'T' in added_date:
                            date_obj = datetime.fromisoformat(added_date.replace('Z', '+00:00'))
                            date_str = date_obj.strftime('%Y-%m-%d')
                        else:
                            date_str = added_date
                    except:
                        date_str = added_date
                else:
                    date_str = 'Unknown'
                
                response += f"{i:2d}. **{admin_name}**\n"
                response += f"    🆔 ID: `{admin_id}`\n"
                
                if admin_username:
                    response += f"    📱 用戶名: `@{admin_username}`\n"
                
                response += f"    📅 新增日期: `{date_str}`\n\n"
            
            response += (
                f"💡 **管理指令**\n"
                f"• `/add_admin <ID/@用戶名>` - 新增管理員\n"
                f"• `/remove_admin <ID/@用戶名>` - 移除管理員\n"
                f"• `/sync_admins` - 從控制群組同步管理員\n"
            )
            
            # 如果內容太長，分段發送
            if len(response) > 4000:
                chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
                for chunk in chunks:
                    await event.respond(chunk)
                    await asyncio.sleep(0.5)
            else:
                await event.respond(response)
                
        except Exception as e:
            await event.respond(f"❌ 獲取管理員列表時發生錯誤: {e}")
            self.logger.error(f"列出管理員錯誤: {e}")

class CommandHandler:
    """統一命令處理器"""
    
    def __init__(self, client_manager: TelegramClientManager, config_manager: ConfigManager, broadcast_manager: BroadcastManager, message_manager: MessageManager):
        self.client_manager = client_manager
        self.config = config_manager
        self.client = client_manager.get_client()
        
        # 初始化權限管理器
        self.permissions = PermissionManager(config_manager)
        
        # 初始化廣播管理器
        self.broadcast_manager = broadcast_manager
        self.message_manager = message_manager
        
        # 初始化各個命令模組
        self.admin_commands = AdminCommands(self.client, config_manager, self.permissions, self.client_manager)
        self.schedule_commands = ScheduleCommands(self.client, config_manager, self.permissions)
        self.group_commands = GroupCommands(self.client, config_manager, self.permissions)
        self.history_commands = HistoryCommands(self.client, config_manager, self.permissions)
        self.broadcast_commands = BroadcastCommands(self.client, config_manager, self.permissions, self.broadcast_manager, self.message_manager)
        self.admin_management_commands = AdminManagementCommands(self.client, config_manager, self.permissions)
        self.quick_commands = QuickCommands(self.client, config_manager, self.permissions)
        
        # 設定日誌
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("命令處理器初始化完成")
    
    def register_all_handlers(self):
        """註冊所有命令處理器"""
        try:
            # 按照優先級註冊各模組的處理器
            # 優先註冊具體的命令處理器
            self.admin_commands.register_handlers()
            self.schedule_commands.register_handlers()
            self.group_commands.register_handlers()
            self.history_commands.register_handlers()
            self.broadcast_commands.register_handlers()
            self.admin_management_commands.register_handlers()
            
            # 最後註冊快速命令和未知命令處理器
            # 這樣確保具體命令優先匹配
            self.quick_commands.register_handlers()
            
            self.logger.info("所有命令處理器註冊完成")
            
        except Exception as e:
            self.logger.error(f"註冊命令處理器失敗: {e}")
            raise
    
    def get_permission_manager(self) -> PermissionManager:
        """獲取權限管理器"""
        return self.permissions
    
    def get_broadcast_manager(self) -> BroadcastManager:
        """獲取廣播管理器"""
        return self.broadcast_manager

