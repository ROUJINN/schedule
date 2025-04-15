#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日程管理与提醒工具

功能：
- 日程管理（添加、删除、修改日程）clean
- 提醒功能（定时提醒、重复提醒）
- 任务分类（工作、学习、生活等）
- 优先级设置（高、中、低）
- 日历视图（显示每日/每周/每月的任务安排）
- 数据存储：JSON 文件
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from ui_manager import MainWindow

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.log')),
        logging.StreamHandler()
    ]
)

def main():
    """程序主入口"""
    app = QApplication(sys.argv)
    app.setApplicationName("日程管理与提醒工具")
    
    # 设置应用程序图标（如果有的话）
    # app.setWindowIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons/app_icon.png')))
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 启动应用程序事件循环
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()