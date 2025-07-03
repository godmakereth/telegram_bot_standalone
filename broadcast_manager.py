"""
廣播管理器 - 統一管理廣播相關功能
"""
import asyncio
import logging
import os
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime

from telegram_client import TelegramClientManager
from config import ConfigManager

class ContentLoader:
    """內容載入器"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
    
    def load_campaign_content(self, campaign: str) -> Optional[Dict[str, Any]]:
        """
        載入指定活動的內容
        
        Args:
            campaign: 活動名稱 (A, B, C, D, E)
            
        Returns:
            Dict: 包含文字、圖片、影片等內容的字典
        """
        try:
            campaign = campaign.upper()
            campaign_path = self.config.get_content_path(campaign)
            
            if not os.path.exists(campaign_path):
                self.logger.warning(f"活動目錄不存在: {campaign_path}")
                return None
            
            content = {
                'campaign': campaign,
                'text': None,
                'images': [],
                'videos': [],
                'gifs': [],
                'files': []
            }
            
            # 載入文字內容
            text_files = ['message.txt', 'text.txt']
            for text_file in text_files:
                text_path = os.path.join(campaign_path, text_file)
                if os.path.exists(text_path):
                    try:
                        with open(text_path, 'r', encoding='utf-8') as f:
                            content['text'] = f.read().strip()
                        self.logger.debug(f"載入文字內容: {text_path}")
                        break
                    except Exception as e:
                        self.logger.warning(f"讀取文字文件失敗 {text_path}: {e}")
            
            # 載入媒體文件
            for item in os.listdir(campaign_path):
                item_path = os.path.join(campaign_path, item)
                
                if not os.path.isfile(item_path):
                    continue
                
                # 獲取文件擴展名
                _, ext = os.path.splitext(item.lower())
                
                # 分類文件
                if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                    content['images'].append(item_path)
                elif ext in ['.mp4', '.avi', '.mov', '.mkv']:
                    content['videos'].append(item_path)
                elif ext in ['.gif']:
                    content['gifs'].append(item_path)
                elif ext not in ['.txt']:  # 排除文字文件
                    content['files'].append(item_path)
            
            # 排序文件列表
            content['images'].sort()
            content['videos'].sort()
            content['gifs'].sort()
            content['files'].sort()
            
            self.logger.info(f"載入活動 {campaign} 內容: "
                           f"文字={'是' if content['text'] else '否'}, "
                           f"圖片{len(content['images'])}個, "
                           f"影片{len(content['videos'])}個, "
                           f"GIF{len(content['gifs'])}個")
            
            return content
            
        except Exception as e:
            self.logger.error(f"載入活動內容失敗 {campaign}: {e}")
            return None
    
    def validate_campaign_content(self, campaign: str) -> Dict[str, Any]:
        """
        驗證活動內容的完整性
        
        Returns:
            Dict: 驗證結果
        """
        result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'content_summary': {}
        }
        
        try:
            content = self.load_campaign_content(campaign)
            
            if not content:
                result['errors'].append(f"無法載入活動 {campaign} 的內容")
                return result
            
            # 檢查是否有任何內容
            has_text = bool(content['text'])
            has_media = bool(content['images'] or content['videos'] or content['gifs'])
            
            if not has_text and not has_media:
                result['errors'].append("活動內容為空：沒有文字也沒有媒體文件")
                return result
            
            # 檢查文字內容
            if has_text:
                text_length = len(content['text'])
                if text_length > 4096:  # Telegram限制
                    result['warnings'].append(f"文字內容過長 ({text_length} 字符)，可能被截斷")
                result['content_summary']['text_length'] = text_length
            else:
                result['warnings'].append("沒有文字內容")
            
            # 檢查媒體文件
            for image_path in content['images']:
                size = os.path.getsize(image_path)
                if size > 10 * 1024 * 1024:  # 10MB
                    result['warnings'].append(f"圖片文件過大: {os.path.basename(image_path)} ({size // 1024 // 1024}MB)")
            
            for video_path in content['videos']:
                size = os.path.getsize(video_path)
                if size > 50 * 1024 * 1024:  # 50MB
                    result['warnings'].append(f"影片文件過大: {os.path.basename(video_path)} ({size // 1024 // 1024}MB)")
            
            # 設定內容摘要
            result['content_summary'] = {
                'has_text': has_text,
                'text_length': len(content['text']) if has_text else 0,
                'images_count': len(content['images']),
                'videos_count': len(content['videos']),
                'gifs_count': len(content['gifs']),
                'total_files': len(content['images']) + len(content['videos']) + len(content['gifs'])
            }
            
            result['valid'] = True
            
        except Exception as e:
            result['errors'].append(f"驗證過程發生錯誤: {e}")
        
        return result
    
    def list_available_campaigns(self) -> List[str]:
        """列出所有可用的活動"""
        return self.config.list_available_campaigns()
    
    def get_campaign_summary(self, campaign: str) -> Optional[str]:
        """
        獲取活動內容摘要
        
        Returns:
            str: 活動內容的簡短描述
        """
        try:
            validation = self.validate_campaign_content(campaign)
            
            if not validation['valid']:
                return f"活動 {campaign}: ❌ 無效內容"
            
            summary = validation['content_summary']
            parts = []
            
            if summary['has_text']:
                parts.append(f"文字({summary['text_length']}字)")
            
            if summary['images_count'] > 0:
                parts.append(f"圖片{summary['images_count']}個")
            
            if summary['videos_count'] > 0:
                parts.append(f"影片{summary['videos_count']}個")
            
            if summary['gifs_count'] > 0:
                parts.append(f"GIF{summary['gifs_count']}個")
            
            if not parts:
                return f"活動 {campaign}: ❌ 空內容"
            
            return f"活動 {campaign}: {', '.join(parts)}"
            
        except Exception as e:
            self.logger.error(f"獲取活動摘要失敗 {campaign}: {e}")
            return f"活動 {campaign}: ❌ 錯誤"
    
    def create_sample_content(self, campaign: str) -> bool:
        """
        創建範例內容文件
        
        Args:
            campaign: 活動名稱
            
        Returns:
            bool: 是否成功創建
        """
        try:
            campaign_path = self.config.get_content_path(campaign)
            os.makedirs(campaign_path, exist_ok=True)
            
            # 創建範例文字文件
            text_path = os.path.join(campaign_path, 'message.txt')
            if not os.path.exists(text_path):
                sample_text = f"""🚀 這是活動 {campaign} 的範例廣播內容

✨ 您可以編輯這個文件來自定義廣播內容
📁 在同一目錄下放置圖片、影片或GIF文件
🎯 支援的格式：
   • 圖片：.jpg, .png, .webp
   • 影片：.mp4, .avi, .mov
   • 動圖：.gif

💡 提示：刪除這個範例文字，加入您自己的內容！"""
                
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(sample_text)
                
                self.logger.info(f"已創建活動 {campaign} 的範例內容")
                return True
            
            return True
            
        except Exception as e:
            self.logger.error(f"創建範例內容失敗 {campaign}: {e}")
            return False

class BroadcastSender:
    """廣播發送引擎"""
    
    def __init__(self, client_manager: TelegramClientManager, config_manager: ConfigManager, content_loader: ContentLoader):
        self.client_manager = client_manager
        self.config = config_manager
        self.content_loader = content_loader
        self.client = client_manager.get_client()
        self.logger = logging.getLogger(__name__)
        
        # 發送配置
        self.send_delay = self.config.broadcast_config.get('broadcast_delay', 5)
        self.max_retries = self.config.broadcast_config.get('max_retries', 3)
    
    async def send_campaign_broadcast(self, campaign: str, target_groups: List[int] = None) -> Tuple[int, int, List[str], List[int], List[int]]:
        """
        發送活動廣播到指定群組
        
        Args:
            campaign: 活動名稱
            target_groups: 目標群組列表，如果為None則使用配置中的群組
            
        Returns:
            Tuple[int, int, List[str], List[int], List[int]]: (成功數量, 總數量, 錯誤列表, 成功群組列表, 失敗群組列表)
        """
        try:
            # 確保客戶端已認證
            if not await self.client_manager.is_authorized():
                error_msg = "Telegram客戶端未認證"
                self.logger.error(error_msg)
                return 0, 0, [error_msg]
            
            # 載入活動內容
            content = self.content_loader.load_campaign_content(campaign)
            if not content:
                error_msg = f"無法載入活動 {campaign} 的內容"
                self.logger.error(error_msg)
                return 0, 0, [error_msg]
            
            # 驗證內容
            validation = self.content_loader.validate_campaign_content(campaign)
            if not validation['valid']:
                error_msg = f"活動 {campaign} 內容無效: {', '.join(validation['errors'])}"
                self.logger.error(error_msg)
                return 0, 0, [error_msg]
            
            # 獲取目標群組
            if target_groups is None:
                target_groups = self.config.get_target_groups()
            
            if not target_groups:
                error_msg = "沒有設定目標群組"
                self.logger.warning(error_msg)
                return 0, 0, [error_msg]
            
            self.logger.info(f"開始廣播活動 {campaign} 到 {len(target_groups)} 個群組")
            
            # 發送到各個群組
            success_count = 0
            errors = []
            success_groups = []
            failed_groups = []
            
            for i, group_id in enumerate(target_groups):
                try:
                    self.logger.debug(f"發送到群組 {group_id} ({i+1}/{len(target_groups)})")
                    
                    # 發送內容到群組
                    success = await self._send_content_to_group(group_id, content)
                    
                    if success:
                        success_count += 1
                        success_groups.append(group_id)
                        self.logger.debug(f"成功發送到群組 {group_id}")
                    else:
                        failed_groups.append(group_id)
                        errors.append(f"群組 {group_id}: 發送失敗")
                        self.logger.warning(f"發送到群組 {group_id} 失敗")
                    
                    # 發送間隔延遲
                    if i < len(target_groups) - 1:  # 最後一個不需要延遲
                        await asyncio.sleep(self.send_delay)
                
                except Exception as e:
                    failed_groups.append(group_id)
                    error_msg = f"群組 {group_id}: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(f"發送到群組 {group_id} 時發生錯誤: {e}")
            
            # 記錄廣播歷史
            self.config.add_broadcast_history(
                campaign=campaign,
                groups_count=len(target_groups),
                success_count=success_count,
                errors=errors
            )
            
            self.logger.info(f"廣播完成: {success_count}/{len(target_groups)} 成功")
            
            return success_count, len(target_groups), errors, success_groups, failed_groups
            
        except Exception as e:
            error_msg = f"廣播過程發生嚴重錯誤: {e}"
            self.logger.error(error_msg)
            return 0, 0, [error_msg], [], []
    
    async def _send_content_to_group(self, group_id: int, content: Dict[str, Any]) -> bool:
        """
        發送內容到單個群組
        
        Args:
            group_id: 群組ID
            content: 內容字典
            
        Returns:
            bool: 是否發送成功
        """
        try:
            # 重試機制
            for attempt in range(self.max_retries):
                try:
                    text_content = content.get('text', '')
                    has_sent_text_with_media = False
                    
                    # 優先發送圖片配文字
                    if content['images']:
                        # 第一張圖片攜帶文字
                        first_image = content['images'][0]
                        await self.client.send_file(group_id, first_image, caption=text_content)
                        has_sent_text_with_media = True
                        await asyncio.sleep(1)
                        
                        # 其餘圖片單獨發送
                        for image_path in content['images'][1:]:
                            await self.client.send_file(group_id, image_path)
                            await asyncio.sleep(1)
                    
                    # 發送GIF，如果還沒發送文字則攜帶文字
                    if content['gifs']:
                        if not has_sent_text_with_media and text_content:
                            # 第一個GIF攜帶文字
                            first_gif = content['gifs'][0]
                            await self.client.send_file(group_id, first_gif, caption=text_content)
                            has_sent_text_with_media = True
                            
                            # 其餘GIF單獨發送
                            for gif_path in content['gifs'][1:]:
                                await self.client.send_file(group_id, gif_path)
                                await asyncio.sleep(1)
                        else:
                            # 所有GIF單獨發送
                            for gif_path in content['gifs']:
                                await self.client.send_file(group_id, gif_path)
                                await asyncio.sleep(1)
                    
                    # 發送影片，如果還沒發送文字則攜帶文字
                    if content['videos']:
                        if not has_sent_text_with_media and text_content:
                            # 第一個影片攜帶文字
                            first_video = content['videos'][0]
                            await self.client.send_file(group_id, first_video, caption=text_content)
                            has_sent_text_with_media = True
                            
                            # 其餘影片單獨發送
                            for video_path in content['videos'][1:]:
                                await self.client.send_file(group_id, video_path)
                                await asyncio.sleep(2)  # 影片需要更長延遲
                        else:
                            # 所有影片單獨發送
                            for video_path in content['videos']:
                                await self.client.send_file(group_id, video_path)
                                await asyncio.sleep(2)  # 影片需要更長延遲
                    
                    # 發送其他文件，如果還沒發送文字則攜帶文字
                    if content['files']:
                        if not has_sent_text_with_media and text_content:
                            # 第一個文件攜帶文字
                            first_file = content['files'][0]
                            await self.client.send_file(group_id, first_file, caption=text_content)
                            has_sent_text_with_media = True
                            
                            # 其餘文件單獨發送
                            for file_path in content['files'][1:]:
                                await self.client.send_file(group_id, file_path)
                                await asyncio.sleep(1)
                        else:
                            # 所有文件單獨發送
                            for file_path in content['files']:
                                await self.client.send_file(group_id, file_path)
                                await asyncio.sleep(1)
                    
                    # 如果只有文字沒有媒體，單獨發送文字
                    if text_content and not has_sent_text_with_media:
                        await self.client.send_message(group_id, text_content)
                    
                    return True
                    
                except Exception as e:
                    self.logger.warning(f"第 {attempt + 1} 次嘗試發送到群組 {group_id} 失敗: {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # 指數退避
                    else:
                        raise e
            
            return False
            
        except Exception as e:
            self.logger.error(f"發送內容到群組 {group_id} 失敗: {e}")
            return False

class BroadcastManager:
    """廣播管理器"""
    
    def __init__(self, client_manager: TelegramClientManager, config_manager: ConfigManager):
        self.client_manager = client_manager
        self.config = config_manager
        self.content_loader = ContentLoader(config_manager)
        self.sender = BroadcastSender(client_manager, config_manager, self.content_loader)
        self.logger = logging.getLogger(__name__)
        
        # 廣播狀態
        self.is_broadcasting = False
        self.current_broadcast = None
    
    async def execute_broadcast(self, campaign: str, target_groups: List[int] = None) -> Dict[str, Any]:
        """
        執行廣播
        
        Args:
            campaign: 活動名稱
            target_groups: 目標群組列表
            
        Returns:
            Dict: 廣播結果
        """
        try:
            if self.is_broadcasting:
                return {
                    'success': False,
                    'error': '已有廣播正在進行中',
                    'success_count': 0,
                    'total_count': 0,
                    'errors': [],
                    'success_groups': [],
                    'failed_groups': []
                }
            
            self.is_broadcasting = True
            self.current_broadcast = {
                'campaign': campaign,
                'start_time': datetime.now(),
                'status': 'running'
            }
            
            try:
                # 執行廣播
                success_count, total_count, errors, success_groups, failed_groups = await self.sender.send_campaign_broadcast(
                    campaign, target_groups
                )
                
                result = {
                    'success': True,
                    'campaign': campaign,
                    'success_count': success_count,
                    'total_count': total_count,
                    'success_rate': (success_count / total_count * 100) if total_count > 0 else 0,
                    'errors': errors,
                    'success_groups': success_groups,
                    'failed_groups': failed_groups,
                    'start_time': self.current_broadcast['start_time'],
                    'end_time': datetime.now()
                }
                
                # 計算執行時間
                duration = result['end_time'] - result['start_time']
                result['duration_seconds'] = duration.total_seconds()
                
                self.logger.info(f"廣播完成: {campaign}, 成功率: {result['success_rate']:.1f}%")
                
                return result
                
            finally:
                self.is_broadcasting = False
                self.current_broadcast = None
                
        except Exception as e:
            self.is_broadcasting = False
            self.current_broadcast = None
            self.logger.error(f"執行廣播時發生錯誤: {e}")
            
            return {
                'success': False,
                'error': f'執行廣播時發生錯誤: {e}',
                'success_count': 0,
                'total_count': 0,
                'errors': [str(e)],
                'success_groups': [],
                'failed_groups': []
            }
    
    def get_available_campaigns(self) -> List[str]:
        """獲取可用的活動列表"""
        return self.content_loader.list_available_campaigns()
    
    def get_campaign_summary(self, campaign: str) -> str:
        """獲取活動摘要"""
        return self.content_loader.get_campaign_summary(campaign)
    
    def validate_campaign(self, campaign: str) -> Dict[str, Any]:
        """驗證活動內容"""
        return self.content_loader.validate_campaign_content(campaign)
    
    def get_broadcast_status(self) -> Dict[str, Any]:
        """獲取當前廣播狀態"""
        return {
            'is_broadcasting': self.is_broadcasting,
            'current_broadcast': self.current_broadcast
        }
    
    def get_broadcast_statistics(self) -> Dict[str, Any]:
        """獲取廣播統計數據"""
        try:
            history = self.config.get_broadcast_history()
            
            if not history:
                return {
                    'total_broadcasts': 0,
                    'total_success_rate': 0,
                    'campaign_stats': {},
                    'recent_activity': []
                }
            
            # 總體統計
            total_broadcasts = len(history)
            total_groups_targeted = sum(h.get('groups_count', 0) for h in history)
            total_successful = sum(h.get('success_count', 0) for h in history)
            overall_success_rate = (total_successful / total_groups_targeted * 100) if total_groups_targeted > 0 else 0
            
            # 按活動統計
            campaign_stats = {}
            for record in history:
                campaign = record.get('campaign', 'Unknown')
                if campaign not in campaign_stats:
                    campaign_stats[campaign] = {
                        'count': 0,
                        'success_count': 0,
                        'total_count': 0,
                        'success_rate': 0
                    }
                
                stats = campaign_stats[campaign]
                stats['count'] += 1
                stats['success_count'] += record.get('success_count', 0)
                stats['total_count'] += record.get('groups_count', 0)
            
            # 計算各活動成功率
            for campaign, stats in campaign_stats.items():
                if stats['total_count'] > 0:
                    stats['success_rate'] = stats['success_count'] / stats['total_count'] * 100
            
            # 最近活動
            recent_activity = history[-10:] if len(history) > 10 else history
            
            return {
                'total_broadcasts': total_broadcasts,
                'total_groups_targeted': total_groups_targeted,
                'total_successful': total_successful,
                'total_success_rate': overall_success_rate,
                'campaign_stats': campaign_stats,
                'recent_activity': recent_activity
            }
            
        except Exception as e:
            self.logger.error(f"獲取廣播統計失敗: {e}")
            return {
                'total_broadcasts': 0,
                'total_success_rate': 0,
                'campaign_stats': {},
                'recent_activity': [],
                'error': str(e)
            }
    
    def create_sample_campaigns(self) -> bool:
        """創建範例活動內容"""
        try:
            campaigns = ['A', 'B', 'C', 'D', 'E']
            success_count = 0
            
            for campaign in campaigns:
                if self.content_loader.create_sample_content(campaign):
                    success_count += 1
            
            self.logger.info(f"創建了 {success_count}/{len(campaigns)} 個範例活動")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"創建範例活動失敗: {e}")
            return False
