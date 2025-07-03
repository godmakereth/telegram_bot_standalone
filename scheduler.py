"""
自動排程系統 - 負責定時執行廣播任務
"""
import asyncio
import json
import logging
import os
from datetime import datetime, time, timedelta
from typing import Dict, List, Any, Optional
import threading

from config import ConfigManager
from broadcast_manager import BroadcastManager


class BroadcastScheduler:
    """廣播排程器"""
    
    def __init__(self, config_manager: ConfigManager, broadcast_manager: BroadcastManager):
        self.config = config_manager
        self.broadcast_manager = broadcast_manager
        self.logger = logging.getLogger(__name__)
        
        # 排程狀態
        self.is_running = False
        self.scheduler_task = None
        self.next_execution = None
        
        # 統計信息
        self.executions_today = 0
        self.last_execution = None
        self.last_execution_result = None
    
    async def start_scheduler(self):
        """啟動排程器"""
        if self.is_running:
            self.logger.warning("排程器已在運行中")
            return
        
        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        self.logger.info("排程器已啟動")
    
    async def stop_scheduler(self):
        """停止排程器"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("排程器已停止")
    
    async def _scheduler_loop(self):
        """排程主迴圈"""
        try:
            while self.is_running:
                try:
                    # 檢查是否啟用排程
                    if not self.config.is_schedule_enabled():
                        await asyncio.sleep(60)  # 每分鐘檢查一次
                        continue
                    
                    # 獲取當前時間
                    now = datetime.now()
                    current_time = now.strftime('%H:%M')
                    
                    # 檢查是否有需要執行的排程
                    schedules = self.config.get_schedules()
                    
                    for schedule in schedules:
                        schedule_time = schedule['time']
                        campaign = schedule['campaign']
                        
                        # 檢查是否到了執行時間 (精確到分鐘)
                        if current_time == schedule_time:
                            # 檢查今天是否已經執行過這個排程
                            execution_key = f"{now.strftime('%Y-%m-%d')}_{schedule_time}_{campaign}"
                            
                            if not self._is_already_executed_today(execution_key):
                                self.logger.info(f"執行排程廣播: {schedule_time} - 活動 {campaign}")
                                
                                # 執行廣播
                                success = await self._execute_scheduled_broadcast(schedule)
                                
                                # 只有在廣播成功時才記錄執行
                                if success:
                                    self._mark_executed(execution_key)
                                    self.logger.info(f"排程廣播成功完成並記錄: {schedule_time} - 活動 {campaign}")
                                else:
                                    self.logger.warning(f"排程廣播失敗，未記錄執行: {schedule_time} - 活動 {campaign}")
                    
                    # 更新下次執行時間
                    self._update_next_execution()
                    
                    # 等待到下一分鐘
                    await asyncio.sleep(60)
                    
                except Exception as e:
                    self.logger.error(f"排程迴圈發生錯誤: {e}")
                    await asyncio.sleep(60)  # 錯誤後等待1分鐘再繼續
                    
        except asyncio.CancelledError:
            self.logger.info("排程迴圈被取消")
        except Exception as e:
            self.logger.error(f"排程迴圈嚴重錯誤: {e}")
        finally:
            self.is_running = False
    
    async def _execute_scheduled_broadcast(self, schedule: Dict[str, str]) -> bool:
        """執行排程廣播"""
        try:
            campaign = schedule['campaign']
            schedule_time = schedule['time']
            
            self.logger.info(f"開始執行排程廣播: {schedule_time} - 活動 {campaign}")
            
            # 檢查廣播管理器狀態
            status = self.broadcast_manager.get_broadcast_status()
            if status['is_broadcasting']:
                self.logger.warning(f"已有廣播正在進行，跳過排程 {schedule_time} - {campaign}")
                return False
            
            # 執行廣播
            result = await self.broadcast_manager.execute_broadcast(campaign)
            
            # 記錄結果
            self.last_execution = datetime.now()
            self.last_execution_result = result
            self.executions_today += 1
            
            # 記錄日誌
            if result['success']:
                success_rate = result['success_rate']
                self.logger.info(f"排程廣播完成: {campaign}, 成功率: {success_rate:.1f}%")
                
                # 發送結果到控制群組
                await self._send_schedule_result_to_control_group(schedule, result)
                return True
            else:
                self.logger.error(f"排程廣播失敗: {campaign} - {result.get('error', '未知錯誤')}")
                
                # 發送失敗通知到控制群組
                await self._send_schedule_error_to_control_group(schedule, result)
                return False
                
        except Exception as e:
            self.logger.error(f"執行排程廣播時發生錯誤: {e}")
            
            # 發送錯誤通知到控制群組
            await self._send_schedule_error_to_control_group(
                schedule, 
                {'success': False, 'error': str(e)}
            )
            return False
    
    async def _send_schedule_result_to_control_group(self, schedule: Dict[str, str], result: Dict[str, Any]):
        """發送排程執行結果到控制群組"""
        try:
            control_group = self.config.get_control_group()
            if control_group == 0:
                return
            
            client = self.broadcast_manager.client_manager.get_client()
            if not client or not await self.broadcast_manager.client_manager.is_authorized():
                return
            
            campaign = schedule['campaign']
            schedule_time = schedule['time']
            success_rate = result['success_rate']
            
            # 選擇表情符號
            if success_rate >= 90:
                status_icon = "🎉"
            elif success_rate >= 70:
                status_icon = "⚠️"
            else:
                status_icon = "❌"
            
            # 格式化執行時間
            duration = result.get('duration_seconds', 0)
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
            
            # 獲取當前時間
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            message = f"""
{status_icon} **排程廣播完成**

📅 **排程資訊:**
• 排程時間: `{schedule_time}`
• 活動名稱: `{campaign}`
• 執行時間: `{current_time}`

📊 **執行統計:**
• 成功發送: `{result['success_count']}` 個群組
• 失敗發送: `{result['total_count'] - result['success_count']}` 個群組
• 總目標群組: `{result['total_count']}` 個
• 成功率: `{success_rate:.1f}%`
• 總執行時間: `{duration_str}`
• 平均速度: `{avg_speed:.1f}` 群組/秒

🤖 **自動排程執行**
            """
            
            # 顯示成功群組詳情
            if result.get('success_groups'):
                success_groups = result['success_groups']
                message += f"\n✅ **成功群組 ({len(success_groups)} 個):**\n"
                
                if len(success_groups) <= 6:
                    for i, group_id in enumerate(success_groups, 1):
                        message += f"  {i}. `{group_id}`\n"
                else:
                    for i, group_id in enumerate(success_groups[:6], 1):
                        message += f"  {i}. `{group_id}`\n"
                    message += f"  ... 還有 {len(success_groups) - 6} 個群組\n"
            
            # 顯示失敗群組詳情
            if result.get('failed_groups'):
                failed_groups = result['failed_groups']
                message += f"\n❌ **失敗群組 ({len(failed_groups)} 個):**\n"
                
                if len(failed_groups) <= 6:
                    for i, group_id in enumerate(failed_groups, 1):
                        message += f"  {i}. `{group_id}`\n"
                else:
                    for i, group_id in enumerate(failed_groups[:6], 1):
                        message += f"  {i}. `{group_id}`\n"
                    message += f"  ... 還有 {len(failed_groups) - 6} 個群組\n"
            
            # 添加錯誤資訊和建議
            if result.get('errors'):
                message += f"\n⚠️ **錯誤記錄 ({len(result['errors'])} 項):**\n"
                for i, error in enumerate(result['errors'][:3], 1):
                    message += f"  {i}. {error}\n"
                if len(result['errors']) > 3:
                    message += f"  ... 還有 {len(result['errors']) - 3} 個錯誤\n"
            
            # 添加排程建議
            if result['total_count'] - result['success_count'] > 0:
                message += f"\n💡 **建議檢查:**\n"
                message += f"• 失敗群組是否需要重新加入機器人\n"
                message += f"• 檢查網路連接和機器人權限\n"
            
            await client.send_message(control_group, message.strip())
            
        except Exception as e:
            self.logger.error(f"發送排程結果到控制群組失敗: {e}")
    
    async def _send_schedule_error_to_control_group(self, schedule: Dict[str, str], result: Dict[str, Any]):
        """發送排程錯誤到控制群組"""
        try:
            control_group = self.config.get_control_group()
            if control_group == 0:
                return
            
            client = self.broadcast_manager.client_manager.get_client()
            if not client or not await self.broadcast_manager.client_manager.is_authorized():
                return
            
            campaign = schedule['campaign']
            schedule_time = schedule['time']
            error = result.get('error', '未知錯誤')
            
            message = f"""
❌ **排程廣播失敗**

🕐 排程時間: `{schedule_time}`
📁 活動: `{campaign}`
🚫 錯誤: {error}

請檢查系統狀態和活動內容
            """
            
            await client.send_message(control_group, message.strip())
            
        except Exception as e:
            self.logger.error(f"發送排程錯誤到控制群組失敗: {e}")
    
    def _is_already_executed_today(self, execution_key: str) -> bool:
        """檢查今天是否已經執行過指定的排程"""
        executed_records = self._load_execution_records()
        return execution_key in executed_records
    
    def _mark_executed(self, execution_key: str):
        """標記排程已執行"""
        executed_records = self._load_execution_records()
        executed_records.add(execution_key)
        self._save_execution_records(executed_records)
        
        # 清理舊的執行記錄 (保留今天的)
        today = datetime.now().strftime('%Y-%m-%d')
        current_records = {key for key in executed_records if key.startswith(today)}
        self._save_execution_records(current_records)
    
    def _load_execution_records(self) -> set:
        """從檔案載入執行記錄"""
        execution_file = "data/scheduler_execution_records.json"
        today = datetime.now().strftime('%Y-%m-%d')
        
        try:
            if os.path.exists(execution_file):
                with open(execution_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 只載入今天的記錄
                    today_records = {key for key in data.get('executed_today', []) if key.startswith(today)}
                    return today_records
        except Exception as e:
            self.logger.warning(f"載入執行記錄失敗: {e}")
        
        return set()
    
    def _save_execution_records(self, executed_records: set):
        """儲存執行記錄到檔案"""
        execution_file = "data/scheduler_execution_records.json"
        
        try:
            # 確保目錄存在
            os.makedirs(os.path.dirname(execution_file), exist_ok=True)
            
            data = {
                'executed_today': list(executed_records),
                'last_updated': datetime.now().isoformat()
            }
            
            with open(execution_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"儲存執行記錄失敗: {e}")
    
    def _update_next_execution(self):
        """更新下次執行時間"""
        try:
            if not self.config.is_schedule_enabled():
                self.next_execution = None
                return
            
            schedules = self.config.get_schedules()
            if not schedules:
                self.next_execution = None
                return
            
            now = datetime.now()
            today = now.date()
            current_time = now.time()
            
            # 找到今天剩餘的排程
            remaining_today = []
            for schedule in schedules:
                schedule_time_str = schedule['time']
                try:
                    hour, minute = map(int, schedule_time_str.split(':'))
                    schedule_time = time(hour, minute)
                    
                    if schedule_time > current_time:
                        next_datetime = datetime.combine(today, schedule_time)
                        remaining_today.append((next_datetime, schedule))
                except ValueError:
                    continue
            
            if remaining_today:
                # 找到最近的執行時間
                remaining_today.sort(key=lambda x: x[0])
                self.next_execution = remaining_today[0]
            else:
                # 找到明天最早的排程
                tomorrow = today + timedelta(days=1)
                tomorrow_schedules = []
                
                for schedule in schedules:
                    schedule_time_str = schedule['time']
                    try:
                        hour, minute = map(int, schedule_time_str.split(':'))
                        schedule_time = time(hour, minute)
                        next_datetime = datetime.combine(tomorrow, schedule_time)
                        tomorrow_schedules.append((next_datetime, schedule))
                    except ValueError:
                        continue
                
                if tomorrow_schedules:
                    tomorrow_schedules.sort(key=lambda x: x[0])
                    self.next_execution = tomorrow_schedules[0]
                else:
                    self.next_execution = None
                    
        except Exception as e:
            self.logger.error(f"更新下次執行時間失敗: {e}")
            self.next_execution = None
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """獲取排程器狀態"""
        return {
            'is_running': self.is_running,
            'is_enabled': self.config.is_schedule_enabled(),
            'next_execution': self.next_execution,
            'executions_today': self.executions_today,
            'last_execution': self.last_execution,
            'last_execution_result': self.last_execution_result,
            'total_schedules': len(self.config.get_schedules())
        }
    
    def get_next_execution_info(self) -> Optional[str]:
        """獲取下次執行信息"""
        if not self.next_execution:
            return None
        
        next_datetime, schedule = self.next_execution
        campaign = schedule['campaign']
        
        # 計算時間差
        now = datetime.now()
        time_diff = next_datetime - now
        
        if time_diff.days > 0:
            return f"明天 {next_datetime.strftime('%H:%M')} - 活動 {campaign}"
        else:
            hours, remainder = divmod(time_diff.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            if hours > 0:
                return f"{hours}小時{minutes}分鐘後 ({next_datetime.strftime('%H:%M')}) - 活動 {campaign}"
            else:
                return f"{minutes}分鐘後 ({next_datetime.strftime('%H:%M')}) - 活動 {campaign}"