#!/usr/bin/env python3

import threading
import time
import schedule 
import logging
from datetime import datetime, timedelta
from PySide6.QtCore import QObject, Signal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Reminder(QObject):
    reminder_signal = Signal(dict)
    
    def __init__(self, schedule_manager):
        super().__init__()
        self.schedule_manager = schedule_manager
        self.reminder_thread = None
        self.running = False
        
    def start(self):
        if self.reminder_thread is not None and self.reminder_thread.is_alive():
            logging.warning("提醒线程已经在运行中")
            return False
        
        self.running = True
        self.reminder_thread = threading.Thread(target=self._reminder_loop)
        self.reminder_thread.daemon = True  
        self.reminder_thread.start()
        logging.info("提醒服务已启动")
        return True
    
    def stop(self):
        self.running = False
        if self.reminder_thread and self.reminder_thread.is_alive():
            self.reminder_thread.join(timeout=2.0)
            logging.info("提醒服务已停止")
            return True
        return False
    
    def _reminder_loop(self):
        schedule.every().day.at("00:00").do(self._schedule_daily_tasks)
        schedule.every().minute.do(self._check_reminders)
        self._schedule_daily_tasks()
        
        while self.running:
            schedule.run_pending()
            time.sleep(1)  
    
    def _schedule_daily_tasks(self):
        tasks = self.schedule_manager.get_today_tasks()
        logging.info(f"今日共有{len(tasks)}个任务")
    
    def _check_reminders(self):
        upcoming_tasks = self.schedule_manager.get_upcoming_reminders(minutes=30)
        
        for task in upcoming_tasks:
            self.reminder_signal.emit(task)
            logging.info(f"发出提醒: {task['title']}")
    
    def add_one_time_reminder(self, task_id, minutes_before=15):
        task = self.schedule_manager.get_task(task_id)
        if not task:
            logging.warning(f"未找到ID为{task_id}的任务")
            return False
            
        if not task.get("due_date"):
            logging.warning(f"任务'{task['title']}'没有截止日期")
            return False
            
        self.schedule_manager.update_task(task_id, reminder_time=minutes_before)
        logging.info(f"为任务'{task['title']}'添加了提前{minutes_before}分钟的提醒")
        return True
    
    def remove_reminder(self, task_id):
        task = self.schedule_manager.get_task(task_id)
        if not task:
            logging.warning(f"未找到ID为{task_id}的任务")
            return False
            
        if not task.get("reminder_time"):
            logging.warning(f"任务'{task['title']}'没有设置提醒")
            return False
            
        self.schedule_manager.update_task(task_id, reminder_time=None)
        logging.info(f"移除了任务'{task['title']}'的提醒")
        return True