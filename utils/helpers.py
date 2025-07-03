"""
輔助函數 - 通用工具函數
"""
import os
import json
import asyncio
import functools
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path


def safe_json_load(file_path: str, default_value: Any = None) -> Any:
    """安全載入JSON文件"""
    try:
        if not os.path.exists(file_path):
            return default_value
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"載入JSON文件失敗 {file_path}: {e}")
        return default_value


def safe_json_save(file_path: str, data: Any, backup: bool = True) -> bool:
    """安全保存JSON文件"""
    try:
        # 創建備份
        if backup and os.path.exists(file_path):
            backup_path = f"{file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(file_path, backup_path)
        
        # 確保目錄存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 保存文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"保存JSON文件失敗 {file_path}: {e}")
        return False


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def format_duration(seconds: float) -> str:
    """格式化時間長度"""
    if seconds < 60:
        return f"{seconds:.1f} 秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} 分鐘"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} 小時"


def format_timestamp(timestamp: str) -> str:
    """格式化時間戳"""
    try:
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp
        
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days} 天前"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} 小時前"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} 分鐘前"
        else:
            return "剛剛"
    except:
        return str(timestamp)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """截斷文字"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def clean_filename(filename: str) -> str:
    """清理文件名，移除非法字符"""
    import re
    # 移除或替換非法字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 移除前後空格
    filename = filename.strip()
    # 確保不為空
    if not filename:
        filename = "unnamed"
    return filename


def ensure_directory(path: str) -> bool:
    """確保目錄存在"""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        print(f"創建目錄失敗 {path}: {e}")
        return False


def get_file_info(file_path: str) -> Optional[Dict[str, Any]]:
    """獲取文件信息"""
    try:
        if not os.path.exists(file_path):
            return None
        
        stat = os.stat(file_path)
        
        return {
            'name': os.path.basename(file_path),
            'size': stat.st_size,
            'size_formatted': format_file_size(stat.st_size),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'modified_formatted': format_timestamp(datetime.fromtimestamp(stat.st_mtime)),
            'extension': os.path.splitext(file_path)[1].lower(),
            'is_file': os.path.isfile(file_path),
            'is_directory': os.path.isdir(file_path)
        }
    except Exception as e:
        print(f"獲取文件信息失敗 {file_path}: {e}")
        return None


def retry_on_exception(retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """重試裝飾器"""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < retries - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < retries - 1:
                        import time
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise last_exception
        
        # 檢查是否為異步函數
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def rate_limit(calls: int = 10, period: float = 60.0):
    """速率限制裝飾器"""
    def decorator(func):
        calls_times = []
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            now = datetime.now().timestamp()
            
            # 清理過期的調用記錄
            calls_times[:] = [t for t in calls_times if now - t < period]
            
            # 檢查是否超過限制
            if len(calls_times) >= calls:
                sleep_time = period - (now - calls_times[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
            
            # 記錄調用時間
            calls_times.append(now)
            
            return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            now = datetime.now().timestamp()
            
            # 清理過期的調用記錄
            calls_times[:] = [t for t in calls_times if now - t < period]
            
            # 檢查是否超過限制
            if len(calls_times) >= calls:
                sleep_time = period - (now - calls_times[0])
                if sleep_time > 0:
                    import time
                    time.sleep(sleep_time)
            
            # 記錄調用時間
            calls_times.append(now)
            
            return func(*args, **kwargs)
        
        # 檢查是否為異步函數
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def validate_phone_number(phone: str) -> bool:
    """驗證電話號碼格式"""
    import re
    # 支援國際格式，如 +886912345678
    pattern = r'^\+[1-9]\d{1,14}$'
    return bool(re.match(pattern, phone))


def validate_time_format(time_str: str) -> bool:
    """驗證時間格式 (HH:MM)"""
    import re
    pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
    return bool(re.match(pattern, time_str))


def normalize_time_format(time_str: str) -> str:
    """標準化時間格式"""
    try:
        time_str = time_str.strip()
        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 2:
                hour, minute = parts
                hour = int(hour)
                minute = int(minute)
                return f"{hour:02d}:{minute:02d}"
    except:
        pass
    
    return time_str


def get_next_schedule_time(schedules: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
    """獲取下一個排程時間"""
    try:
        if not schedules:
            return None
        
        now = datetime.now()
        today = now.date()
        current_time = now.time()
        
        # 找到今天剩餘的排程
        remaining_today = []
        for schedule in schedules:
            try:
                hour, minute = map(int, schedule['time'].split(':'))
                schedule_time = datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute)).time()
                
                if schedule_time > current_time:
                    next_datetime = datetime.combine(today, schedule_time)
                    remaining_today.append({
                        'datetime': next_datetime,
                        'schedule': schedule,
                        'is_today': True
                    })
            except ValueError:
                continue
        
        if remaining_today:
            remaining_today.sort(key=lambda x: x['datetime'])
            return remaining_today[0]
        
        # 找到明天最早的排程
        tomorrow = today + timedelta(days=1)
        tomorrow_schedules = []
        
        for schedule in schedules:
            try:
                hour, minute = map(int, schedule['time'].split(':'))
                schedule_time = datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute)).time()
                next_datetime = datetime.combine(tomorrow, schedule_time)
                tomorrow_schedules.append({
                    'datetime': next_datetime,
                    'schedule': schedule,
                    'is_today': False
                })
            except ValueError:
                continue
        
        if tomorrow_schedules:
            tomorrow_schedules.sort(key=lambda x: x['datetime'])
            return tomorrow_schedules[0]
        
        return None
        
    except Exception as e:
        print(f"獲取下一個排程時間失敗: {e}")
        return None


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """將列表分塊"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


async def run_in_executor(func: Callable, *args, **kwargs):
    """在執行器中運行同步函數"""
    import concurrent.futures
    
    loop = asyncio.get_event_loop()
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        if kwargs:
            # 如果有關鍵字參數，使用 functools.partial
            partial_func = functools.partial(func, **kwargs)
            return await loop.run_in_executor(executor, partial_func, *args)
        else:
            return await loop.run_in_executor(executor, func, *args)