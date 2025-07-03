#!/usr/bin/env python3
"""
完全運作的GUI版本 - 包含所有實際功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import asyncio
import queue
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# 添加項目路徑
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import ConfigManager
from broadcast_system import BroadcastSystem
from telegram_client import TelegramClientManager
from content_manager import ContentManager
from command_handler import CommandHandler
from broadcast_manager import BroadcastManager
from message_manager import MessageManager

class WorkingBroadcastGUI:
    """完全運作的廣播GUI"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("RG Telegram 廣播系統 - 完全運作版")
        self.root.geometry("1000x700")
        
        # 初始化核心組件
        self.config_manager = ConfigManager()
        self.content_manager = ContentManager()
        self.client_manager = None
        self.broadcast_system = None
        self.command_handler = None
        self.broadcast_manager = None
        self.message_manager = None
        
        # 狀態隊列
        self.status_queue = queue.Queue()
        
        # 異步相關
        self.loop = None
        self.thread = None
        self.running = False
        
        # 連接狀態
        self.is_connected = False
        
        # 掃描結果緩存
        self.scanned_groups = []
        self.last_scan_time = None
        
        # 創建界面
        self.create_widgets()
        self.load_config()
        
        # 啟動異步處理
        self.start_async_thread()
        
        # 開始處理狀態更新
        self.process_status_queue()
    
    def create_widgets(self):
        """創建界面組件"""
        # 主筆記本控件
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=10, padx=10, expand=True, fill='both')
        
        # 創建各個頁籤
        self.create_connection_tab()
        self.create_broadcast_tab()
        self.create_management_tab()
        self.create_status_tab()
    
    def create_connection_tab(self):
        """創建連接頁籤"""
        self.connection_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.connection_tab, text='🔗 連接設定')
        
        # 連接狀態
        status_frame = ttk.LabelFrame(self.connection_tab, text="連接狀態", padding="10")
        status_frame.pack(fill='x', padx=10, pady=5)
        
        self.connection_status_var = tk.StringVar(value="❌ 未連接")
        ttk.Label(status_frame, textvariable=self.connection_status_var, 
                 font=('Arial', 12, 'bold')).pack()
        
        # 連接控制
        control_frame = ttk.Frame(self.connection_tab)
        control_frame.pack(fill='x', padx=10, pady=10)
        
        self.connect_btn = ttk.Button(control_frame, text="🔗 連接Telegram", 
                                     command=self.connect_telegram)
        self.connect_btn.pack(side='left', padx=5)
        
        self.disconnect_btn = ttk.Button(control_frame, text="🔌 斷開連接", 
                                       command=self.disconnect_telegram, state='disabled')
        self.disconnect_btn.pack(side='left', padx=5)
        
        ttk.Button(control_frame, text="🔄 重新載入配置", 
                  command=self.load_config).pack(side='left', padx=5)
        
        # API設定資訊（只顯示，不編輯）
        info_frame = ttk.LabelFrame(self.connection_tab, text="API設定資訊", padding="10")
        info_frame.pack(fill='x', padx=10, pady=5)
        
        self.api_info_text = scrolledtext.ScrolledText(info_frame, height=8, state='disabled')
        self.api_info_text.pack(fill='both', expand=True)
    
    def create_broadcast_tab(self):
        """創建廣播頁籤"""
        self.broadcast_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.broadcast_tab, text='📡 廣播控制')
        
        # 手動廣播
        manual_frame = ttk.LabelFrame(self.broadcast_tab, text="手動廣播", padding="10")
        manual_frame.pack(fill='x', padx=10, pady=5)
        
        # 活動選擇
        ttk.Label(manual_frame, text="選擇活動:").grid(row=0, column=0, sticky='w', pady=5)
        
        self.campaign_var = tk.StringVar()
        self.campaign_frame = ttk.Frame(manual_frame)
        self.campaign_frame.grid(row=0, column=1, sticky='ew', pady=5)
        
        # 動態載入活動選項
        self.refresh_campaign_options()
        
        manual_frame.columnconfigure(1, weight=1)
        
        # 廣播按鈕
        btn_frame = ttk.Frame(manual_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="🚀 立即廣播", command=self.manual_broadcast,
                  style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(btn_frame, text="👁️ 預覽內容", command=self.preview_content).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🧪 測試廣播", command=self.test_broadcast).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🔄 刷新活動", command=self.refresh_campaign_options).pack(side='left', padx=5)
        
        # 排程控制
        schedule_frame = ttk.LabelFrame(self.broadcast_tab, text="排程控制", padding="10")
        schedule_frame.pack(fill='x', padx=10, pady=5)
        
        self.schedule_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(schedule_frame, text="啟用自動排程", 
                       variable=self.schedule_enabled_var, 
                       command=self.toggle_schedule).pack(anchor='w')
        
        ttk.Button(schedule_frame, text="📅 查看排程", 
                  command=self.show_schedules).pack(side='left', padx=5)
        ttk.Button(schedule_frame, text="➕ 新增排程", 
                  command=self.add_schedule_dialog).pack(side='left', padx=5)
        ttk.Button(schedule_frame, text="➖ 移除排程", 
                  command=self.remove_schedule_dialog).pack(side='left', padx=5)
        ttk.Button(schedule_frame, text="🔄 重新載入", 
                  command=self.refresh_schedule_status).pack(side='left', padx=5)
    
    def create_management_tab(self):
        """創建管理頁籤"""
        self.management_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.management_tab, text='⚙️ 系統管理')
        
        # 群組管理
        group_frame = ttk.LabelFrame(self.management_tab, text="群組管理", padding="10")
        group_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 群組狀態資訊
        group_info_frame = ttk.Frame(group_frame)
        group_info_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(group_info_frame, text="目標群組:", font=('Arial', 10, 'bold')).pack(side='left')
        self.group_count_label = ttk.Label(group_info_frame, text="(0 個群組)", foreground='gray')
        self.group_count_label.pack(side='left', padx=(5, 0))
        
        # 群組列表
        self.groups_text = scrolledtext.ScrolledText(group_frame, height=8, state='disabled', 
                                                   font=('Consolas', 9))
        self.groups_text.pack(fill='both', expand=True, pady=(0, 10))
        
        # 群組操作按鈕 - 重新組織為兩行
        group_btn_frame = ttk.Frame(group_frame)
        group_btn_frame.pack(fill='x')
        
        # 第一行按鈕 - 管理操作
        manage_btn_frame = ttk.Frame(group_btn_frame)
        manage_btn_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(manage_btn_frame, text="群組管理:", font=('Arial', 9, 'bold')).pack(side='left')
        
        ttk.Button(manage_btn_frame, text="➕ 添加群組", 
                  command=self.add_group_dialog).pack(side='left', padx=(10, 5))
        ttk.Button(manage_btn_frame, text="➖ 移除群組", 
                  command=self.remove_group_dialog).pack(side='left', padx=5)
        ttk.Button(manage_btn_frame, text="📋 管理群組", 
                  command=self.manage_groups_dialog).pack(side='left', padx=5)
        
        # 第二行按鈕 - 查看操作
        view_btn_frame = ttk.Frame(group_btn_frame)
        view_btn_frame.pack(fill='x')
        
        ttk.Label(view_btn_frame, text="查看功能:", font=('Arial', 9, 'bold')).pack(side='left')
        
        ttk.Button(view_btn_frame, text="🔄 重新載入", 
                  command=self.refresh_groups).pack(side='left', padx=(10, 5))
        ttk.Button(view_btn_frame, text="🌐 掃描群組", 
                  command=self.scan_groups).pack(side='left', padx=5)
        ttk.Button(view_btn_frame, text="📊 群組詳情", 
                  command=self.show_group_details).pack(side='left', padx=5)
        
        # 活動內容
        content_frame = ttk.LabelFrame(self.management_tab, text="活動內容", padding="10")
        content_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.content_text = scrolledtext.ScrolledText(content_frame, height=6, state='disabled')
        self.content_text.pack(fill='both', expand=True, pady=5)
        
        ttk.Button(content_frame, text="🔄 重新載入內容", 
                  command=self.refresh_content).pack(side='left', padx=5)
    
    def create_status_tab(self):
        """創建狀態頁籤"""
        self.status_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.status_tab, text='📋 系統狀態')
        
        # 狀態顯示
        status_frame = ttk.LabelFrame(self.status_tab, text="系統日誌", padding="10")
        status_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.status_text = scrolledtext.ScrolledText(status_frame, height=25, wrap='word')
        self.status_text.pack(fill='both', expand=True)
        
        # 控制按鈕
        status_btn_frame = ttk.Frame(self.status_tab)
        status_btn_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(status_btn_frame, text="🗑️ 清空日誌", 
                  command=self.clear_status).pack(side='left', padx=5)
        ttk.Button(status_btn_frame, text="💾 保存日誌", 
                  command=self.save_status).pack(side='left', padx=5)
        ttk.Button(status_btn_frame, text="🔄 系統重啟", 
                  command=self.restart_system).pack(side='right', padx=5)
    
    def start_async_thread(self):
        """啟動異步處理線程"""
        self.running = True
        self.thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.thread.start()
        self.queue_status_update("🚀 異步處理器已啟動")
    
    def _run_async_loop(self):
        """運行異步事件循環"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self._async_main())
        except Exception as e:
            self.queue_status_update(f"❌ 異步處理器錯誤: {e}")
        finally:
            self.loop.close()
    
    async def _async_main(self):
        """異步主循環"""
        while self.running:
            await asyncio.sleep(1)
    
    def submit_task(self, coro):
        """提交異步任務"""
        if self.loop and self.loop.is_running():
            return asyncio.run_coroutine_threadsafe(coro, self.loop)
        return None
    
    def load_config(self):
        """載入配置"""
        try:
            self.queue_status_update("🔄 載入配置...")
            
            # 載入API設定
            api_id = self.config_manager.get_api_id()
            api_hash = self.config_manager.get_api_hash()
            phone = self.config_manager.get_phone()
            
            # 更新API資訊顯示
            self.api_info_text.config(state='normal')
            self.api_info_text.delete(1.0, 'end')
            
            info_text = f"""API 設定資訊:
API ID: {api_id if api_id else '未設定'}
API Hash: {api_hash[:10] + '...' if api_hash else '未設定'}
手機號碼: {phone if phone else '未設定'}
Session文件: {"存在" if Path("userbot.session").exists() else "不存在"}

配置狀態: {"✅ 完整" if (api_id and api_hash and phone) else "❌ 不完整"}
"""
            self.api_info_text.insert('end', info_text)
            self.api_info_text.config(state='disabled')
            
            # 載入其他配置
            self.refresh_groups()
            self.refresh_content()
            self.refresh_schedule_status()
            
            self.queue_status_update("✅ 配置載入完成")
            
        except Exception as e:
            self.queue_status_update(f"❌ 配置載入失敗: {e}")
    
    def refresh_groups(self):
        """刷新群組列表"""
        try:
            broadcast_config = self.config_manager.broadcast_config
            target_groups = broadcast_config.get('target_groups', [])
            control_group = broadcast_config.get('control_group')
            
            # 更新群組數量標籤
            self.group_count_label.config(text=f"({len(target_groups)} 個群組)")
            
            self.groups_text.config(state='normal')
            self.groups_text.delete(1.0, 'end')
            
            # 添加表頭
            self.groups_text.insert('end', f"{'序號':<4} {'群組ID':<15} {'類型':<8} {'狀態'}\n")
            self.groups_text.insert('end', "-" * 50 + "\n")
            
            # 目標廣播群組
            if target_groups:
                for i, group_id in enumerate(target_groups):
                    status = "✅ 正常" if group_id != 0 else "❌ 無效"
                    self.groups_text.insert('end', f"{i+1:2d}.  {str(group_id):<15} {'目標群組':<8} {status}\n")
            else:
                self.groups_text.insert('end', "     沒有設定目標群組\n")
            
            # 控制群組
            self.groups_text.insert('end', "\n" + "-" * 50 + "\n")
            if control_group and control_group != 0:
                status = "✅ 正常"
                self.groups_text.insert('end', f"{'*':<4} {str(control_group):<15} {'控制群組':<8} {status}\n")
            else:
                self.groups_text.insert('end', "     沒有設定控制群組\n")
            
            self.groups_text.config(state='disabled')
            
        except Exception as e:
            self.queue_status_update(f"❌ 群組資訊載入失敗: {e}")
    
    def refresh_campaign_options(self):
        """刷新活動選項"""
        try:
            # 清除現有的radiobutton
            for widget in self.campaign_frame.winfo_children():
                widget.destroy()
            
            # 獲取所有活動
            campaigns = self.content_manager.get_campaigns()
            
            if not campaigns:
                # 如果沒有活動，顯示提示
                ttk.Label(self.campaign_frame, text="(無可用活動)", 
                         foreground='gray').pack(side='left', padx=10)
                return
            
            # 創建新的radiobutton
            for i, campaign in enumerate(campaigns):
                ttk.Radiobutton(self.campaign_frame, text=f"活動 {campaign}", 
                              variable=self.campaign_var, value=campaign).pack(side='left', padx=10)
            
            # 設定預設選擇第一個活動
            if campaigns and not self.campaign_var.get():
                self.campaign_var.set(campaigns[0])
                
            self.queue_status_update(f"✅ 已載入 {len(campaigns)} 個活動選項")
            
        except Exception as e:
            self.queue_status_update(f"❌ 活動選項載入失敗: {e}")
    
    def refresh_content(self):
        """刷新活動內容"""
        try:
            campaigns = self.content_manager.get_campaigns()
            
            self.content_text.config(state='normal')
            self.content_text.delete(1.0, 'end')
            
            content_text = f"活動內容摘要 ({len(campaigns)} 個活動):\n\n"
            
            for campaign in campaigns:
                content = self.content_manager.get_campaign_content(campaign)
                if 'error' not in content:
                    text_len = len(content.get('text_content', ''))
                    media_count = len(content.get('media_files', []))
                    content_text += f"活動 {campaign}: {text_len} 字符, {media_count} 個媒體檔案\n"
                else:
                    content_text += f"活動 {campaign}: ❌ {content['error']}\n"
            
            self.content_text.insert('end', content_text)
            self.content_text.config(state='disabled')
            
            # 同時刷新活動選項
            self.refresh_campaign_options()
            
        except Exception as e:
            self.queue_status_update(f"❌ 活動內容載入失敗: {e}")
    
    def refresh_schedule_status(self):
        """刷新排程狀態"""
        try:
            if not self.broadcast_system:
                # 暫時創建一個broadcast_system來檢查狀態
                temp_system = BroadcastSystem(self.config_manager)
                enabled = temp_system.is_schedule_enabled()
                schedules = temp_system.get_schedules()
            else:
                enabled = self.broadcast_system.is_schedule_enabled()
                schedules = self.broadcast_system.get_schedules()
            
            self.schedule_enabled_var.set(enabled)
            self.queue_status_update(f"📅 排程狀態: {'啟用' if enabled else '停用'} ({len(schedules)} 個排程)")
            
        except Exception as e:
            self.queue_status_update(f"❌ 排程狀態載入失敗: {e}")
    
    def queue_status_update(self, message):
        """隊列狀態更新"""
        self.status_queue.put(message)
    
    def process_status_queue(self):
        """處理狀態隊列"""
        try:
            while True:
                message = self.status_queue.get_nowait()
                self.update_status_display(message)
                
                # 更新連接狀態
                if "Telegram連接成功" in message:
                    self.connection_status_var.set("✅ 已連接")
                    self.connect_btn.config(state='disabled')
                    self.disconnect_btn.config(state='normal')
                    self.is_connected = True
                elif "已斷開連接" in message or "連接失敗" in message:
                    self.connection_status_var.set("❌ 未連接")
                    self.connect_btn.config(state='normal')
                    self.disconnect_btn.config(state='disabled')
                    self.is_connected = False
                    
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_status_queue)
    
    def update_status_display(self, message):
        """更新狀態顯示"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.status_text.insert('end', formatted_message)
        self.status_text.see('end')
    
    # 連接相關方法
    def connect_telegram(self):
        """連接Telegram"""
        api_id = self.config_manager.get_api_id()
        api_hash = self.config_manager.get_api_hash()
        phone = self.config_manager.get_phone()
        
        if not (api_id and api_hash and phone):
            messagebox.showerror("錯誤", "API設定不完整，請檢查配置檔案")
            return
        
        self.connect_btn.config(state='disabled')
        self.queue_status_update("🔄 正在連接Telegram...")
        
        task = self.submit_task(self._connect_telegram(api_id, api_hash, phone))
    
    async def _connect_telegram(self, api_id, api_hash, phone):
        """異步連接Telegram"""
        try:
            # 初始化客戶端管理器
            self.client_manager = TelegramClientManager(self.config_manager)
            
            # 啟動客戶端
            success = await self.client_manager.start_client(api_id, api_hash, phone)
            
            if success:
                user = self.client_manager.current_user
                self.queue_status_update(f"✅ Telegram連接成功！用戶: {user.first_name}")
                
                # 初始化廣播系統
                self.broadcast_system = BroadcastSystem(
                    self.config_manager, 
                    self.queue_status_update
                )
                self.broadcast_system.client_manager = self.client_manager
                
                # 初始化廣播管理器
                self.broadcast_manager = BroadcastManager(
                    self.client_manager, 
                    self.config_manager
                )
                
                # 初始化訊息管理器（需要使用broadcast_manager的內部組件）
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
                
                # 註冊所有命令處理器（包括/help）
                self.command_handler.register_all_handlers()
                
                self.queue_status_update("✅ 命令處理器已初始化")
                
                return True
            else:
                self.queue_status_update("❌ Telegram連接失敗")
                self.connect_btn.config(state='normal')
                return False
                
        except Exception as e:
            self.queue_status_update(f"❌ 連接錯誤: {e}")
            self.connect_btn.config(state='normal')
            return False
    
    def disconnect_telegram(self):
        """斷開Telegram連接"""
        self.disconnect_btn.config(state='disabled')
        self.queue_status_update("🔄 正在斷開連接...")
        
        task = self.submit_task(self._disconnect_telegram())
    
    async def _disconnect_telegram(self):
        """異步斷開Telegram連接"""
        try:
            if self.client_manager:
                await self.client_manager.disconnect()
                self.client_manager = None
            
            if self.broadcast_system:
                self.broadcast_system = None
            
            self.queue_status_update("🔌 Telegram已斷開連接")
            
        except Exception as e:
            self.queue_status_update(f"❌ 斷開連接錯誤: {e}")
    
    # 廣播相關方法
    def manual_broadcast(self):
        """手動廣播"""
        if not self.is_connected:
            messagebox.showerror("錯誤", "請先連接Telegram")
            return
        
        campaign = self.campaign_var.get()
        if not campaign:
            messagebox.showwarning("警告", "請選擇活動代碼")
            return
        
        result = messagebox.askyesno("確認廣播", 
                                   f"確定要立即廣播活動 {campaign} 嗎？\\n"
                                   f"⚠️ 這將發送真實訊息到所有目標群組！")
        if result:
            self.queue_status_update(f"🚀 開始廣播活動 {campaign}")
            task = self.submit_task(self._manual_broadcast(campaign))
    
    async def _manual_broadcast(self, campaign):
        """異步手動廣播"""
        try:
            if not self.broadcast_system:
                self.queue_status_update("❌ 廣播系統未初始化")
                return
            
            result = await self.broadcast_system.broadcast_campaign(campaign)
            
            if result.get('success'):
                sent = result.get('sent_count', 0)
                failed = result.get('failed_count', 0)
                self.queue_status_update(f"✅ 廣播完成: 成功{sent}個，失敗{failed}個")
                
                if failed > 0:
                    errors = result.get('errors', [])
                    for error in errors[:3]:  # 只顯示前3個錯誤
                        self.queue_status_update(f"   ❌ {error}")
                
            else:
                error = result.get('error', '未知錯誤')
                self.queue_status_update(f"❌ 廣播失敗: {error}")
                
        except Exception as e:
            self.queue_status_update(f"❌ 廣播異常: {e}")
    
    def preview_content(self):
        """預覽活動內容"""
        campaign = self.campaign_var.get()
        if not campaign:
            messagebox.showwarning("警告", "請選擇活動代碼")
            return
        
        try:
            content = self.content_manager.get_campaign_content(campaign)
            if 'error' in content:
                messagebox.showerror("錯誤", content['error'])
                return
            
            text_content = content.get('text_content', '')
            media_files = content.get('media_files', [])
            
            preview_window = tk.Toplevel(self.root)
            preview_window.title(f"活動 {campaign} 內容預覽")
            preview_window.geometry("600x500")
            
            # 文字內容
            if text_content:
                ttk.Label(preview_window, text="文字內容:").pack(anchor='w', padx=10, pady=5)
                text_widget = scrolledtext.ScrolledText(preview_window, height=15)
                text_widget.pack(fill='both', expand=True, padx=10, pady=5)
                text_widget.insert('end', text_content)
                text_widget.config(state='disabled')
            
            # 媒體檔案
            if media_files:
                ttk.Label(preview_window, text=f"媒體檔案 ({len(media_files)} 個):").pack(anchor='w', padx=10, pady=5)
                for media in media_files:
                    ttk.Label(preview_window, text=f"  📎 {media['name']} ({media['type']})").pack(anchor='w', padx=20)
            
        except Exception as e:
            messagebox.showerror("錯誤", f"預覽內容失敗: {e}")
    
    def test_broadcast(self):
        """測試廣播（不實際發送）"""
        campaign = self.campaign_var.get()
        if not campaign:
            messagebox.showwarning("警告", "請選擇活動代碼")
            return
        
        self.queue_status_update(f"🧪 測試廣播活動 {campaign}...")
        
        try:
            # 檢查活動內容
            content = self.content_manager.get_campaign_content(campaign)
            if 'error' in content:
                self.queue_status_update(f"❌ 活動內容錯誤: {content['error']}")
                return
            
            text_len = len(content.get('text_content', ''))
            media_count = len(content.get('media_files', []))
            
            # 檢查目標群組
            broadcast_config = self.config_manager.broadcast_config
            target_groups = broadcast_config.get('target_groups', [])
            
            self.queue_status_update(f"   ✅ 活動內容: {text_len} 字符, {media_count} 個媒體檔案")
            self.queue_status_update(f"   ✅ 目標群組: {len(target_groups)} 個")
            self.queue_status_update(f"   ✅ 連接狀態: {'已連接' if self.is_connected else '未連接'}")
            self.queue_status_update("🎉 測試廣播檢查完成 - 所有項目正常")
            
        except Exception as e:
            self.queue_status_update(f"❌ 測試廣播失敗: {e}")
    
    def toggle_schedule(self):
        """切換排程狀態"""
        if not self.broadcast_system:
            # 創建臨時系統來更新狀態
            temp_system = BroadcastSystem(self.config_manager)
            enabled = self.schedule_enabled_var.get()
            success, message = temp_system.set_schedule_enabled(enabled)
            
            if success:
                self.queue_status_update(f"✅ {message}")
            else:
                self.queue_status_update(f"❌ {message}")
                self.schedule_enabled_var.set(not enabled)  # 恢復原狀態
        else:
            enabled = self.schedule_enabled_var.get()
            success, message = self.broadcast_system.set_schedule_enabled(enabled)
            
            if success:
                self.queue_status_update(f"✅ {message}")
            else:
                self.queue_status_update(f"❌ {message}")
                self.schedule_enabled_var.set(not enabled)  # 恢復原狀態
    
    def show_schedules(self):
        """顯示排程列表"""
        try:
            schedules = self.config_manager.broadcast_config.get('schedules', [])
            
            schedule_window = tk.Toplevel(self.root)
            schedule_window.title("排程列表")
            schedule_window.geometry("600x500")
            schedule_window.transient(self.root)
            
            # 主框架
            main_frame = ttk.Frame(schedule_window, padding="10")
            main_frame.pack(fill='both', expand=True)
            
            # 標題框架
            title_frame = ttk.Frame(main_frame)
            title_frame.pack(fill='x', pady=(0, 10))
            
            ttk.Label(title_frame, text=f"排程列表 (共 {len(schedules)} 個)", 
                     font=('Arial', 14, 'bold')).pack(side='left')
            
            # 狀態標籤
            schedule_enabled = self.config_manager.broadcast_config.get('enabled', False)
            status_text = "✅ 已啟用" if schedule_enabled else "❌ 已停用"
            status_color = "green" if schedule_enabled else "red"
            
            status_info_frame = ttk.Frame(title_frame)
            status_info_frame.pack(side='right')
            
            ttk.Label(status_info_frame, text=f"排程狀態: {status_text}", 
                     foreground=status_color).pack(anchor='e')
            
            # 添加重置時間說明
            now = datetime.now()
            if now.hour >= 8:
                next_reset = "明天 08:00"
            else:
                next_reset = "今天 08:00"
            ttk.Label(status_info_frame, text=f"下次重置: {next_reset}", 
                     font=('Arial', 9), foreground='gray').pack(anchor='e')
            
            # 排程列表框架
            list_frame = ttk.LabelFrame(main_frame, text="排程詳情", padding="10")
            list_frame.pack(fill='both', expand=True, pady=10)
            
            # 如果沒有排程，顯示提示
            if not schedules:
                ttk.Label(list_frame, text="目前沒有任何排程", 
                         font=('Arial', 12), foreground='gray').pack(expand=True)
            else:
                # 排程列表
                schedule_text = scrolledtext.ScrolledText(list_frame, height=15, font=('Consolas', 10))
                schedule_text.pack(fill='both', expand=True)
                
                # 添加表頭
                schedule_text.insert('end', f"{'序號':<4} {'時間':<8} {'活動':<8} {'狀態'}\n")
                schedule_text.insert('end', "-" * 40 + "\n")
                
                # 獲取當前時間和8點重置邏輯
                now = datetime.now()
                current_time = now.strftime('%H:%M')
                current_hour = now.hour
                current_minute = now.minute
                
                for i, schedule in enumerate(schedules):
                    time_str = schedule.get('time', 'N/A')
                    campaign = schedule.get('campaign', 'N/A')
                    
                    # 判斷排程狀態（24小時循環，8點重新開始）
                    status = self._get_schedule_status(time_str, current_hour, current_minute)
                    
                    schedule_text.insert('end', f"{i+1:2d}.  {time_str:<8} 活動{campaign:<4} {status}\n")
                
                schedule_text.config(state='disabled')
            
            # 按鈕框架
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill='x', pady=10)
            
            # 左側按鈕（操作）
            left_buttons = ttk.Frame(button_frame)
            left_buttons.pack(side='left')
            
            ttk.Button(left_buttons, text="➕ 新增排程", 
                      command=lambda: [schedule_window.destroy(), self.add_schedule_dialog()]).pack(side='left', padx=5)
            
            if schedules:  # 只有在有排程時才顯示移除按鈕
                ttk.Button(left_buttons, text="➖ 移除排程", 
                          command=lambda: [schedule_window.destroy(), self.remove_schedule_dialog()]).pack(side='left', padx=5)
            
            # 右側按鈕（控制）
            right_buttons = ttk.Frame(button_frame)
            right_buttons.pack(side='right')
            
            ttk.Button(right_buttons, text="🔄 重新整理", 
                      command=lambda: [schedule_window.destroy(), self.show_schedules()]).pack(side='left', padx=5)
            ttk.Button(right_buttons, text="關閉", 
                      command=schedule_window.destroy).pack(side='left', padx=5)
            
            # 說明框架
            info_frame = ttk.LabelFrame(main_frame, text="24小時循環說明", padding="10")
            info_frame.pack(fill='x', pady=(10, 0))
            
            info_text = """📍 24小時循環排程邏輯：
• 排程週期：每天 08:00 開始新的24小時週期（08:00 ~ 次日07:59）
• 狀態計算：基於當前週期內的時間位置判斷排程狀態
• 自動重置：每天08:00所有「已完成」排程重置為「等待中」

🕐 狀態示例：
• 現在14:00，排程09:00 → ✅已完成  • 現在14:00，排程20:00 → ⏳等待中
• 現在06:00，排程22:00 → ✅已完成  • 現在06:00，排程04:00 → ✅已完成"""
            
            ttk.Label(info_frame, text=info_text, justify='left', 
                     font=('Arial', 9), foreground='#555').pack(anchor='w')
            
        except Exception as e:
            messagebox.showerror("錯誤", f"顯示排程失敗: {e}")
    
    def _get_schedule_status(self, time_str, current_hour, current_minute):
        """
        判斷排程狀態（24小時循環，每天8點重新開始）
        
        24小時循環邏輯：
        - 每天08:00為一個新的24小時週期開始
        - 週期範圍：08:00 -> 次日07:59
        - 已完成的排程在每天08:00重新變為等待中
        
        範例：
        - 當前14:00，排程09:00 -> 已完成（同一週期內，已過時間）
        - 當前14:00，排程20:00 -> 等待中（同一週期內，未到時間）
        - 當前06:00，排程22:00 -> 已完成（昨天週期內的排程）
        - 當前06:00，排程04:00 -> 已完成（今天早上週期內，已過時間）
        """
        try:
            if not time_str or time_str == 'N/A':
                return "❓ 無效時間"
            
            # 解析排程時間
            schedule_parts = time_str.split(':')
            if len(schedule_parts) != 2:
                return "❓ 格式錯誤"
            
            schedule_hour = int(schedule_parts[0])
            schedule_minute = int(schedule_parts[1])
            
            # 當前時間與排程時間的精確比較
            current_time_exact = f"{current_hour:02d}:{current_minute:02d}"
            
            # 如果正好是排程時間（精確到分鐘）
            if current_time_exact == time_str:
                return "🔄 執行中"
            
            # 將時間轉換為從早上8點開始的相對分鐘數
            def get_cycle_minutes(hour, minute):
                """獲取從當前週期開始（8點）的分鐘數"""
                if hour >= 8:
                    # 今天8點後的時間
                    return (hour - 8) * 60 + minute
                else:
                    # 次日0點到8點前的時間（相當於昨天8點後16-24小時）
                    return (hour + 16) * 60 + minute
            
            current_cycle_minutes = get_cycle_minutes(current_hour, current_minute)
            schedule_cycle_minutes = get_cycle_minutes(schedule_hour, schedule_minute)
            
            # 比較在24小時週期內的位置
            if schedule_cycle_minutes < current_cycle_minutes:
                return "✅ 已完成"
            elif schedule_cycle_minutes > current_cycle_minutes:
                return "⏳ 等待中"
            else:
                # 理論上不會到這裡，因為上面已經檢查了精確相等
                return "⏳ 等待中"
                        
        except (ValueError, IndexError):
            return "❓ 格式錯誤"
    
    def add_schedule_dialog(self):
        """新增排程對話框"""
        try:
            # 創建對話框窗口
            dialog = tk.Toplevel(self.root)
            dialog.title("新增排程")
            dialog.geometry("400x250")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # 居中顯示
            dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
            
            # 主框架
            main_frame = ttk.Frame(dialog, padding="20")
            main_frame.pack(fill='both', expand=True)
            
            # 標題
            ttk.Label(main_frame, text="新增排程", font=('Arial', 14, 'bold')).pack(pady=(0, 20))
            
            # 時間輸入
            time_frame = ttk.Frame(main_frame)
            time_frame.pack(fill='x', pady=10)
            
            ttk.Label(time_frame, text="執行時間:").pack(side='left')
            
            # 小時選擇
            hour_var = tk.StringVar()
            hour_combo = ttk.Combobox(time_frame, textvariable=hour_var, width=3, state='readonly')
            hour_combo['values'] = [f"{i:02d}" for i in range(24)]
            hour_combo.pack(side='left', padx=(10, 5))
            hour_combo.set("09")
            
            ttk.Label(time_frame, text=":").pack(side='left')
            
            # 分鐘選擇
            minute_var = tk.StringVar()
            minute_combo = ttk.Combobox(time_frame, textvariable=minute_var, width=3, state='readonly')
            minute_combo['values'] = [f"{i:02d}" for i in range(0, 60, 5)]  # 每5分鐘一個選項
            minute_combo.pack(side='left', padx=(5, 10))
            minute_combo.set("00")
            
            # 活動選擇
            campaign_frame = ttk.Frame(main_frame)
            campaign_frame.pack(fill='x', pady=10)
            
            ttk.Label(campaign_frame, text="選擇活動:").pack(side='left')
            
            campaign_var = tk.StringVar()
            campaign_combo = ttk.Combobox(campaign_frame, textvariable=campaign_var, width=10, state='readonly')
            campaign_combo['values'] = ['A', 'B', 'C', 'D', 'E']
            campaign_combo.pack(side='left', padx=(10, 0))
            campaign_combo.set("A")
            
            # 按鈕框架
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill='x', pady=20)
            
            def add_schedule():
                hour = hour_var.get()
                minute = minute_var.get()
                campaign = campaign_var.get()
                
                if not hour or not minute or not campaign:
                    messagebox.showwarning("警告", "請選擇時間和活動")
                    return
                
                time_str = f"{hour}:{minute}"
                
                # 檢查是否已存在相同排程
                existing_schedules = self.config_manager.get_schedules()
                for schedule in existing_schedules:
                    if schedule['time'] == time_str and schedule['campaign'] == campaign:
                        messagebox.showwarning("警告", f"排程 {time_str} - 活動 {campaign} 已存在")
                        return
                
                # 新增排程
                success = self.config_manager.add_schedule(time_str, campaign)
                if success:
                    self.queue_status_update(f"✅ 已新增排程: {time_str} - 活動 {campaign}")
                    self.refresh_schedule_status()
                    dialog.destroy()
                else:
                    messagebox.showerror("錯誤", "新增排程失敗")
            
            def cancel():
                dialog.destroy()
            
            ttk.Button(button_frame, text="確定", command=add_schedule).pack(side='right', padx=5)
            ttk.Button(button_frame, text="取消", command=cancel).pack(side='right', padx=5)
            
        except Exception as e:
            messagebox.showerror("錯誤", f"開啟新增排程對話框失敗: {e}")
    
    def remove_schedule_dialog(self):
        """移除排程對話框"""
        try:
            schedules = self.config_manager.get_schedules()
            if not schedules:
                messagebox.showinfo("提示", "目前沒有任何排程")
                return
            
            # 創建對話框窗口
            dialog = tk.Toplevel(self.root)
            dialog.title("移除排程")
            dialog.geometry("500x400")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # 居中顯示
            dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
            
            # 主框架
            main_frame = ttk.Frame(dialog, padding="20")
            main_frame.pack(fill='both', expand=True)
            
            # 標題
            ttk.Label(main_frame, text="移除排程", font=('Arial', 14, 'bold')).pack(pady=(0, 20))
            
            # 排程列表框架
            list_frame = ttk.LabelFrame(main_frame, text=f"現有排程 ({len(schedules)} 個)", padding="10")
            list_frame.pack(fill='both', expand=True, pady=10)
            
            # 創建列表框和滾動條
            listbox_frame = ttk.Frame(list_frame)
            listbox_frame.pack(fill='both', expand=True)
            
            scrollbar = ttk.Scrollbar(listbox_frame)
            scrollbar.pack(side='right', fill='y')
            
            schedule_listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, 
                                        selectmode='extended', font=('Consolas', 10))
            schedule_listbox.pack(side='left', fill='both', expand=True)
            scrollbar.config(command=schedule_listbox.yview)
            
            # 填充排程列表
            for i, schedule in enumerate(schedules):
                time_str = schedule.get('time', 'N/A')
                campaign = schedule.get('campaign', 'N/A')
                schedule_listbox.insert('end', f"{i+1:2d}. {time_str} - 活動 {campaign}")
            
            # 操作說明
            ttk.Label(main_frame, text="選擇要移除的排程（可多選），然後點擊「移除選中」", 
                     foreground='gray').pack(pady=5)
            
            # 按鈕框架
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill='x', pady=20)
            
            def remove_selected():
                selected_indices = schedule_listbox.curselection()
                if not selected_indices:
                    messagebox.showwarning("警告", "請選擇要移除的排程")
                    return
                
                # 確認對話框
                count = len(selected_indices)
                result = messagebox.askyesno("確認移除", 
                                           f"確定要移除選中的 {count} 個排程嗎？")
                if not result:
                    return
                
                # 從後往前移除，避免索引變化問題
                removed_count = 0
                for index in reversed(selected_indices):
                    schedule = schedules[index]
                    time_str = schedule['time']
                    campaign = schedule['campaign']
                    
                    success = self.config_manager.remove_schedule(time_str, campaign)
                    if success:
                        removed_count += 1
                        self.queue_status_update(f"✅ 已移除排程: {time_str} - 活動 {campaign}")
                
                if removed_count > 0:
                    self.refresh_schedule_status()
                    dialog.destroy()
                    messagebox.showinfo("完成", f"成功移除 {removed_count} 個排程")
                else:
                    messagebox.showerror("錯誤", "移除排程失敗")
            
            def remove_all():
                result = messagebox.askyesno("確認清空", 
                                           f"確定要清空所有 {len(schedules)} 個排程嗎？\n⚠️ 此操作不可復原！")
                if not result:
                    return
                
                success = self.config_manager.clear_all_schedules()
                if success:
                    self.queue_status_update("✅ 已清空所有排程")
                    self.refresh_schedule_status()
                    dialog.destroy()
                    messagebox.showinfo("完成", "所有排程已清空")
                else:
                    messagebox.showerror("錯誤", "清空排程失敗")
            
            def cancel():
                dialog.destroy()
            
            ttk.Button(button_frame, text="移除選中", command=remove_selected).pack(side='left', padx=5)
            ttk.Button(button_frame, text="清空全部", command=remove_all).pack(side='left', padx=5)
            ttk.Button(button_frame, text="取消", command=cancel).pack(side='right', padx=5)
            
        except Exception as e:
            messagebox.showerror("錯誤", f"開啟移除排程對話框失敗: {e}")
    
    def add_group_dialog(self):
        """添加群組對話框"""
        try:
            # 創建對話框窗口
            dialog = tk.Toplevel(self.root)
            dialog.title("添加群組")
            dialog.geometry("450x300")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # 居中顯示
            dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
            
            # 主框架
            main_frame = ttk.Frame(dialog, padding="20")
            main_frame.pack(fill='both', expand=True)
            
            # 標題
            ttk.Label(main_frame, text="添加群組到目標列表", font=('Arial', 14, 'bold')).pack(pady=(0, 20))
            
            # 群組ID輸入方式選擇
            method_frame = ttk.LabelFrame(main_frame, text="添加方式", padding="10")
            method_frame.pack(fill='x', pady=10)
            
            method_var = tk.StringVar(value="manual")
            
            ttk.Radiobutton(method_frame, text="手動輸入群組ID", 
                          variable=method_var, value="manual").pack(anchor='w')
            
            scan_available = len(self.scanned_groups) > 0
            scan_status = f"從掃描結果中選擇 ({len(self.scanned_groups)} 個群組)" if scan_available else "從掃描結果中選擇 (需要先掃描)"
            scan_radio = ttk.Radiobutton(method_frame, text=scan_status, 
                          variable=method_var, value="select")
            scan_radio.pack(anchor='w')
            if not scan_available:
                scan_radio.config(state='disabled')
            
            # 手動輸入框架
            manual_frame = ttk.LabelFrame(main_frame, text="手動輸入", padding="10")
            manual_frame.pack(fill='x', pady=10)
            
            ttk.Label(manual_frame, text="群組ID (負數):").pack(anchor='w')
            group_id_var = tk.StringVar()
            id_entry = ttk.Entry(manual_frame, textvariable=group_id_var, width=20)
            id_entry.pack(fill='x', pady=5)
            
            ttk.Label(manual_frame, text="群組類型:", foreground='gray').pack(anchor='w', pady=(10, 0))
            type_var = tk.StringVar(value="target")
            ttk.Radiobutton(manual_frame, text="目標廣播群組", 
                          variable=type_var, value="target").pack(anchor='w')
            ttk.Radiobutton(manual_frame, text="控制群組", 
                          variable=type_var, value="control").pack(anchor='w')
            
            # 按鈕框架
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill='x', pady=20)
            
            def add_group():
                try:
                    if method_var.get() == "manual":
                        group_id_str = group_id_var.get().strip()
                        if not group_id_str:
                            messagebox.showwarning("警告", "請輸入群組ID")
                            return
                        
                        try:
                            group_id = int(group_id_str)
                        except ValueError:
                            messagebox.showerror("錯誤", "群組ID必須是數字")
                            return
                        
                        if group_id >= 0:
                            messagebox.showwarning("警告", "群組ID通常是負數")
                            return
                        
                        group_type = type_var.get()
                        
                        if group_type == "target":
                            # 檢查是否已存在
                            target_groups = self.config_manager.get_target_groups()
                            if group_id in target_groups:
                                messagebox.showwarning("警告", f"群組 {group_id} 已在目標列表中")
                                return
                            
                            success = self.config_manager.add_target_group(group_id)
                            if success:
                                self.queue_status_update(f"✅ 已添加目標群組: {group_id}")
                                self.refresh_groups()
                                dialog.destroy()
                            else:
                                messagebox.showerror("錯誤", "添加群組失敗")
                        
                        elif group_type == "control":
                            success = self.config_manager.set_control_group(group_id)
                            if success:
                                self.queue_status_update(f"✅ 已設定控制群組: {group_id}")
                                self.refresh_groups()
                                dialog.destroy()
                            else:
                                messagebox.showerror("錯誤", "設定控制群組失敗")
                    
                    else:
                        # 從掃描結果選擇
                        if not self.scanned_groups:
                            messagebox.showwarning("警告", "請先掃描群組")
                            return
                        
                        dialog.destroy()
                        self._show_group_selection_dialog()
                        
                except Exception as e:
                    messagebox.showerror("錯誤", f"添加群組時發生錯誤: {e}")
            
            def cancel():
                dialog.destroy()
            
            ttk.Button(button_frame, text="確定", command=add_group).pack(side='right', padx=5)
            ttk.Button(button_frame, text="取消", command=cancel).pack(side='right', padx=5)
            
        except Exception as e:
            messagebox.showerror("錯誤", f"開啟添加群組對話框失敗: {e}")
    
    def _show_group_selection_dialog(self):
        """顯示群組選擇對話框"""
        try:
            # 創建對話框窗口
            dialog = tk.Toplevel(self.root)
            dialog.title("選擇群組")
            dialog.geometry("800x600")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # 居中顯示
            dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
            
            # 主框架
            main_frame = ttk.Frame(dialog, padding="20")
            main_frame.pack(fill='both', expand=True)
            
            # 標題
            ttk.Label(main_frame, text="從掃描結果選擇群組", font=('Arial', 14, 'bold')).pack(pady=(0, 20))
            
            # 操作類型選擇
            action_frame = ttk.LabelFrame(main_frame, text="操作類型", padding="10")
            action_frame.pack(fill='x', pady=10)
            
            action_var = tk.StringVar(value="add_target")
            ttk.Radiobutton(action_frame, text="添加為目標群組", 
                          variable=action_var, value="add_target").pack(anchor='w')
            ttk.Radiobutton(action_frame, text="設定為控制群組", 
                          variable=action_var, value="set_control").pack(anchor='w')
            
            # 群組列表框架
            list_frame = ttk.LabelFrame(main_frame, text=f"可選群組 (共 {len(self.scanned_groups)} 個)", padding="10")
            list_frame.pack(fill='both', expand=True, pady=10)
            
            # 創建框架來正確放置滾動條
            selection_tree_frame = ttk.Frame(list_frame)
            selection_tree_frame.pack(fill='both', expand=True)
            
            # 創建Treeview
            columns = ('選擇', '編號', '群組ID', '群組名稱', '類型', '成員數', '狀態')
            tree = ttk.Treeview(selection_tree_frame, columns=columns, show='tree headings', height=12, selectmode='extended')
            
            # 設定欄位
            tree.heading('#0', text='')
            tree.heading('選擇', text='')
            tree.heading('編號', text='編號')
            tree.heading('群組ID', text='群組ID')
            tree.heading('群組名稱', text='群組名稱')
            tree.heading('類型', text='類型')
            tree.heading('成員數', text='成員數')
            tree.heading('狀態', text='狀態')
            
            tree.column('#0', width=30, minwidth=20)
            tree.column('選擇', width=50, anchor='center', minwidth=40)
            tree.column('編號', width=70, anchor='center', minwidth=50)
            tree.column('群組ID', width=130, anchor='center', minwidth=100)
            tree.column('群組名稱', width=220, anchor='w', minwidth=150)
            tree.column('類型', width=90, anchor='center', minwidth=70)
            tree.column('成員數', width=80, anchor='center', minwidth=60)
            tree.column('狀態', width=120, anchor='center', minwidth=90)
            
            # 滾動條
            selection_scrollbar_y = ttk.Scrollbar(selection_tree_frame, orient='vertical', command=tree.yview)
            selection_scrollbar_x = ttk.Scrollbar(selection_tree_frame, orient='horizontal', command=tree.xview)
            tree.configure(yscrollcommand=selection_scrollbar_y.set, xscrollcommand=selection_scrollbar_x.set)
            
            # 使用grid布局正確放置組件
            tree.grid(row=0, column=0, sticky='nsew')
            selection_scrollbar_y.grid(row=0, column=1, sticky='ns')
            selection_scrollbar_x.grid(row=1, column=0, sticky='ew')
            
            # 配置grid權重
            selection_tree_frame.grid_rowconfigure(0, weight=1)
            selection_tree_frame.grid_columnconfigure(0, weight=1)
            
            # 填充數據
            target_groups = self.config_manager.get_target_groups()
            control_group = self.config_manager.get_control_group()
            
            for i, dialog_data in enumerate(self.scanned_groups, 1):
                group_id = dialog_data.get('id')
                title = dialog_data.get('title', 'N/A')
                group_type = dialog_data.get('type', 'N/A')
                participant_count = dialog_data.get('participant_count', 0)
                
                # 判斷狀態
                if group_id in target_groups:
                    status = "✅ 目標群組"
                elif group_id == control_group:
                    status = "⚙️ 控制群組"
                else:
                    status = "⭕ 未使用"
                
                # 格式化顯示數據
                formatted_title = title[:30] + '...' if len(title) > 30 else title
                formatted_type = group_type[:8] + '...' if len(group_type) > 8 else group_type
                formatted_count = f"{participant_count:,}" if participant_count > 0 else "N/A"
                
                tree.insert('', 'end', values=(
                    '',  # 選擇欄位
                    f"{i:03d}",
                    str(group_id),
                    formatted_title,
                    formatted_type,
                    formatted_count,
                    status
                ))
            
            # 操作說明
            ttk.Label(main_frame, text="選擇群組後點擊「執行操作」，支援多選（Ctrl+點擊）", 
                     foreground='gray').pack(pady=5)
            
            # 按鈕框架
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill='x', pady=20)
            
            def execute_action():
                selected_items = tree.selection()
                if not selected_items:
                    messagebox.showwarning("警告", "請選擇群組")
                    return
                
                action = action_var.get()
                
                if action == "set_control" and len(selected_items) > 1:
                    messagebox.showwarning("警告", "控制群組只能選擇一個")
                    return
                
                # 獲取選中的群組
                selected_groups = []
                for item in selected_items:
                    values = tree.item(item)['values']
                    group_id = int(values[2])  # 群組ID在第3列
                    group_name = values[3]     # 群組名稱在第4列
                    current_status = values[6] # 狀態在第7列
                    
                    if action == "add_target" and "目標群組" not in current_status:
                        selected_groups.append({'id': group_id, 'name': group_name})
                    elif action == "set_control":
                        selected_groups.append({'id': group_id, 'name': group_name})
                
                if not selected_groups:
                    if action == "add_target":
                        messagebox.showinfo("提示", "選中的群組都已經是目標群組")
                    else:
                        messagebox.showinfo("提示", "請選擇群組")
                    return
                
                # 執行操作
                if action == "add_target":
                    self._execute_add_groups(selected_groups, dialog)
                elif action == "set_control":
                    self._execute_set_control(selected_groups[0], dialog)
            
            def cancel():
                dialog.destroy()
            
            def scan_again():
                dialog.destroy()
                self.scan_groups()
            
            ttk.Button(button_frame, text="執行操作", command=execute_action).pack(side='left', padx=5)
            ttk.Button(button_frame, text="🔄 重新掃描", command=scan_again).pack(side='left', padx=5)
            ttk.Button(button_frame, text="取消", command=cancel).pack(side='right', padx=5)
            
        except Exception as e:
            messagebox.showerror("錯誤", f"開啟群組選擇對話框失敗: {e}")
    
    def _execute_add_groups(self, selected_groups, dialog):
        """執行添加群組操作"""
        try:
            # 確認對話框
            group_list = "\n".join([f"• {group['name']} ({group['id']})" for group in selected_groups[:5]])
            if len(selected_groups) > 5:
                group_list += f"\n... 還有 {len(selected_groups) - 5} 個群組"
            
            result = messagebox.askyesno("確認添加", 
                                       f"確定要添加以下 {len(selected_groups)} 個群組為目標群組嗎？\n\n{group_list}")
            if not result:
                return
            
            # 添加群組
            added_count = 0
            for group in selected_groups:
                success = self.config_manager.add_target_group(group['id'])
                if success:
                    added_count += 1
                    self.queue_status_update(f"✅ 已添加目標群組: {group['name']} ({group['id']})")
            
            if added_count > 0:
                self.refresh_groups()
                messagebox.showinfo("完成", f"成功添加 {added_count} 個目標群組")
                dialog.destroy()
            else:
                messagebox.showerror("錯誤", "添加群組失敗")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"添加群組時發生錯誤: {e}")
    
    def _execute_set_control(self, group, dialog):
        """執行設定控制群組操作"""
        try:
            # 確認對話框
            result = messagebox.askyesno("確認設定", 
                                       f"確定要將以下群組設為控制群組嗎？\n\n"
                                       f"群組名稱: {group['name']}\n"
                                       f"群組ID: {group['id']}\n\n"
                                       f"控制群組用於接收系統通知和廣播結果。")
            if not result:
                return
            
            # 設定控制群組
            success = self.config_manager.set_control_group(group['id'])
            if success:
                self.queue_status_update(f"✅ 已設定控制群組: {group['name']} ({group['id']})")
                self.refresh_groups()
                messagebox.showinfo("完成", f"成功設定控制群組: {group['name']}")
                dialog.destroy()
            else:
                messagebox.showerror("錯誤", "設定控制群組失敗")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"設定控制群組時發生錯誤: {e}")
    
    def remove_group_dialog(self):
        """移除群組對話框"""
        try:
            target_groups = self.config_manager.get_target_groups()
            control_group = self.config_manager.get_control_group()
            
            if not target_groups and not control_group:
                messagebox.showinfo("提示", "目前沒有任何群組")
                return
            
            # 創建對話框窗口
            dialog = tk.Toplevel(self.root)
            dialog.title("移除群組")
            dialog.geometry("500x400")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # 居中顯示
            dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
            
            # 主框架
            main_frame = ttk.Frame(dialog, padding="20")
            main_frame.pack(fill='both', expand=True)
            
            # 標題
            ttk.Label(main_frame, text="移除群組", font=('Arial', 14, 'bold')).pack(pady=(0, 20))
            
            # 群組列表框架
            total_groups = len(target_groups) + (1 if control_group else 0)
            list_frame = ttk.LabelFrame(main_frame, text=f"現有群組 ({total_groups} 個)", padding="10")
            list_frame.pack(fill='both', expand=True, pady=10)
            
            # 創建列表框和滾動條
            listbox_frame = ttk.Frame(list_frame)
            listbox_frame.pack(fill='both', expand=True)
            
            scrollbar = ttk.Scrollbar(listbox_frame)
            scrollbar.pack(side='right', fill='y')
            
            group_listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set, 
                                     selectmode='extended', font=('Consolas', 10))
            group_listbox.pack(side='left', fill='both', expand=True)
            scrollbar.config(command=group_listbox.yview)
            
            # 填充群組列表
            group_items = []
            
            # 添加目標群組
            for i, group_id in enumerate(target_groups):
                item_text = f"目標群組 - {group_id}"
                group_listbox.insert('end', item_text)
                group_items.append(('target', group_id))
            
            # 添加控制群組
            if control_group and control_group != 0:
                item_text = f"控制群組 - {control_group}"
                group_listbox.insert('end', item_text)
                group_items.append(('control', control_group))
            
            # 操作說明
            ttk.Label(main_frame, text="選擇要移除的群組（可多選），然後點擊「移除選中」", 
                     foreground='gray').pack(pady=5)
            
            # 按鈕框架
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill='x', pady=20)
            
            def remove_selected():
                selected_indices = group_listbox.curselection()
                if not selected_indices:
                    messagebox.showwarning("警告", "請選擇要移除的群組")
                    return
                
                # 確認對話框
                count = len(selected_indices)
                result = messagebox.askyesno("確認移除", 
                                           f"確定要移除選中的 {count} 個群組嗎？")
                if not result:
                    return
                
                # 移除群組
                removed_count = 0
                for index in reversed(selected_indices):
                    group_type, group_id = group_items[index]
                    
                    if group_type == 'target':
                        success = self.config_manager.remove_target_group(group_id)
                        if success:
                            removed_count += 1
                            self.queue_status_update(f"✅ 已移除目標群組: {group_id}")
                    
                    elif group_type == 'control':
                        success = self.config_manager.set_control_group(0)  # 設為0表示清除
                        if success:
                            removed_count += 1
                            self.queue_status_update(f"✅ 已清除控制群組: {group_id}")
                
                if removed_count > 0:
                    self.refresh_groups()
                    dialog.destroy()
                    messagebox.showinfo("完成", f"成功移除 {removed_count} 個群組")
                else:
                    messagebox.showerror("錯誤", "移除群組失敗")
            
            def clear_all():
                result = messagebox.askyesno("確認清空", 
                                           f"確定要清空所有 {total_groups} 個群組嗎？\n⚠️ 此操作不可復原！")
                if not result:
                    return
                
                removed_count = 0
                
                # 清空目標群組
                for group_id in target_groups[:]:  # 使用切片複製避免修改過程中列表變化
                    success = self.config_manager.remove_target_group(group_id)
                    if success:
                        removed_count += 1
                
                # 清空控制群組
                if control_group and control_group != 0:
                    success = self.config_manager.set_control_group(0)
                    if success:
                        removed_count += 1
                
                if removed_count > 0:
                    self.queue_status_update("✅ 已清空所有群組")
                    self.refresh_groups()
                    dialog.destroy()
                    messagebox.showinfo("完成", f"成功清空 {removed_count} 個群組")
                else:
                    messagebox.showerror("錯誤", "清空群組失敗")
            
            def cancel():
                dialog.destroy()
            
            ttk.Button(button_frame, text="移除選中", command=remove_selected).pack(side='left', padx=5)
            ttk.Button(button_frame, text="清空全部", command=clear_all).pack(side='left', padx=5)
            ttk.Button(button_frame, text="取消", command=cancel).pack(side='right', padx=5)
            
        except Exception as e:
            messagebox.showerror("錯誤", f"開啟移除群組對話框失敗: {e}")
    
    def manage_groups_dialog(self):
        """群組管理對話框"""
        try:
            # 創建對話框窗口
            dialog = tk.Toplevel(self.root)
            dialog.title("群組管理")
            dialog.geometry("700x600")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # 居中顯示
            dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
            
            # 主框架
            main_frame = ttk.Frame(dialog, padding="20")
            main_frame.pack(fill='both', expand=True)
            
            # 標題
            ttk.Label(main_frame, text="群組管理中心", font=('Arial', 16, 'bold')).pack(pady=(0, 20))
            
            # 創建筆記本控件
            notebook = ttk.Notebook(main_frame)
            notebook.pack(fill='both', expand=True, pady=10)
            
            # 目標群組頁籤
            target_frame = ttk.Frame(notebook)
            notebook.add(target_frame, text='🎯 目標群組')
            
            # 控制群組頁籤  
            control_frame = ttk.Frame(notebook)
            notebook.add(control_frame, text='⚙️ 控制群組')
            
            # 群組掃描頁籤
            scan_frame = ttk.Frame(notebook)
            notebook.add(scan_frame, text='🌐 群組掃描')
            
            # 填充目標群組頁籤
            self._create_target_groups_tab(target_frame)
            
            # 填充控制群組頁籤
            self._create_control_group_tab(control_frame)
            
            # 填充掃描頁籤
            self._create_scan_tab(scan_frame)
            
            # 底部按鈕
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill='x', pady=20)
            
            ttk.Button(button_frame, text="關閉", command=dialog.destroy).pack(side='right', padx=5)
            ttk.Button(button_frame, text="重新整理", 
                      command=lambda: [dialog.destroy(), self.manage_groups_dialog()]).pack(side='right', padx=5)
            
        except Exception as e:
            messagebox.showerror("錯誤", f"開啟群組管理對話框失敗: {e}")
    
    def _create_target_groups_tab(self, parent):
        """創建目標群組頁籤內容"""
        target_groups = self.config_manager.get_target_groups()
        
        # 資訊框架
        info_frame = ttk.Frame(parent, padding="10")
        info_frame.pack(fill='x')
        
        ttk.Label(info_frame, text=f"目標群組數量: {len(target_groups)}", 
                 font=('Arial', 12, 'bold')).pack(side='left')
        
        # 列表框架
        list_frame = ttk.LabelFrame(parent, text="目標群組列表", padding="10")
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        if target_groups:
            target_text = scrolledtext.ScrolledText(list_frame, height=15, font=('Consolas', 10))
            target_text.pack(fill='both', expand=True)
            
            target_text.insert('end', f"{'序號':<4} {'群組ID':<15} {'狀態'}\n")
            target_text.insert('end', "-" * 35 + "\n")
            
            for i, group_id in enumerate(target_groups):
                status = "✅ 正常" if group_id != 0 else "❌ 無效"
                target_text.insert('end', f"{i+1:2d}.  {str(group_id):<15} {status}\n")
            
            target_text.config(state='disabled')
        else:
            ttk.Label(list_frame, text="目前沒有設定目標群組", 
                     font=('Arial', 12), foreground='gray').pack(expand=True)
    
    def _create_control_group_tab(self, parent):
        """創建控制群組頁籤內容"""
        control_group = self.config_manager.get_control_group()
        
        # 資訊框架
        info_frame = ttk.Frame(parent, padding="10")
        info_frame.pack(fill='x')
        
        if control_group and control_group != 0:
            ttk.Label(info_frame, text=f"控制群組: {control_group}", 
                     font=('Arial', 12, 'bold'), foreground='green').pack()
        else:
            ttk.Label(info_frame, text="未設定控制群組", 
                     font=('Arial', 12, 'bold'), foreground='red').pack()
        
        # 說明框架
        desc_frame = ttk.LabelFrame(parent, text="控制群組說明", padding="10")
        desc_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        desc_text = """控制群組功能:

• 接收廣播執行結果通知
• 接收排程執行狀態報告  
• 接收系統錯誤警告
• 管理員指令接收

設定建議:
• 建議設定為管理員專用群組
• 確保機器人在該群組有發送訊息權限
• 建議群組ID為負數"""
        
        ttk.Label(desc_frame, text=desc_text, justify='left', foreground='gray').pack(anchor='w')
    
    def _create_scan_tab(self, parent):
        """創建掃描頁籤內容"""
        # 說明框架
        info_frame = ttk.Frame(parent, padding="10")
        info_frame.pack(fill='x')
        
        ttk.Label(info_frame, text="群組掃描功能", font=('Arial', 12, 'bold')).pack()
        
        # 掃描按鈕
        scan_btn_frame = ttk.Frame(parent, padding="10")
        scan_btn_frame.pack(fill='x')
        
        ttk.Button(scan_btn_frame, text="🌐 開始掃描群組", 
                  command=self.scan_groups).pack()
        
        # 說明文字
        desc_frame = ttk.LabelFrame(parent, text="掃描說明", padding="10")
        desc_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        desc_text = """群組掃描功能:

• 掃描機器人可存取的所有群組和頻道
• 顯示群組ID、名稱、類型和成員數
• 方便選擇合適的群組作為目標或控制群組

注意事項:
• 需要先連接Telegram才能掃描
• 只會顯示機器人有權限的群組
• 掃描結果會在新視窗中顯示"""
        
        ttk.Label(desc_frame, text=desc_text, justify='left', foreground='gray').pack(anchor='w')
    
    def show_group_details(self):
        """顯示群組詳細資訊"""
        try:
            target_groups = self.config_manager.get_target_groups()
            control_group = self.config_manager.get_control_group()
            
            # 創建詳情視窗
            details_window = tk.Toplevel(self.root)
            details_window.title("群組詳細資訊")
            details_window.geometry("600x500")
            details_window.transient(self.root)
            
            # 主框架
            main_frame = ttk.Frame(details_window, padding="20")
            main_frame.pack(fill='both', expand=True)
            
            # 標題
            ttk.Label(main_frame, text="群組詳細資訊", font=('Arial', 14, 'bold')).pack(pady=(0, 20))
            
            # 統計資訊框架
            stats_frame = ttk.LabelFrame(main_frame, text="統計資訊", padding="10")
            stats_frame.pack(fill='x', pady=10)
            
            stats_text = f"""群組配置統計:

• 目標群組數量: {len(target_groups)} 個
• 控制群組: {'已設定' if control_group and control_group != 0 else '未設定'}
• 總計群組數: {len(target_groups) + (1 if control_group and control_group != 0 else 0)} 個

配置狀態: {'✅ 完整' if target_groups and control_group else '⚠️ 不完整'}"""
            
            ttk.Label(stats_frame, text=stats_text, justify='left').pack(anchor='w')
            
            # 詳細列表框架
            detail_frame = ttk.LabelFrame(main_frame, text="詳細列表", padding="10")
            detail_frame.pack(fill='both', expand=True, pady=10)
            
            detail_text = scrolledtext.ScrolledText(detail_frame, height=15, font=('Consolas', 10))
            detail_text.pack(fill='both', expand=True)
            
            # 添加詳細資訊
            detail_text.insert('end', f"{'類型':<10} {'群組ID':<15} {'狀態':<10} {'備註'}\n")
            detail_text.insert('end', "=" * 55 + "\n")
            
            # 目標群組
            if target_groups:
                for i, group_id in enumerate(target_groups):
                    status = "正常" if group_id != 0 else "無效"
                    remark = f"目標群組 #{i+1}"
                    detail_text.insert('end', f"{'目標群組':<10} {str(group_id):<15} {status:<10} {remark}\n")
            else:
                detail_text.insert('end', f"{'目標群組':<10} {'無':<15} {'未設定':<10} 需要設定廣播目標\n")
            
            # 控制群組
            if control_group and control_group != 0:
                detail_text.insert('end', f"{'控制群組':<10} {str(control_group):<15} {'正常':<10} 接收通知訊息\n")
            else:
                detail_text.insert('end', f"{'控制群組':<10} {'無':<15} {'未設定':<10} 建議設定以接收通知\n")
            
            detail_text.config(state='disabled')
            
            # 按鈕框架
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill='x', pady=20)
            
            ttk.Button(button_frame, text="關閉", command=details_window.destroy).pack(side='right', padx=5)
            
        except Exception as e:
            messagebox.showerror("錯誤", f"顯示群組詳情失敗: {e}")
    
    def scan_groups(self):
        """掃描可用群組"""
        if not self.is_connected:
            messagebox.showerror("錯誤", "請先連接Telegram")
            return
        
        self.queue_status_update("🔍 掃描可用群組...")
        task = self.submit_task(self._scan_groups())
    
    async def _scan_groups(self):
        """異步掃描群組"""
        try:
            if not self.client_manager:
                self.queue_status_update("❌ 客戶端未連接")
                return
            
            dialogs = await self.client_manager.get_dialogs()
            
            # 更新緩存
            self.scanned_groups = dialogs
            self.last_scan_time = datetime.now()
            
            self.queue_status_update(f"✅ 找到 {len(dialogs)} 個群組/頻道")
            
            # 顯示群組列表窗口
            def show_groups_window():
                self._show_scan_results_window(dialogs)
            
            # 在主線程中顯示窗口
            self.root.after(0, show_groups_window)
            
        except Exception as e:
            self.queue_status_update(f"❌ 掃描群組失敗: {e}")
    
    def _show_scan_results_window(self, dialogs):
        """顯示掃描結果窗口"""
        try:
            groups_window = tk.Toplevel(self.root)
            groups_window.title("群組掃描結果")
            groups_window.geometry("900x700")
            groups_window.transient(self.root)
            
            # 主框架
            main_frame = ttk.Frame(groups_window, padding="20")
            main_frame.pack(fill='both', expand=True)
            
            # 標題框架
            title_frame = ttk.Frame(main_frame)
            title_frame.pack(fill='x', pady=(0, 10))
            
            ttk.Label(title_frame, text=f"群組掃描結果 (共 {len(dialogs)} 個)", 
                     font=('Arial', 14, 'bold')).pack(side='left')
            
            scan_time = self.last_scan_time.strftime('%H:%M:%S') if self.last_scan_time else 'N/A'
            ttk.Label(title_frame, text=f"掃描時間: {scan_time}", 
                     foreground='gray').pack(side='right')
            
            # 操作提示框架
            tip_frame = ttk.Frame(main_frame)
            tip_frame.pack(fill='x', pady=(0, 10))
            
            ttk.Label(tip_frame, text="💡 提示：可以從下方列表選擇群組進行添加或移除操作", 
                     foreground='blue', font=('Arial', 9)).pack(side='left')
            
            # 群組列表框架
            list_frame = ttk.LabelFrame(main_frame, text="群組列表", padding="10")
            list_frame.pack(fill='both', expand=True, pady=10)
            
            # 創建框架來正確放置滾動條
            tree_frame = ttk.Frame(list_frame)
            tree_frame.pack(fill='both', expand=True)
            
            # 創建Treeview來顯示群組
            columns = ('編號', '群組ID', '群組名稱', '類型', '成員數', '狀態')
            tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15, selectmode='extended')
            
            # 設定欄位標題和寬度
            tree.heading('編號', text='編號')
            tree.heading('群組ID', text='群組ID')
            tree.heading('群組名稱', text='群組名稱')
            tree.heading('類型', text='類型')
            tree.heading('成員數', text='成員數')
            tree.heading('狀態', text='狀態')
            
            tree.column('編號', width=70, anchor='center', minwidth=50)
            tree.column('群組ID', width=130, anchor='center', minwidth=100)
            tree.column('群組名稱', width=250, anchor='w', minwidth=150)
            tree.column('類型', width=90, anchor='center', minwidth=70)
            tree.column('成員數', width=80, anchor='center', minwidth=60)
            tree.column('狀態', width=120, anchor='center', minwidth=90)
            
            # 創建滾動條
            scrollbar_y = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
            scrollbar_x = ttk.Scrollbar(tree_frame, orient='horizontal', command=tree.xview)
            tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
            
            # 使用grid布局正確放置組件
            tree.grid(row=0, column=0, sticky='nsew')
            scrollbar_y.grid(row=0, column=1, sticky='ns')
            scrollbar_x.grid(row=1, column=0, sticky='ew')
            
            # 配置grid權重
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)
            
            # 填充數據
            target_groups = self.config_manager.get_target_groups()
            control_group = self.config_manager.get_control_group()
            
            # 對群組進行排序：未使用 -> 目標群組 -> 控制群組
            def get_sort_key(dialog):
                group_id = dialog.get('id')
                if group_id in target_groups:
                    return (1, dialog.get('title', '').lower())  # 目標群組
                elif group_id == control_group:
                    return (2, dialog.get('title', '').lower())  # 控制群組
                else:
                    return (0, dialog.get('title', '').lower())  # 未使用
            
            sorted_dialogs = sorted(dialogs, key=get_sort_key)
            
            for i, dialog in enumerate(sorted_dialogs, 1):
                group_id = dialog.get('id')
                title = dialog.get('title', 'N/A')
                group_type = dialog.get('type', 'N/A')
                participant_count = dialog.get('participant_count', 0)
                
                # 判斷狀態
                if group_id in target_groups:
                    status = "✅ 目標群組"
                elif group_id == control_group:
                    status = "⚙️ 控制群組"
                else:
                    status = "⭕ 未使用"
                
                # 格式化顯示數據
                formatted_title = title[:35] + '...' if len(title) > 35 else title
                formatted_type = group_type[:8] + '...' if len(group_type) > 8 else group_type
                formatted_count = f"{participant_count:,}" if participant_count > 0 else "N/A"
                
                tree.insert('', 'end', values=(
                    f"{i:03d}",  # 編號，3位數字補零
                    str(group_id),
                    formatted_title,
                    formatted_type,
                    formatted_count,
                    status
                ))
            
            # 操作按鈕框架
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill='x', pady=20)
            
            # 左側按鈕
            left_buttons = ttk.Frame(button_frame)
            left_buttons.pack(side='left')
            
            ttk.Button(left_buttons, text="➕ 從選中添加", 
                      command=lambda: self._add_groups_from_selection(tree, groups_window)).pack(side='left', padx=5)
            ttk.Button(left_buttons, text="➖ 從選中移除", 
                      command=lambda: self._remove_groups_from_selection(tree, groups_window)).pack(side='left', padx=5)
            ttk.Button(left_buttons, text="⚙️ 設為控制群組", 
                      command=lambda: self._set_control_from_selection(tree, groups_window)).pack(side='left', padx=5)
            
            # 右側按鈕
            right_buttons = ttk.Frame(button_frame)
            right_buttons.pack(side='right')
            
            ttk.Button(right_buttons, text="🔄 重新掃描", 
                      command=lambda: [groups_window.destroy(), self.scan_groups()]).pack(side='left', padx=5)
            ttk.Button(right_buttons, text="💾 匯出列表", 
                      command=lambda: self._export_scan_results()).pack(side='left', padx=5)
            ttk.Button(right_buttons, text="關閉", 
                      command=groups_window.destroy).pack(side='left', padx=5)
            
            # 底部狀態列
            status_frame = ttk.Frame(main_frame)
            status_frame.pack(fill='x', pady=(10, 0))
            
            status_text = f"總計: {len(dialogs)} 個群組 | "
            status_text += f"目標群組: {len(target_groups)} 個 | "
            status_text += f"控制群組: {'已設定' if control_group and control_group != 0 else '未設定'}"
            
            ttk.Label(status_frame, text=status_text, foreground='gray', font=('Arial', 9)).pack(side='left')
            
        except Exception as e:
            messagebox.showerror("錯誤", f"顯示掃描結果失敗: {e}")
    
    def _add_groups_from_selection(self, tree, parent_window):
        """從選中的掃描結果添加群組"""
        try:
            selected_items = tree.selection()
            if not selected_items:
                messagebox.showwarning("警告", "請選擇要添加的群組")
                return
            
            # 獲取選中的群組資訊
            selected_groups = []
            for item in selected_items:
                values = tree.item(item)['values']
                group_id = int(values[1])  # 群組ID在第二列
                group_name = values[2]     # 群組名稱在第三列
                current_status = values[5] # 狀態在第六列
                
                # 跳過已經是目標群組的
                if "目標群組" not in current_status:
                    selected_groups.append({'id': group_id, 'name': group_name})
            
            if not selected_groups:
                messagebox.showinfo("提示", "選中的群組都已經是目標群組")
                return
            
            # 確認對話框
            group_list = "\n".join([f"• {group['name']} ({group['id']})" for group in selected_groups[:5]])
            if len(selected_groups) > 5:
                group_list += f"\n... 還有 {len(selected_groups) - 5} 個群組"
            
            result = messagebox.askyesno("確認添加", 
                                       f"確定要添加以下 {len(selected_groups)} 個群組為目標群組嗎？\n\n{group_list}")
            if not result:
                return
            
            # 添加群組
            added_count = 0
            for group in selected_groups:
                success = self.config_manager.add_target_group(group['id'])
                if success:
                    added_count += 1
                    self.queue_status_update(f"✅ 已添加目標群組: {group['name']} ({group['id']})")
            
            if added_count > 0:
                self.refresh_groups()
                messagebox.showinfo("完成", f"成功添加 {added_count} 個目標群組")
                
                # 刷新掃描窗口
                parent_window.destroy()
                self._show_scan_results_window(self.scanned_groups)
            else:
                messagebox.showerror("錯誤", "添加群組失敗")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"添加群組時發生錯誤: {e}")
    
    def _remove_groups_from_selection(self, tree, parent_window):
        """從選中的掃描結果移除群組"""
        try:
            selected_items = tree.selection()
            if not selected_items:
                messagebox.showwarning("警告", "請選擇要移除的群組")
                return
            
            # 獲取選中的群組資訊
            selected_groups = []
            for item in selected_items:
                values = tree.item(item)['values']
                group_id = int(values[1])  # 群組ID在第二列
                group_name = values[2]     # 群組名稱在第三列
                current_status = values[5] # 狀態在第六列
                
                # 只處理目標群組或控制群組
                if "目標群組" in current_status or "控制群組" in current_status:
                    group_type = "目標群組" if "目標群組" in current_status else "控制群組"
                    selected_groups.append({'id': group_id, 'name': group_name, 'type': group_type})
            
            if not selected_groups:
                messagebox.showinfo("提示", "選中的群組都不在使用中")
                return
            
            # 確認對話框
            group_list = "\n".join([f"• {group['name']} ({group['id']}) - {group['type']}" for group in selected_groups[:5]])
            if len(selected_groups) > 5:
                group_list += f"\n... 還有 {len(selected_groups) - 5} 個群組"
            
            result = messagebox.askyesno("確認移除", 
                                       f"確定要移除以下 {len(selected_groups)} 個群組嗎？\n\n{group_list}")
            if not result:
                return
            
            # 移除群組
            removed_count = 0
            for group in selected_groups:
                if group['type'] == "目標群組":
                    success = self.config_manager.remove_target_group(group['id'])
                    if success:
                        removed_count += 1
                        self.queue_status_update(f"✅ 已移除目標群組: {group['name']} ({group['id']})")
                elif group['type'] == "控制群組":
                    success = self.config_manager.set_control_group(0)
                    if success:
                        removed_count += 1
                        self.queue_status_update(f"✅ 已清除控制群組: {group['name']} ({group['id']})")
            
            if removed_count > 0:
                self.refresh_groups()
                messagebox.showinfo("完成", f"成功移除 {removed_count} 個群組")
                
                # 刷新掃描窗口
                parent_window.destroy()
                self._show_scan_results_window(self.scanned_groups)
            else:
                messagebox.showerror("錯誤", "移除群組失敗")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"移除群組時發生錯誤: {e}")
    
    def _set_control_from_selection(self, tree, parent_window):
        """從選中的掃描結果設定控制群組"""
        try:
            selected_items = tree.selection()
            if not selected_items:
                messagebox.showwarning("警告", "請選擇要設為控制群組的群組")
                return
            
            if len(selected_items) > 1:
                messagebox.showwarning("警告", "控制群組只能選擇一個")
                return
            
            # 獲取選中的群組資訊
            item = selected_items[0]
            values = tree.item(item)['values']
            group_id = int(values[1])  # 群組ID在第二列
            group_name = values[2]     # 群組名稱在第三列
            current_status = values[5] # 狀態在第六列
            
            # 確認對話框
            result = messagebox.askyesno("確認設定", 
                                       f"確定要將以下群組設為控制群組嗎？\n\n"
                                       f"群組名稱: {group_name}\n"
                                       f"群組ID: {group_id}\n\n"
                                       f"控制群組用於接收系統通知和廣播結果。")
            if not result:
                return
            
            # 設定控制群組
            success = self.config_manager.set_control_group(group_id)
            if success:
                self.queue_status_update(f"✅ 已設定控制群組: {group_name} ({group_id})")
                self.refresh_groups()
                messagebox.showinfo("完成", f"成功設定控制群組: {group_name}")
                
                # 刷新掃描窗口
                parent_window.destroy()
                self._show_scan_results_window(self.scanned_groups)
            else:
                messagebox.showerror("錯誤", "設定控制群組失敗")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"設定控制群組時發生錯誤: {e}")
    
    def _export_scan_results(self):
        """匯出掃描結果"""
        try:
            if not self.scanned_groups:
                messagebox.showwarning("警告", "沒有掃描結果可以匯出")
                return
            
            # 生成匯出內容
            export_content = "群組掃描結果\n"
            export_content += f"掃描時間: {self.last_scan_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            export_content += f"總計群組: {len(self.scanned_groups)} 個\n"
            export_content += "=" * 80 + "\n\n"
            
            target_groups = self.config_manager.get_target_groups()
            control_group = self.config_manager.get_control_group()
            
            for i, dialog in enumerate(self.scanned_groups, 1):
                group_id = dialog.get('id')
                title = dialog.get('title', 'N/A')
                group_type = dialog.get('type', 'N/A')
                participant_count = dialog.get('participant_count', 0)
                
                # 判斷狀態
                if group_id in target_groups:
                    status = "目標群組"
                elif group_id == control_group:
                    status = "控制群組"
                else:
                    status = "未使用"
                
                export_content += f"編號: {i:03d}\n"
                export_content += f"群組ID: {group_id}\n"
                export_content += f"群組名稱: {title}\n"
                export_content += f"類型: {group_type}\n"
                export_content += f"成員數: {participant_count}\n"
                export_content += f"狀態: {status}\n"
                export_content += "-" * 50 + "\n"
            
            # 保存檔案
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                title="匯出掃描結果",
                defaultextension=".txt",
                filetypes=[("文字檔案", "*.txt"), ("所有檔案", "*.*")],
                initialname=f"群組掃描結果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(export_content)
                
                messagebox.showinfo("完成", f"掃描結果已匯出到:\n{filename}")
                self.queue_status_update(f"📄 已匯出掃描結果: {filename}")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"匯出掃描結果失敗: {e}")
    
    def restart_system(self):
        """重啟系統"""
        result = messagebox.askyesno("確認重啟", 
                                   "這將重啟整個系統，包括：\\n"
                                   "1. 斷開所有連接\\n"
                                   "2. 重新載入配置\\n"
                                   "3. 清理狀態\\n\\n"
                                   "確定要繼續嗎？")
        if result:
            self.queue_status_update("🔄 開始系統重啟...")
            task = self.submit_task(self._restart_system())
    
    async def _restart_system(self):
        """異步重啟系統"""
        try:
            # 斷開連接
            if self.client_manager:
                await self.client_manager.disconnect()
                self.client_manager = None
            
            # 重置狀態
            self.broadcast_system = None
            self.is_connected = False
            
            # 重新載入配置
            self.root.after(0, self.load_config)
            
            self.queue_status_update("✅ 系統重啟完成")
            
        except Exception as e:
            self.queue_status_update(f"❌ 系統重啟失敗: {e}")
    
    def clear_status(self):
        """清空狀態"""
        self.status_text.delete(1.0, 'end')
        self.queue_status_update("🗑️ 狀態日誌已清空")
    
    def save_status(self):
        """保存狀態"""
        try:
            content = self.status_text.get(1.0, 'end')
            filename = f"gui_log_{int(time.time())}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            messagebox.showinfo("保存成功", f"狀態日誌已保存為 {filename}")
            self.queue_status_update(f"💾 日誌已保存: {filename}")
            
        except Exception as e:
            messagebox.showerror("保存失敗", f"保存日誌失敗: {e}")
    
    def on_closing(self):
        """關閉程序"""
        if messagebox.askokcancel("退出", "確定要退出系統嗎？"):
            self.queue_status_update("🛑 正在關閉系統...")
            self.running = False
            
            if self.client_manager:
                try:
                    task = self.submit_task(self.client_manager.disconnect())
                    if task:
                        task.result(timeout=5)  # 等待5秒完成斷開
                except:
                    pass
            
            self.root.destroy()

def main():
    """主函數"""
    root = tk.Tk()
    app = WorkingBroadcastGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.on_closing()

if __name__ == "__main__":
    main()