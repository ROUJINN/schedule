#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import uuid
from datetime import datetime, timedelta
import logging
from SCRAPER import WebScraper
import asyncio

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Schedule:
    WORK = "工作"
    STUDY = "学习"
    LIFE = "生活"
    OTHER = "其他"
    
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"
    
    def __init__(self, data_file="data/tasks.json", pet_state=None):
        self.data_file = data_file
        self.tasks = []
        self.pet_state = pet_state
        self._load_tasks()
    
    def _load_tasks(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.tasks = json.load(f)
                logging.info(f"从{self.data_file}成功加载了{len(self.tasks)}个日程任务")
            else:
                os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False)
                logging.info(f"创建了新的任务文件:{self.data_file}")
        except Exception as e:
            logging.error(f"加载任务时出错: {e}")
            self.tasks = []
    
    def _save_tasks(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
            logging.info(f"成功保存了{len(self.tasks)}个日程任务")
        except Exception as e:
            logging.error(f"保存任务时出错: {e}")
    
    def add_task(self, title, description, category, priority, due_date, 
                 start_time=None, end_time=None, repeat=None, reminder_time=None):
        task_id = str(uuid.uuid4())
        
        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            logging.error("日期格式无效，应为 YYYY-MM-DD")
            return None
        
        task = {
            "id": task_id,
            "title": title,
            "description": description,
            "category": category,
            "priority": priority,
            "due_date": due_date,
            "start_time": start_time,
            "end_time": end_time,
            "repeat": repeat,
            "reminder_time": reminder_time,
            "completed": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.tasks.append(task)
        self._save_tasks()
        logging.info(f"添加了新任务: {title}")
        return task_id
    
    def update_task(self, task_id, **kwargs):
        for i, task in enumerate(self.tasks):
            if task["id"] == task_id:
                for key, value in kwargs.items():
                    if key in task:
                        task[key] = value
                
                self._save_tasks()
                logging.info(f"更新了任务: {task['title']}")
                return True
        
        logging.warning(f"未找到ID为{task_id}的任务")
        return False
    
    def delete_task(self, task_id):
        for i, task in enumerate(self.tasks):
            if task["id"] == task_id:
                deleted_task = self.tasks.pop(i)
                self._save_tasks()
                logging.info(f"删除了任务: {deleted_task['title']}")
                return True
        
        logging.warning(f"未找到ID为{task_id}的任务")
        return False
    
    def get_task(self, task_id):
        for task in self.tasks:
            if task["id"] == task_id:
                return task
        return None
    
    def get_tasks(self, category=None, priority=None, from_date=None, to_date=None, completed=None):
        filtered_tasks = self.tasks
        
        if category:
            filtered_tasks = [t for t in filtered_tasks if t["category"] == category]
        
        if priority:
            filtered_tasks = [t for t in filtered_tasks if t["priority"] == priority]
        
        if from_date:
            try:
                from_date_obj = datetime.strptime(from_date, "%Y-%m-%d")
                filtered_tasks = [t for t in filtered_tasks if datetime.strptime(t["due_date"], "%Y-%m-%d") >= from_date_obj]
            except ValueError:
                logging.error("起始日期格式无效")
        
        if to_date:
            try:
                to_date_obj = datetime.strptime(to_date, "%Y-%m-%d")
                filtered_tasks = [t for t in filtered_tasks if datetime.strptime(t["due_date"], "%Y-%m-%d") <= to_date_obj]
            except ValueError:
                logging.error("结束日期格式无效")
        
        if completed is not None:
            filtered_tasks = [t for t in filtered_tasks if t["completed"] == completed]
        
        return filtered_tasks
    
    def get_today_tasks(self):
        today = datetime.now().strftime("%Y-%m-%d")
        return self.get_tasks(from_date=today, to_date=today)
    
    def get_week_tasks(self):
        today = datetime.now()
        start_of_week = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
        end_of_week = (today + timedelta(days=6-today.weekday())).strftime("%Y-%m-%d")
        return self.get_tasks(from_date=start_of_week, to_date=end_of_week)
    
    def get_month_tasks(self):
        today = datetime.now()
        start_of_month = datetime(today.year, today.month, 1).strftime("%Y-%m-%d")
        if today.month == 12:
            end_of_month = datetime(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_of_month = datetime(today.year, today.month + 1, 1) - timedelta(days=1)
        end_of_month = end_of_month.strftime("%Y-%m-%d")
        return self.get_tasks(from_date=start_of_month, to_date=end_of_month)
    
    def mark_completed(self, task_id, completed=True):
        result = self.update_task(task_id, completed=completed)
        if result and completed and self.pet_state:
            self.pet_state.increase_hp(10)
        return result
    
    def get_upcoming_reminders(self, minutes=30):
        now = datetime.now()
        reminder_tasks = []
        
        for task in self.tasks:
            if task["completed"]:
                continue
                
            if not task.get("reminder_time"):
                continue
                
            try:
                due_date = task["due_date"]
                
                if task.get("start_time"):
                    task_time = datetime.strptime(f"{due_date} {task['start_time']}", "%Y-%m-%d %H:%M")
                else:
                    task_time = datetime.strptime(f"{due_date}", "%Y-%m-%d")
                
                reminder_time = task_time - timedelta(minutes=int(task["reminder_time"]))
                
                if now <= reminder_time <= (now + timedelta(minutes=minutes)):
                    reminder_tasks.append(task)
            except Exception as e:
                logging.error(f"计算提醒时间出错: {e}")
        
        return reminder_tasks
    
    def import_from_web(self, base_url):
        base_url = "https://course.pku.edu.cn/webapps/bb-sso-BBLEARN/login.html"
        assignments = asyncio.run(WebScraper(base_url))
        logging.info(f"从网页导入了 {len(assignments)} 个任务")
        
        for assignment in assignments:
            due_date = assignment.get("due_date")
            if due_date and due_date.strip():
                try:
                    from dateutil.parser import parse
                    parsed_date = parse(due_date, fuzzy=True)
                    due_date = parsed_date.strftime("%Y-%m-%d")
                except Exception as e:
                    logging.error(f"截止日期无法解析: {due_date}, 错误: {e}")
                    due_date = datetime.now().strftime("%Y-%m-%d")
            else:
                due_date = datetime.now().strftime("%Y-%m-%d")
            
            if datetime.strptime(due_date, "%Y-%m-%d").date() < datetime.now().date():
                logging.info(f"任务'{assignment['title']}'截止日期 {due_date} 已经过期，将跳过该任务")
                continue

            course_name = assignment.get("course_name", "未知课程")
            link_text = f" 链接: {assignment['link']}" if assignment.get("link") else ""
            description = f"从网页导入的任务，所属课程: {course_name}{link_text}"
            
            self.add_task(
                title=assignment['title'],
                description=description,
                category=self.STUDY,
                priority=self.MEDIUM,
                due_date=due_date
            )
    
    def check_overdue_tasks(self):
        now = datetime.now()
        changed = False
        for task in self.tasks:
            if not task.get("completed", False):
                due_str = task.get("due_date")
                if due_str:
                    try:
                        due_date = datetime.strptime(due_str, "%Y-%m-%d")
                        if due_date < now.date():
                            if not task.get("overdue_penalized", False):
                                if self.pet_state:
                                    self.pet_state.hp = max(5, self.pet_state.hp - 15)
                                task["overdue_penalized"] = True
                                changed = True
                    except Exception as e:
                        pass
        if changed:
            self._save_tasks()



if __name__ == "__main__":
    s = Schedule()
    task_id = s.add_task(
        title="测试任务", 
        description="这是一个测试任务", 
        category=Schedule.WORK,
        priority=Schedule.HIGH, 
        due_date="2025-04-16", 
        start_time="09:00",
        end_time="10:00",
        reminder_time=15
    )
    task = s.get_task(task_id)
    print(f"创建的任务: {task}")
    s.update_task(task_id, description="已更新的任务描述")
    week_tasks = s.get_week_tasks()
    print(f"本周任务数: {len(week_tasks)}")