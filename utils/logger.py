"""
日誌系統 - 統一的日誌管理
"""
import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path


class LoggerManager:
    """日誌管理器"""
    
    def __init__(self, base_path: str = None):
        self.base_path = base_path or os.getcwd()
        self.logs_path = os.path.join(self.base_path, "data", "logs")
        
        # 確保日誌目錄存在
        os.makedirs(self.logs_path, exist_ok=True)
        
        # 設定日誌格式
        self.log_format = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 初始化日誌系統
        self._setup_loggers()
    
    def _setup_loggers(self):
        """設定各種日誌記錄器"""
        
        # 主應用程式日誌
        self._setup_main_logger()
        
        # 廣播日誌
        self._setup_broadcast_logger()
        
        # 錯誤日誌
        self._setup_error_logger()
        
        # 排程日誌
        self._setup_scheduler_logger()
    
    def _setup_main_logger(self):
        """設定主日誌記錄器"""
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        
        # 清除現有的處理器
        logger.handlers.clear()
        
        # 檔案處理器
        file_handler = RotatingFileHandler(
            os.path.join(self.logs_path, 'bot.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(self.log_format)
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)
        
        # 控制台處理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self.log_format)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)
    
    def _setup_broadcast_logger(self):
        """設定廣播日誌記錄器"""
        logger = logging.getLogger('broadcast')
        logger.setLevel(logging.INFO)
        
        file_handler = RotatingFileHandler(
            os.path.join(self.logs_path, 'broadcast.log'),
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setFormatter(self.log_format)
        logger.addHandler(file_handler)
    
    def _setup_error_logger(self):
        """設定錯誤日誌記錄器"""
        logger = logging.getLogger('error')
        logger.setLevel(logging.ERROR)
        
        file_handler = RotatingFileHandler(
            os.path.join(self.logs_path, 'error.log'),
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(self.log_format)
        logger.addHandler(file_handler)
    
    def _setup_scheduler_logger(self):
        """設定排程日誌記錄器"""
        logger = logging.getLogger('scheduler')
        logger.setLevel(logging.INFO)
        
        file_handler = RotatingFileHandler(
            os.path.join(self.logs_path, 'scheduler.log'),
            maxBytes=2*1024*1024,  # 2MB
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setFormatter(self.log_format)
        logger.addHandler(file_handler)
    
    def get_logger(self, name: str = None) -> logging.Logger:
        """獲取指定名稱的日誌記錄器"""
        return logging.getLogger(name)
    
    def log_broadcast_event(self, campaign: str, event: str, details: str = None):
        """記錄廣播事件"""
        broadcast_logger = logging.getLogger('broadcast')
        message = f"[{campaign}] {event}"
        if details:
            message += f" - {details}"
        broadcast_logger.info(message)
    
    def log_error_event(self, error: Exception, context: str = None):
        """記錄錯誤事件"""
        error_logger = logging.getLogger('error')
        message = f"錯誤: {str(error)}"
        if context:
            message = f"[{context}] {message}"
        error_logger.error(message, exc_info=True)
    
    def log_scheduler_event(self, event: str, details: str = None):
        """記錄排程事件"""
        scheduler_logger = logging.getLogger('scheduler')
        message = f"排程器: {event}"
        if details:
            message += f" - {details}"
        scheduler_logger.info(message)
    
    def get_recent_logs(self, log_type: str = 'main', lines: int = 100) -> list:
        """獲取最近的日誌記錄"""
        try:
            log_files = {
                'main': 'bot.log',
                'broadcast': 'broadcast.log',
                'error': 'error.log',
                'scheduler': 'scheduler.log'
            }
            
            log_file = log_files.get(log_type, 'bot.log')
            log_path = os.path.join(self.logs_path, log_file)
            
            if not os.path.exists(log_path):
                return []
            
            with open(log_path, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
            
            # 返回最後N行
            return all_lines[-lines:] if len(all_lines) > lines else all_lines
            
        except Exception as e:
            logging.error(f"讀取日誌文件失敗: {e}")
            return []
    
    def clean_old_logs(self, days: int = 30):
        """清理舊日誌文件"""
        try:
            cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            for file_path in Path(self.logs_path).glob('*.log*'):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    logging.info(f"清理舊日誌文件: {file_path}")
                    
        except Exception as e:
            logging.error(f"清理舊日誌失敗: {e}")


# 全局日誌管理器實例
_logger_manager = None

def get_logger_manager(base_path: str = None) -> LoggerManager:
    """獲取全局日誌管理器實例"""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = LoggerManager(base_path)
    return _logger_manager

def setup_logging(base_path: str = None):
    """設定日誌系統"""
    get_logger_manager(base_path)