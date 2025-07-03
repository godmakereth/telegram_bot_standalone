
"""
配置管理與驗證 - 統一管理所有配置文件並提供驗證功能
"""
import json
import os
import re
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

class ConfigValidator:
    """配置驗證器"""
    
    @staticmethod
    def validate_time_format(time_str: str) -> bool:
        """驗證時間格式 (HH:MM)"""
        pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
        return bool(re.match(pattern, time_str))
    
    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """驗證電話號碼格式"""
        # 支援國際格式，如 +886912345678
        pattern = r'^\+[1-9]\d{1,14}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def validate_api_id(api_id: str) -> bool:
        """驗證API ID格式"""
        try:
            api_id_int = int(api_id)
            return 1000000 <= api_id_int <= 99999999  # Telegram API ID範圍
        except ValueError:
            return False
    
    @staticmethod
    def validate_api_hash(api_hash: str) -> bool:
        """驗證API Hash格式"""
        # Telegram API Hash通常是32位十六進制字符串
        pattern = r'^[a-fA-F0-9]{32}$'
        return bool(re.match(pattern, api_hash))
    
    @staticmethod
    def validate_campaign_name(campaign: str) -> bool:
        """驗證活動名稱"""
        # 只允許字母、數字、下劃線，1-10個字符
        pattern = r'^[A-Za-z0-9_]{1,10}$'
        return bool(re.match(pattern, campaign))
    
    @staticmethod
    def validate_group_id(group_id: int) -> bool:
        """驗證群組ID"""
        # Telegram群組ID通常是負數，範圍很大
        return isinstance(group_id, int) and group_id != 0
    
    @staticmethod
    def validate_schedule(schedule: Dict[str, str]) -> Tuple[bool, Optional[str]]:
        """驗證排程配置"""
        if not isinstance(schedule, dict):
            return False, "排程必須是字典格式"
        
        if "time" not in schedule:
            return False, "排程缺少時間欄位"
        
        if "campaign" not in schedule:
            return False, "排程缺少活動欄位"
        
        if not ConfigValidator.validate_time_format(schedule["time"]):
            return False, f"時間格式錯誤: {schedule['time']}"
        
        if not ConfigValidator.validate_campaign_name(schedule["campaign"]):
            return False, f"活動名稱格式錯誤: {schedule['campaign']}"
        
        return True, None
    
    @staticmethod
    def validate_broadcast_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """驗證廣播配置"""
        errors = []
        
        # 檢查必要欄位
        required_fields = ["schedules", "target_groups", "control_group", "enabled"]
        for field in required_fields:
            if field not in config:
                errors.append(f"缺少必要欄位: {field}")
        
        # 驗證排程列表
        if "schedules" in config:
            if not isinstance(config["schedules"], list):
                errors.append("schedules必須是列表格式")
            else:
                for i, schedule in enumerate(config["schedules"]):
                    is_valid, error = ConfigValidator.validate_schedule(schedule)
                    if not is_valid:
                        errors.append(f"排程[{i}]: {error}")
        
        # 驗證目標群組
        if "target_groups" in config:
            if not isinstance(config["target_groups"], list):
                errors.append("target_groups必須是列表格式")
            else:
                for group_id in config["target_groups"]:
                    if not ConfigValidator.validate_group_id(group_id):
                        errors.append(f"無效的群組ID: {group_id}")
        
        # 驗證控制群組
        if "control_group" in config:
            if config["control_group"] != 0 and not ConfigValidator.validate_group_id(config["control_group"]):
                errors.append(f"無效的控制群組ID: {config['control_group']}")
        
        # 驗證啟用狀態
        if "enabled" in config:
            if not isinstance(config["enabled"], bool):
                errors.append("enabled必須是布林值")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_admin_config(admin: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """驗證管理員配置"""
        if not isinstance(admin, dict):
            return False, "管理員配置必須是字典格式"
        
        if "id" not in admin:
            return False, "管理員配置缺少ID欄位"
        
        if not isinstance(admin["id"], int):
            return False, "管理員ID必須是整數"
        
        if "name" not in admin:
            return False, "管理員配置缺少名稱欄位"
        
        if not isinstance(admin["name"], str) or not admin["name"].strip():
            return False, "管理員名稱不能為空"
        
        return True, None
    
    @staticmethod
    def validate_api_config(config: Dict[str, str]) -> Tuple[bool, List[str]]:
        """驗證API配置"""
        errors = []
        
        # 檢查API ID
        if "api_id" not in config or not config["api_id"]:
            errors.append("API ID不能為空")
        elif not ConfigValidator.validate_api_id(config["api_id"]):
            errors.append("API ID格式錯誤")
        
        # 檢查API Hash
        if "api_hash" not in config or not config["api_hash"]:
            errors.append("API Hash不能為空")
        elif not ConfigValidator.validate_api_hash(config["api_hash"]):
            errors.append("API Hash格式錯誤")
        
        # 檢查電話號碼
        if "phone_number" not in config or not config["phone_number"]:
            errors.append("電話號碼不能為空")
        elif not ConfigValidator.validate_phone_number(config["phone_number"]):
            errors.append("電話號碼格式錯誤 (應為國際格式，如: +886912345678)")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def sanitize_schedule_time(time_str: str) -> str:
        """清理和標準化時間格式"""
        # 移除空格
        time_str = time_str.strip()
        
        # 確保兩位數格式
        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 2:
                hour, minute = parts
                try:
                    hour = int(hour)
                    minute = int(minute)
                    return f"{hour:02d}:{minute:02d}"
                except ValueError:
                    pass
        
        return time_str
    
    @staticmethod
    def sanitize_campaign_name(campaign: str) -> str:
        """清理活動名稱"""
        # 移除空格並轉換為大寫
        return campaign.strip().upper()
    
    @staticmethod
    def sanitize_phone_number(phone: str) -> str:
        """清理電話號碼"""
        # 移除空格和特殊字符，確保以+開頭
        phone = re.sub(r'[^\d+]', '', phone.strip())
        if not phone.startswith('+'):
            phone = '+' + phone
        return phone

class ConfigManager:
    """配置管理器 - 統一管理所有配置"""
    
    def __init__(self, base_path: str = None):
        import logging
        self.logger = logging.getLogger(__name__)
        self.base_path = base_path or os.getcwd()
        self.data_path = os.path.join(self.base_path, "data")
        
        # 配置文件路徑
        self.broadcast_config_path = os.path.join(self.data_path, "broadcast_config.json")
        self.broadcast_history_path = os.path.join(self.data_path, "broadcast_history.json")
        self.admins_config_path = os.path.join(self.data_path, "admins.json")
        self.settings_config_path = os.path.join(self.data_path, "settings.json")
        self.env_path = os.path.join(self.base_path, ".env")
        
        # 確保數據目錄存在
        os.makedirs(self.data_path, exist_ok=True)
        
        # 載入配置
        self._load_all_configs()
    
    def _load_all_configs(self):
        """載入所有配置文件"""
        # 載入環境變數配置
        self.api_config = self._load_env_config()
        
        # 載入JSON配置文件
        self.broadcast_config = self._load_json_config(self.broadcast_config_path, self._default_broadcast_config())
        self.broadcast_history = self._load_json_config(self.broadcast_history_path, [])
        self.admins_config = self._load_json_config(self.admins_config_path, self._default_admins_config())
        self.settings_config = self._load_json_config(self.settings_config_path, self._default_settings_config())
    
    def _load_env_config(self) -> Dict[str, str]:
        """載入.env配置"""
        config = {}
        if os.path.exists(self.env_path):
            with open(self.env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        return config
    
    def _load_json_config(self, file_path: str, default_config: Any) -> Any:
        """載入JSON配置文件"""
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"警告: 無法讀取 {file_path}: {e}")
                return default_config
        else:
            # 創建默認配置文件
            self._save_json_config(file_path, default_config)
            return default_config
    
    def _save_json_config(self, file_path: str, config: Any) -> bool:
        """保存JSON配置文件"""
        try:
            # 備份現有文件
            if os.path.exists(file_path):
                backup_path = f"{file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(file_path, backup_path)
            
            # 保存新配置
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            print(f"錯誤: 無法保存 {file_path}: {e}")
            return False
    
    def _default_broadcast_config(self) -> Dict[str, Any]:
        """默認廣播配置"""
        return {
            "schedules": [
                {"time": "09:00", "campaign": "A"},
                {"time": "14:00", "campaign": "B"},
                {"time": "19:00", "campaign": "C"}
            ],
            "target_groups": [],
            "control_group": 0,
            "enabled": True,
            "broadcast_delay": 5,
            "max_retries": 3,
            "total_restarts": 0
        }
    
    def _default_admins_config(self) -> List[Dict[str, Any]]:
        """默認管理員配置"""
        return []
    
    def _default_settings_config(self) -> Dict[str, Any]:
        """默認系統設定"""
        return {
            "timezone": "Asia/Taipei",
            "log_level": "INFO",
            "max_log_files": 10,
            "backup_retention_days": 30,
            "api_rate_limit": {
                "messages_per_second": 1,
                "messages_per_minute": 20
            }
        }
    
    # 廣播配置管理
    def get_schedules(self) -> List[Dict[str, str]]:
        """獲取排程列表"""
        return self.broadcast_config.get("schedules", [])
    
    def add_schedule(self, time: str, campaign: str) -> bool:
        """新增排程"""
        new_schedule = {"time": time, "campaign": campaign}
        if new_schedule not in self.broadcast_config["schedules"]:
            self.broadcast_config["schedules"].append(new_schedule)
            return self.save_broadcast_config()
        return False
    
    def remove_schedule(self, time: str = None, campaign: str = None) -> bool:
        """移除排程"""
        original_count = len(self.broadcast_config["schedules"])
        
        if time and campaign:
            # 移除指定時間和活動的排程
            self.broadcast_config["schedules"] = [
                s for s in self.broadcast_config["schedules"] 
                if not (s["time"] == time and s["campaign"] == campaign)
            ]
        elif time:
            # 移除指定時間的所有排程
            self.broadcast_config["schedules"] = [
                s for s in self.broadcast_config["schedules"] 
                if s["time"] != time
            ]
        elif campaign:
            # 移除指定活動的所有排程
            self.broadcast_config["schedules"] = [
                s for s in self.broadcast_config["schedules"] 
                if s["campaign"] != campaign
            ]
        
        if len(self.broadcast_config["schedules"]) < original_count:
            return self.save_broadcast_config()
        return False
    
    def clear_all_schedules(self) -> bool:
        """清空所有排程"""
        if self.broadcast_config["schedules"]:
            self.broadcast_config["schedules"] = []
            return self.save_broadcast_config()
        return False
    
    def get_target_groups(self) -> List[int]:
        """獲取目標群組列表"""
        target_groups = self.broadcast_config.get("target_groups", [])
        # 去除重複項目，保持順序
        unique_groups = []
        seen = set()
        for group_id in target_groups:
            if group_id not in seen:
                unique_groups.append(group_id)
                seen.add(group_id)
        
        # 如果發現重複項目，更新配置檔案
        if len(unique_groups) != len(target_groups):
            self.broadcast_config["target_groups"] = unique_groups
            success = self.save_broadcast_config()
            if success:
                self.logger.info(f"清理重複目標群組：原有 {len(target_groups)} 個，去重後 {len(unique_groups)} 個")
            else:
                self.logger.error("清理重複目標群組時保存配置失敗")
        
        return unique_groups
    
    def add_target_group(self, group_id: int) -> bool:
        """新增目標群組"""
        if group_id not in self.broadcast_config["target_groups"]:
            self.broadcast_config["target_groups"].append(group_id)
            return self.save_broadcast_config()
        return False
    
    def remove_target_group(self, group_id: int) -> bool:
        """移除目標群組"""
        if group_id in self.broadcast_config["target_groups"]:
            self.broadcast_config["target_groups"].remove(group_id)
            success = self.save_broadcast_config()
            if success:
                # 強制重新載入配置以確保一致性
                self._reload_broadcast_config()
            return success
        return False
    
    def get_control_group(self) -> int:
        """獲取控制群組ID"""
        return self.broadcast_config.get("control_group", 0)
    
    def set_control_group(self, group_id: int) -> bool:
        """設定控制群組"""
        self.broadcast_config["control_group"] = group_id
        return self.save_broadcast_config()
    
    def is_schedule_enabled(self) -> bool:
        """檢查排程是否啟用"""
        return self.broadcast_config.get("enabled", True)
    
    def toggle_schedule(self) -> bool:
        """切換排程啟用狀態"""
        self.broadcast_config["enabled"] = not self.broadcast_config.get("enabled", True)
        return self.save_broadcast_config()
    
    def save_broadcast_config(self, config: dict = None) -> bool:
        """保存廣播配置"""
        try:
            if config:
                self.broadcast_config = config
            self._save_json_config(self.broadcast_config_path, self.broadcast_config)
            return True
        except Exception as e:
            print(f"保存廣播配置失敗: {e}")
            return False
    
    def _reload_broadcast_config(self):
        """重新載入廣播配置"""
        try:
            self.broadcast_config = self._load_json_config(self.broadcast_config_path, self.default_broadcast_config)
            self.logger.debug("廣播配置已重新載入")
        except Exception as e:
            self.logger.error(f"重新載入廣播配置失敗: {e}")
    
    def _original_save_broadcast_config(self) -> bool:
        """保存廣播配置"""
        return self._save_json_config(self.broadcast_config_path, self.broadcast_config)

    def save_config(self) -> bool:
        """保存 settings.json 配置"""
        return self._save_json_config(self.settings_config_path, self.settings_config)
    
    # 管理員配置管理
    def get_admins(self) -> List[Dict[str, Any]]:
        """獲取管理員列表"""
        return self.admins_config
    
    def add_admin(self, user_id: int, name: str, username: str = None) -> bool:
        """新增管理員"""
        admin = {
            "id": user_id,
            "name": name,
            "username": username,
            "added_at": datetime.now().isoformat()
        }
        
        # 檢查是否已存在
        for existing_admin in self.admins_config:
            if existing_admin.get("id") == user_id:
                return False
        
        self.admins_config.append(admin)
        return self.save_admins_config()
    
    def remove_admin(self, user_id: int) -> bool:
        """移除管理員"""
        original_count = len(self.admins_config)
        self.admins_config = [admin for admin in self.admins_config if admin.get("id") != user_id]
        
        if len(self.admins_config) < original_count:
            return self.save_admins_config()
        return False
    
    def is_admin(self, user_id: int) -> bool:
        """檢查是否為管理員"""
        return any(admin.get("id") == user_id for admin in self.admins_config)
    
    def save_admins_config(self) -> bool:
        """保存管理員配置"""
        return self._save_json_config(self.admins_config_path, self.admins_config)
    
    # 廣播歷史管理
    def add_broadcast_history(self, campaign: str, groups_count: int, success_count: int, errors: List[str] = None) -> bool:
        """新增廣播歷史記錄"""
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "campaign": campaign,
            "groups_count": groups_count,
            "success_count": success_count,
            "failure_count": groups_count - success_count,
            "success_rate": (success_count / groups_count * 100) if groups_count > 0 else 0,
            "errors": errors or []
        }
        
        self.broadcast_history.append(history_entry)
        
        # 限制歷史記錄數量
        if len(self.broadcast_history) > 1000:
            self.broadcast_history = self.broadcast_history[-1000:]
        
        return self.save_broadcast_history()
    
    def get_broadcast_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """獲取廣播歷史記錄"""
        return self.broadcast_history[-limit:] if limit else self.broadcast_history
    
    def save_broadcast_history(self) -> bool:
        """保存廣播歷史"""
        return self._save_json_config(self.broadcast_history_path, self.broadcast_history)
    
    # API配置管理
    def get_api_config(self) -> Dict[str, str]:
        """獲取API配置"""
        api_config = self.settings_config.get("api_config", {})
        return {
            "api_id": api_config.get("api_id", ""),
            "api_hash": api_config.get("api_hash", ""),
            "phone": api_config.get("phone", ""),
            "session_name": "userbot"
        }

    def get_api_id(self) -> Optional[str]:
        return self.settings_config.get('api_config', {}).get('api_id')

    def get_api_hash(self) -> Optional[str]:
        return self.settings_config.get('api_config', {}).get('api_hash')

    def get_phone(self) -> Optional[str]:
        return self.settings_config.get('api_config', {}).get('phone')

    def set_api_credentials(self, api_id: int, api_hash: str, phone: str):
        if 'api_config' not in self.settings_config:
            self.settings_config['api_config'] = {}
        self.settings_config['api_config']['api_id'] = api_id
        self.settings_config['api_config']['api_hash'] = api_hash
        self.settings_config['api_config']['phone'] = phone
    
    def update_api_config(self, api_id: str, api_hash: str, phone_number: str) -> bool:
        """更新API配置"""
        try:
            with open(self.env_path, 'w', encoding='utf-8') as f:
                f.write(f"API_ID={api_id}\n")
                f.write(f"API_HASH={api_hash}\n")
                f.write(f"PHONE_NUMBER={phone_number}\n")
            
            # 更新內存中的配置
            self.api_config.update({
                "API_ID": api_id,
                "API_HASH": api_hash,
                "PHONE_NUMBER": phone_number
            })
            return True
        except IOError as e:
            print(f"錯誤: 無法保存API配置: {e}")
            return False
    
    # 系統設定管理
    def get_settings(self) -> Dict[str, Any]:
        """獲取系統設定"""
        return self.settings_config
    
    def update_setting(self, key: str, value: Any) -> bool:
        """更新系統設定"""
        self.settings_config[key] = value
        return self._save_json_config(self.settings_config_path, self.settings_config)
    
    # 內容目錄管理
    def get_content_path(self, campaign: str) -> str:
        """獲取內容目錄路徑"""
        content_base = os.path.join(self.data_path, "content_databases")
        return os.path.join(content_base, campaign.upper())
    
    def list_available_campaigns(self) -> List[str]:
        """列出可用的活動"""
        content_base = os.path.join(self.data_path, "content_databases")
        if not os.path.exists(content_base):
            return []
        
        campaigns = []
        for item in os.listdir(content_base):
            campaign_path = os.path.join(content_base, item)
            if os.path.isdir(campaign_path):
                campaigns.append(item)
        
        return sorted(campaigns)
