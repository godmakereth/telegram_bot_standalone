#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
權限管理模組 - 處理管理員和控制群組權限驗證
"""
import logging
from functools import wraps
from typing import List, Union
from telethon import events

from config import ConfigManager


class PermissionManager:
    """權限管理器"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        
    def is_admin(self, user_id: int) -> bool:
        """檢查用戶是否為管理員"""
        try:
            admins = self.config.get_admins()
            return any(admin.get('id') == user_id for admin in admins)
        except Exception as e:
            self.logger.error(f"檢查管理員權限時發生錯誤: {e}")
            return False
    
    def is_control_group(self, chat_id: int) -> bool:
        """檢查是否為控制群組"""
        try:
            control_group = self.config.get_control_group()
            return control_group == chat_id
        except Exception as e:
            self.logger.error(f"檢查控制群組權限時發生錯誤: {e}")
            return False
    
    def has_permission(self, user_id: int, chat_id: int) -> bool:
        """檢查用戶是否在控制群組中並且是管理員"""
        return self.is_admin(user_id) and self.is_control_group(chat_id)
    
    def get_admin_list(self) -> List[dict]:
        """獲取管理員列表"""
        try:
            return self.config.get_admins()
        except Exception as e:
            self.logger.error(f"獲取管理員列表時發生錯誤: {e}")
            return []


def require_admin_and_control_group(func):
    """裝飾器: 要求管理員權限和控制群組"""
    @wraps(func)
    async def wrapper(self, event):
        # 獲取用戶和聊天信息
        user_id = event.sender_id
        chat_id = event.chat_id
        
        # 檢查權限
        if not hasattr(self, 'permissions'):
            self.logger.error("未找到權限管理器")
            return
            
        if not self.permissions.is_control_group(chat_id):
            return  # 靜默忽略非控制群組的訊息
            
        if not self.permissions.is_admin(user_id):
            await event.respond("❌ 您沒有執行此命令的權限。")
            return
        
        # 執行原函數
        return await func(self, event)
    
    return wrapper


def require_admin(func):
    """裝飾器: 僅要求管理員權限"""
    @wraps(func)
    async def wrapper(self, event):
        user_id = event.sender_id
        
        if not hasattr(self, 'permissions'):
            self.logger.error("未找到權限管理器")
            return
            
        if not self.permissions.is_admin(user_id):
            await event.respond("❌ 您沒有執行此命令的權限。")
            return
        
        return await func(self, event)
    
    return wrapper


def require_control_group(func):
    """裝飾器: 僅要求控制群組"""
    @wraps(func)
    async def wrapper(self, event):
        chat_id = event.chat_id
        
        if not hasattr(self, 'permissions'):
            self.logger.error("未找到權限管理器")
            return
            
        if not self.permissions.is_control_group(chat_id):
            return  # 靜默忽略非控制群組的訊息
        
        return await func(self, event)
    
    return wrapper