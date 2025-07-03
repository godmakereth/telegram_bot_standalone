#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram 廣播機器人 - 獨立版本
只包含 Telegram Bot 功能，不含 GUI 界面
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/logs/bot.log')
    ]
)

logger = logging.getLogger("TelegramBot")

# 導入核心組件
from config import ConfigManager
from telegram_client import TelegramClientManager
from command_handler import CommandHandler
from scheduler import BroadcastScheduler
from permissions import PermissionManager
from broadcast_manager import BroadcastManager
from message_manager import MessageManager


class TelegramBotStandalone:
    """獨立 Telegram 廣播機器人"""
    
    def __init__(self):
        """初始化廣播機器人"""
        self.config_manager = ConfigManager()
        self.client_manager = None
        self.broadcast_manager = None
        self.message_manager = None
        self.permission_manager = None
        self.command_handler = None
        self.scheduler = None
        self.running = False
        
        # 信號處理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("🤖 Telegram 廣播機器人初始化完成")
    
    def _signal_handler(self, signum, frame):
        """處理信號，優雅關閉"""
        logger.info(f"收到信號 {signum}，準備關閉機器人...")
        self.running = False
    
    def _status_callback(self, message: str):
        """狀態回調函數"""
        logger.info(f"📢 {message}")
    
    async def _list_all_groups(self):
        """列出所有 Bot 加入的群組並顯示廣播狀態"""
        try:
            logger.info("🔍 正在掃描所有已加入的群組...")
            
            # 直接使用 Telethon 客戶端獲取對話
            client = self.client_manager.get_client()
            target_groups = self.config_manager.get_target_groups()
            control_group = self.config_manager.get_control_group()
            
            # 篩選群組和頻道
            groups = []
            channels = []
            
            async for dialog in client.iter_dialogs():
                # 只處理群組和頻道
                if dialog.is_group or dialog.is_channel:
                    entity = dialog.entity
                    group_id = dialog.id
                    
                    # 處理超級群組的負數 ID (Telethon 通常已經處理好了)
                    # 但確保一致性
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
            
            # 顯示結果
            logger.info(f"📊 群組掃描完成：找到 {len(groups)} 個群組，{len(channels)} 個頻道")
            
            # 合併群組和頻道，統一顯示
            if groups or channels:
                all_items = groups + channels
                logger.info("[群組/頻道偵測結果]")
                
                for i, item in enumerate(all_items, 1):
                    # 判斷廣播狀態
                    if item['is_control']:
                        status = "[控制群組]"
                    elif item['is_target']:
                        status = "[設定廣播]"
                    else:
                        status = "[未設定廣播]"
                    
                    logger.info(f"{i}. {item['title']} ({item['id']}) {status}")
            
            # 統計摘要
            target_count = len([g for g in groups + channels if g['is_target']])
            logger.info("=" * 50)
            logger.info(f"📈 統計摘要：")
            logger.info(f"  🎮 控制群組: {'已設定' if any(g['is_control'] for g in groups) else '未設定'}")
            logger.info(f"  🎯 廣播目標: {target_count} 個")
            logger.info(f"  📱 總群組/頻道: {len(groups) + len(channels)} 個")
            
            return groups + channels
            
        except Exception as e:
            logger.error(f"❌ 掃描群組時發生錯誤: {e}")
            return []
    
    async def _send_startup_info_to_control_group(self, groups_info):
        """發送啟動資訊和群組列表到控制群組"""
        try:
            control_group = self.config_manager.get_control_group()
            if control_group == 0:
                logger.warning("⚠️ 控制群組未設定，無法發送啟動資訊")
                return
            
            # 準備啟動資訊
            user = self.client_manager.current_user
            target_groups = self.config_manager.get_target_groups()
            admins = self.config_manager.get_admins()
            broadcast_config = self.config_manager.broadcast_config
            schedules = broadcast_config.get('schedules', [])
            
            # 分類群組
            groups = [g for g in groups_info if g['type'] == 'group']
            channels = [g for g in groups_info if g['type'] == 'channel']
            target_count = len([g for g in groups_info if g['is_target']])
            
            # 構建啟動訊息
            startup_msg = (
                f"🤖 **Telegram 廣播機器人已啟動**\n\n"
                f"👤 **Bot 身分:** {user.first_name} (@{user.username or 'N/A'})\n"
                f"🆔 **Bot ID:** `{user.id}`\n\n"
                f"📊 **配置摘要:**\n"
                f"🎮 控制群組: `{control_group}`\n"
                f"🎯 廣播目標: {target_count} 個\n"
                f"👤 管理員: {len(admins)} 位\n"
                f"⏰ 排程: {len(schedules)} 個\n\n"
                f"📱 **群組統計:**\n"
                f"📋 已加入群組: {len(groups)} 個\n"
                f"📺 已加入頻道: {len(channels)} 個\n"
                f"📈 總計: {len(groups_info)} 個"
            )
            
            # 發送啟動資訊
            await self.client_manager.send_message(control_group, startup_msg)
            
            # 合併群組和頻道，統一發送
            if groups or channels:
                all_items = groups + channels
                combined_msg = "**[群組/頻道偵測結果]**\n\n"
                
                for i, item in enumerate(all_items, 1):
                    # 判斷廣播狀態
                    if item['is_control']:
                        status = "[控制群組]"
                    elif item['is_target']:
                        status = "[設定廣播]"
                    else:
                        status = "[未設定廣播]"
                    
                    combined_msg += f"{i}. {item['title']} ({item['id']}) {status}\n"
                
                # 如果訊息太長，分段發送
                if len(combined_msg) > 4000:
                    chunks = []
                    current_chunk = "**[群組/頻道偵測結果]**\n\n"
                    
                    for i, item in enumerate(all_items, 1):
                        # 判斷廣播狀態
                        if item['is_control']:
                            status = "[控制群組]"
                        elif item['is_target']:
                            status = "[設定廣播]"
                        else:
                            status = "[未設定廣播]"
                        
                        item_info = f"{i}. {item['title']} ({item['id']}) {status}\n"
                        
                        if len(current_chunk + item_info) > 4000:
                            chunks.append(current_chunk)
                            current_chunk = "**[群組/頻道偵測結果 (續)]**\n\n" + item_info
                        else:
                            current_chunk += item_info
                    
                    if current_chunk:
                        chunks.append(current_chunk)
                    
                    # 發送所有分段
                    for chunk in chunks:
                        await self.client_manager.send_message(control_group, chunk)
                        await asyncio.sleep(1)  # 避免發送太快
                else:
                    await self.client_manager.send_message(control_group, combined_msg)
            
            logger.info("✅ 啟動資訊已發送到控制群組")
            
        except Exception as e:
            logger.error(f"❌ 發送啟動資訊到控制群組時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    async def initialize(self):
        """初始化機器人組件"""
        try:
            # 檢查配置
            api_config = self.config_manager.get_api_config()
            if not all([api_config.get('api_id'), api_config.get('api_hash'), api_config.get('phone')]):
                logger.error("❌ API 配置不完整，請先設置 Telegram API 資訊")
                return False
            
            # 初始化 Telegram 客戶端
            self.client_manager = TelegramClientManager(self.config_manager)
            success = await self.client_manager.start_client(
                api_config['api_id'],
                api_config['api_hash'], 
                api_config['phone']
            )
            
            if not success:
                logger.error("❌ Telegram 客戶端連接失敗")
                return False
            
            # 初始化廣播管理器
            self.broadcast_manager = BroadcastManager(self.client_manager, self.config_manager)
            
            # 初始化訊息管理器
            self.message_manager = MessageManager(
                self.client_manager, 
                self.config_manager, 
                self.broadcast_manager.content_loader,
                self.broadcast_manager.sender
            )
            
            # 初始化命令處理器
            self.command_handler = CommandHandler(
                self.client_manager,
                self.config_manager,
                self.broadcast_manager,
                self.message_manager
            )
            
            # 註冊事件處理器
            self.command_handler.register_all_handlers()
            
            # 初始化排程器
            self.scheduler = BroadcastScheduler(self.config_manager, self.broadcast_manager)
            await self.scheduler.start_scheduler()
            
            logger.info("✅ 機器人所有組件初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def run(self):
        """運行機器人"""
        logger.info("🚀 啟動 Telegram 廣播機器人...")
        
        # 初始化組件
        if not await self.initialize():
            logger.error("❌ 機器人初始化失敗，退出")
            return
        
        # 顯示機器人資訊
        user = self.client_manager.current_user
        logger.info(f"✅ 機器人已啟動，登入身分: {user.first_name} (@{user.username or 'N/A'})")
        
        # 顯示配置資訊
        control_group = self.config_manager.get_control_group()
        target_groups = self.config_manager.get_target_groups()
        admins = self.config_manager.get_admins()
        
        logger.info(f"📋 控制群組: {control_group}")
        logger.info(f"🎯 廣播目標: {len(target_groups)} 個群組")
        logger.info(f"👤 管理員: {len(admins)} 位")
        
        # 檢查排程狀態
        broadcast_config = self.config_manager.broadcast_config
        if broadcast_config.get('enabled', True):
            schedules = broadcast_config.get('schedules', [])
            logger.info(f"⏰ 自動廣播已啟用，共 {len(schedules)} 個排程")
        else:
            logger.info("⏰ 自動廣播已停用")
        
        # 掃描並顯示所有群組
        groups_info = await self._list_all_groups()
        
        # 發送群組資訊到控制群組
        await self._send_startup_info_to_control_group(groups_info)
        
        # 主運行循環
        self.running = True
        logger.info("🔄 機器人進入監聽模式，按 Ctrl+C 停止")
        
        try:
            while self.running:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info("⚠️  運行循環被取消")
        except Exception as e:
            logger.error(f"❌ 運行時錯誤: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """清理資源"""
        logger.info("🧹 正在清理資源...")
        
        try:
            # 停止排程器
            if self.scheduler:
                await self.scheduler.stop_scheduler()
                logger.info("✅ 排程器已停止")
            
            # 停止廣播管理器
            if self.broadcast_manager:
                # BroadcastManager 通常不需要特殊清理
                logger.info("✅ 廣播管理器已清理")
            
            # 斷開 Telegram 連接
            if self.client_manager:
                await self.client_manager.disconnect()
                logger.info("✅ Telegram 客戶端已斷開")
                
        except Exception as e:
            logger.error(f"❌ 清理時發生錯誤: {e}")
        
        logger.info("👋 機器人已完全停止")


def main():
    """主函數"""
    # 檢查 Python 版本
    if sys.version_info < (3, 8):
        print("❌ 錯誤: 需要 Python 3.8 或更高版本")
        sys.exit(1)
    
    # 檢查依賴
    try:
        import telethon
        logger.info("✅ 依賴檢查通過")
    except ImportError as e:
        print(f"❌ 缺少依賴: {e}")
        print("請運行: pip install -r requirements.txt")
        sys.exit(1)
    
    # 檢查必要目錄
    data_dir = Path("data")
    if not data_dir.exists():
        logger.error("❌ 找不到 data 目錄，請確保專案結構完整")
        sys.exit(1)
    
    # 創建並運行機器人
    bot = TelegramBotStandalone()
    
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("⚠️  收到中斷信號，正在停止...")
    except Exception as e:
        logger.error(f"❌ 未預期的錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()