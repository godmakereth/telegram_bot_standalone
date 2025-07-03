"""
Telegram客戶端管理器 - 修復Python 3.13兼容性問題
"""
import asyncio
import threading
import logging
from typing import Optional, Callable, Dict, Any
from telethon import TelegramClient, errors
from telethon.tl.types import User

from config import ConfigManager


class TelegramClientManager:
    """Telegram客戶端管理器"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.client: Optional[TelegramClient] = None
        self.is_connected = False
        self.current_user: Optional[User] = None
        self.logger = logging.getLogger(__name__)
        self.logger.info("TelegramClientManager initialized, client is not created yet.")

    def _initialize_client(self, api_id: int, api_hash: str):
        """Initializes the TelegramClient instance with provided credentials."""
        try:
            session_name = self.config_manager.get_api_config().get("session_name", "userbot")
            self.client = TelegramClient(session_name, api_id, api_hash)
            self.logger.info("TelegramClient instance created.")
        except Exception as e:
            self.logger.error(f"Failed to initialize TelegramClient: {e}")
            self.client = None

    async def start_client(self, api_id: int, api_hash: str, phone: str) -> bool:
        """
        Initializes, connects, and logs in the client.
        This method is the new main entry point for connection.
        """
        try:
            if not self.client:
                self._initialize_client(api_id, api_hash)
                if not self.client:
                    return False

            self.logger.info("Starting Telegram client...")
            # The start() method handles everything: connect, sign in, 2FA.
            # It will prompt for code/password in the console where the script is run.
            await self.client.start(phone=lambda: phone)
            self.is_connected = self.client.is_connected()

            if self.is_connected:
                # 正確獲取當前用戶信息
                self.current_user = await self.client.get_me()
                if self.current_user:
                    self.logger.info(f"Client started successfully. Logged in as {self.current_user.first_name}")
                    return True
                else:
                    self.logger.error("Failed to get current user info")
                    return False
            else:
                self.logger.error("Client failed to start or connect.")
                self.is_connected = False
                return False

        except Exception as e:
            self.logger.error(f"Failed to start client: {e}", exc_info=True)
            self.is_connected = False
            return False

    async def disconnect(self):
        """斷開Telegram連接"""
        if self.client and self.client.is_connected():
            try:
                await self.client.disconnect()
                self.logger.info("已斷開連接")
            except Exception as e:
                self.logger.error(f"斷開連接時發生錯誤: {e}")
        
        self.is_connected = False
        self.current_user = None
    
    async def get_me(self) -> Optional[User]:
        """獲取當前用戶信息"""
        if not self.client or not self.client.is_connected():
            return None
        
        try:
            if await self.client.is_user_authorized():
                self.current_user = await self.client.get_me()
                return self.current_user
        except Exception as e:
            self.logger.error(f"獲取用戶信息失敗: {e}")
        
        return None
    
    async def is_authorized(self) -> bool:
        """檢查是否已認證"""
        if not self.client or not self.client.is_connected():
            return False
        
        try:
            return await self.client.is_user_authorized()
        except Exception as e:
            self.logger.error(f"檢查認證狀態失敗: {e}")
            return False
    
    async def send_message(self, entity, message: str, **kwargs) -> bool:
        """發送訊息"""
        if not self.client or not await self.is_authorized():
            self.logger.error("客戶端未認證")
            return False
        
        try:
            await self.client.send_message(entity, message, **kwargs)
            return True
        except Exception as e:
            self.logger.error(f"發送訊息失敗: {e}")
            return False
    
    async def send_file(self, entity, file_path: str, caption: str = None, **kwargs) -> bool:
        """發送檔案"""
        if not self.client or not await self.is_authorized():
            self.logger.error("客戶端未認證")
            return False
        
        try:
            await self.client.send_file(entity, file_path, caption=caption, **kwargs)
            return True
        except Exception as e:
            self.logger.error(f"發送檔案失敗: {e}")
            return False
    
    async def get_dialogs(self):
        """獲取對話列表"""
        if not self.client or not await self.is_authorized():
            self.logger.error("客戶端未認證")
            return []
        
        try:
            dialogs = []
            async for dialog in self.client.iter_dialogs():
                if dialog.is_group or dialog.is_channel:
                    dialogs.append({
                        'id': dialog.id,
                        'title': dialog.name,
                        'type': 'channel' if dialog.is_channel else 'group',
                        'participant_count': getattr(dialog.entity, 'participants_count', 0)
                    })
            return dialogs
        except Exception as e:
            self.logger.error(f"獲取對話列表失敗: {e}")
            return []
    
    async def get_entity_info(self, entity_id: int) -> Optional[Dict[str, Any]]:
        """獲取實體信息"""
        if not self.client or not await self.is_authorized():
            return None
        
        try:
            entity = await self.client.get_entity(entity_id)
            return {
                'id': entity.id,
                'title': getattr(entity, 'title', getattr(entity, 'first_name', 'Unknown')),
                'type': 'channel' if hasattr(entity, 'megagroup') else 'group',
                'participant_count': getattr(entity, 'participants_count', 0)
            }
        except Exception as e:
            self.logger.error(f"獲取實體信息失敗 {entity_id}: {e}")
            return None
    
    def get_client(self) -> Optional[TelegramClient]:
        """獲取原始客戶端對象"""
        return self.client
    
    def is_client_connected(self) -> bool:
        """檢查客戶端連接狀態"""
        return self.client and self.client.is_connected() if self.client else False
    
    def reinitialize_client(self):
        """重新初始化客戶端"""
        if self.client:
            try:
                # 在異步上下文中關閉現有客戶端
                if self.client.is_connected():
                    asyncio.create_task(self.client.disconnect())
            except:
                pass
        
        self._initialize_client()