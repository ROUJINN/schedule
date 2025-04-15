#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import time
import my_schedule as scheduler
import logging
from datetime import datetime, timedelta
from PyQt5.QtCore import QObject, pyqtSignal

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Reminder(QObject):
    """
    提醒功能类：负责任务的定时提醒
    使用QObject作为基类，以支持信号和槽机制
    """
    # 定义一个信号，当有需要提醒的任务时发出
    reminder_signal = pyqtSignal(dict)
    
    def __init__(self, schedule_manager):
        """
        初始化提醒管理器
        
        Args:
            schedule_manager: 日程管理器实例
        """
        super().__init__()
        self.schedule_manager = schedule_manager
        self.reminder_thread = None
        self.running = False
        
    def start(self):
        """启动提醒线程"""
        if self.reminder_thread is not None and self.reminder_thread.is_alive():
            logging.warning("提醒线程已经在运行中")
            return False
        
        self.running = True
        self.reminder_thread = threading.Thread(target=self._reminder_loop)
        self.reminder_thread.daemon = True  # 使线程成为守护线程，主程序结束时线程也会结束
        self.reminder_thread.start()
        logging.info("提醒服务已启动")
        return True
    
    def stop(self):
        """停止提醒线程"""
        self.running = False
        if self.reminder_thread and self.reminder_thread.is_alive():
            self.reminder_thread.join(timeout=2.0)  # 等待线程结束，最多等待2秒
            logging.info("提醒服务已停止")
            return True
        return False
    
    def _reminder_loop(self):
        """提醒线程的主循环"""
        # 每天凌晨重新加载当天的重复任务
        scheduler.every().day.at("00:00").do(self._schedule_daily_tasks)
        
        # 每分钟检查一次是否有需要提醒的任务
        scheduler.every().minute.do(self._check_reminders)
        
        # 初始加载当天任务
        self._schedule_daily_tasks()
        
        # 主循环
        while self.running:
            scheduler.run_pending()
            time.sleep(1)  # 休眠1秒以减少CPU使用率
    
    def _schedule_daily_tasks(self):
        """为当天的任务设置提醒"""
        tasks = self.schedule_manager.get_today_tasks()
        logging.info(f"今日共有{len(tasks)}个任务")
    
    def _check_reminders(self):
        """检查是否有需要提醒的任务"""
        # 获取未来30分钟内需要提醒的任务
        upcoming_tasks = self.schedule_manager.get_upcoming_reminders(minutes=30)
        
        for task in upcoming_tasks:
            # 发出提醒信号
            self.reminder_signal.emit(task)
            logging.info(f"发出提醒: {task['title']}")
    
    def add_one_time_reminder(self, task_id, minutes_before=15):
        """
        为特定任务添加一次性提醒
        
        Args:
            task_id: 任务ID
            minutes_before: 提前多少分钟提醒
            
        Returns:
            bool: 是否成功添加提醒
        """
        task = self.schedule_manager.get_task(task_id)
        if not task:
            logging.warning(f"未找到ID为{task_id}的任务")
            return False
            
        if not task.get("due_date"):
            logging.warning(f"任务'{task['title']}'没有截止日期")
            return False
            
        # 更新任务的提醒时间
        self.schedule_manager.update_task(task_id, reminder_time=minutes_before)
        logging.info(f"为任务'{task['title']}'添加了提前{minutes_before}分钟的提醒")
        return True
    
    def remove_reminder(self, task_id):
        """
        移除任务的提醒
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功移除提醒
        """
        task = self.schedule_manager.get_task(task_id)
        if not task:
            logging.warning(f"未找到ID为{task_id}的任务")
            return False
            
        if not task.get("reminder_time"):
            logging.warning(f"任务'{task['title']}'没有设置提醒")
            return False
            
        # 清除任务的提醒时间
        self.schedule_manager.update_task(task_id, reminder_time=None)
        logging.info(f"移除了任务'{task['title']}'的提醒")
        return True