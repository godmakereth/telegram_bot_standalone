
"""
訊息管理器 - 負責格式化和預覽廣播訊息
"""
import asyncio
import logging
from typing import Dict, Any, Tuple

from telegram_client import TelegramClientManager
from config import ConfigManager
from broadcast_manager import ContentLoader, BroadcastSender

class MessageManager:
    """訊息管理器"""
    
    def __init__(self, client_manager: TelegramClientManager, config_manager: ConfigManager, content_loader: ContentLoader, sender: BroadcastSender):
        self.client_manager = client_manager
        self.config = config_manager
        self.content_loader = content_loader
        self.sender = sender
        self.client = client_manager.get_client()
        self.logger = logging.getLogger(__name__)

    async def send_test_broadcast(self, campaign: str, test_group_id: int = None) -> Tuple[bool, str]:
        """
        發送測試廣播
        
        Args:
            campaign: 活動名稱
            test_group_id: 測試群組ID, 如果為None則使用控制群組
            
        Returns:
            Tuple[bool, str]: (是否成功, 結果消息)
        """
        try:
            # 確定測試群組
            if test_group_id is None:
                test_group_id = self.config.get_control_group()
            
            if test_group_id == 0:
                return False, "未設定測試群組或控制群組"
            
            # 載入內容
            content = self.content_loader.load_campaign_content(campaign)
            if not content:
                return False, f"無法載入活動 {campaign} 的內容"
            
            # 驗證內容
            validation = self.content_loader.validate_campaign_content(campaign)
            if not validation['valid']:
                return False, f"活動內容無效: {', '.join(validation['errors'])}"
            
            # 發送測試消息前綴
            test_prefix = f"🧪 **測試廣播 - 活動 {campaign}**\n" + "="*30 + "\n\n"
            
            # 發送測試內容
            success = True
            error_msg = ""
            
            try:
                # 發送前綴
                await self.client.send_message(test_group_id, test_prefix)
                await asyncio.sleep(1)
                
                # 發送實際內容
                send_success = await self.sender._send_content_to_group(test_group_id, content)
                
                if not send_success:
                    success = False
                    error_msg = "發送內容失敗"
                else:
                    # 發送測試結果摘要
                    summary = validation['content_summary']
                    result_msg = (
                        f"🔍 **測試結果摘要**\n\n"
                        f"✅ 活動 `{campaign}` 測試發送成功\n\n"
                        f"📊 **內容統計:**\n"
                        f"• 文字: {'✅' if summary['has_text'] else '❌'} ({summary['text_length']} 字符)\n"
                        f"• 圖片: {summary['images_count']} 個\n"
                        f"• 影片: {summary['videos_count']} 個\n"
                        f"• GIF: {summary['gifs_count']} 個\n\n"
                        f"⚠️ **注意:** 這是測試廣播，實際廣播將發送到 {len(self.config.get_target_groups())} 個群組"
                    )
                    
                    await asyncio.sleep(2)
                    await self.client.send_message(test_group_id, result_msg.strip())
                
            except Exception as e:
                success = False
                error_msg = str(e)
            
            if success:
                return True, f"活動 {campaign} 測試廣播成功"
            else:
                return False, f"測試廣播失敗: {error_msg}"
                
        except Exception as e:
            return False, f"測試廣播過程發生錯誤: {e}"
    
    async def get_broadcast_preview(self, campaign: str) -> str:
        """
        獲取廣播內容預覽
        
        Args:
            campaign: 活動名稱
            
        Returns:
            str: 內容預覽文字
        """
        try:
            validation = self.content_loader.validate_campaign_content(campaign)
            
            if not validation['valid']:
                return f"❌ 活動 {campaign} 內容無效"
            
            content = self.content_loader.load_campaign_content(campaign)
            if not content:
                return f"❌ 無法載入活動 {campaign}"
            
            summary = validation['content_summary']
            target_groups_count = len(self.config.get_target_groups())
            
            preview = (
                f"📋 **廣播預覽 - 活動 {campaign}**\n\n"
                f"🎯 **目標:** {target_groups_count} 個群組\n"
                f"⏱️ **預計時間:** ~{target_groups_count * self.sender.send_delay // 60} 分鐘\n\n"
                f"📄 **內容摘要:**\n"
            )
            
            if summary['has_text']:
                text_preview = content['text'][:100] + "..." if len(content['text']) > 100 else content['text']
                preview += f"• 文字內容: {summary['text_length']} 字符\n"
                preview += f"  預覽: \"{text_preview}\"\n"
            
            if summary['images_count'] > 0:
                preview += f"• 圖片: {summary['images_count']} 個\n"
            
            if summary['videos_count'] > 0:
                preview += f"• 影片: {summary['videos_count']} 個\n"
            
            if summary['gifs_count'] > 0:
                preview += f"• GIF: {summary['gifs_count']} 個\n"
            
            if validation['warnings']:
                preview += f"\n⚠️ **警告:**\n"
                for warning in validation['warnings']:
                    preview += f"• {warning}\n"
            
            return preview.strip()
            
        except Exception as e:
            return f"❌ 獲取預覽失敗: {e}"

