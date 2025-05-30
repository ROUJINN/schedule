Schedule
PetState
DesktopPet
Reminder
&ui_manager的一堆

## 项目类结构详细分析

### 1. 核心业务类（my_schedule.py）

#### Schedule 类
- 功能: 日程管理的核心类，负责任务的增删改查等所有操作
- 主要属性:
    - `data_file`: JSON数据文件路径
    - `tasks`: 任务列表
    - 常量定义：任务类型（WORK, STUDY, LIFE, OTHER）和优先级（HIGH, MEDIUM, LOW）
- 主要方法:
    - `_load_tasks()`: 从JSON文件加载任务数据
    - `_save_tasks()`: 保存任务数据到JSON文件
    - `add_task()`: 添加新任务，返回任务ID
    - `update_task()`: 更新任务信息
    - `delete_task()`: 删除任务
    - `get_task()`: 获取单个任务详情
    - `get_tasks()`: 获取任务列表，支持多种筛选条件
    - `get_today_tasks()`: 获取今日任务
    - `get_week_tasks()`: 获取本周任务
    - `get_month_tasks()`: 获取本月任务
    - `mark_completed()`: 标记任务完成状态
    - `get_upcoming_reminders()`: 获取即将到期的提醒任务
    - `import_from_web()`: 从网页导入任务

### 2. 宠物系统类（pet_engine.py）

#### PetState 类
- 继承: QObject
- 功能: 管理桌面宠物的状态（血量、食物、心情）
- 主要属性:
    - `_hp`: 血量（0-100）
    - `_food`: 食物值（0-100）
    - `_mood`: 心情状态（normal/happy/angry）
    - `state_file`: 状态保存文件路径
- 信号:
    - `hp_changed`: 血量变化信号
    - `mood_changed`: 心情变化信号
- 主要方法:
    - `load_state()`: 加载宠物状态
    - `save_state()`: 保存宠物状态
    - 属性的getter/setter方法

#### DesktopPet 类
- 继承: QWidget
- 功能: 桌面宠物的可视化界面和交互
- 主要属性:
    - `state`: PetState实例
    - `movie`: 宠物动画（QMovie）
    - `tray`: 系统托盘图标
    - `hp_timer`: 自动减血定时器
- 主要方法:
    - `init_pet()`: 初始化宠物窗口
    - `init_tray()`: 初始化系统托盘
    - `init_hp_timer()`: 初始化血量定时器
    - `paintEvent()`: 绘制宠物和HP条
    - `mousePressEvent()/mouseMoveEvent()/mouseReleaseEvent()`: 鼠标拖拽事件
    - `toggle_visibility()`: 切换显示/隐藏
    - `auto_decrease_hp()`: 自动减少血量

### 3. 提醒系统类（reminder.py）

#### Reminder 类
- 继承: QObject
- 功能: 管理任务提醒功能
- 主要属性:
    - `schedule_manager`: Schedule实例
    - `reminder_thread`: 提醒线程
    - `running`: 线程运行状态标志
- 信号:
    - `reminder_signal`: 提醒信号
- 主要方法:
    - `start()`: 启动提醒线程
    - `stop()`: 停止提醒线程
    - `_reminder_loop()`: 提醒线程主循环
    - `_schedule_daily_tasks()`: 为当天任务设置提醒
    - `_check_reminders()`: 检查需要提醒的任务
    - `add_one_time_reminder()`: 为特定任务添加一次性提醒
    - `remove_reminder()`: 移除任务提醒

### 4. 用户界面类（ui_manager.py）

#### CustomCalendarWidget 类
- 继承: QCalendarWidget
- 功能: 自定义日历控件，支持高亮有任务的日期
- 主要属性:
    - `schedule_manager`: Schedule实例
    - `dates_with_tasks`: 存储有任务的日期集合
- 主要方法:
    - `initUI()`: 初始化UI样式
    - `update_dates_with_tasks()`: 更新有任务的日期列表
    - `paintCell()`: 重写绘制单元格方法，高亮有任务的日期

#### TaskDialog 类
- 继承: QDialog
- 功能: 任务详情对话框，用于添加/编辑任务
- 主要属性:
    - `task`: 当前编辑的任务数据（如果是编辑模式）
    - 各种输入控件（标题、描述、类别、优先级等）
- 主要方法:
    - `init_ui()`: 初始化用户界面
    - `fill_form_data()`: 用现有任务数据填充表单
    - `get_task_data()`: 获取表单数据

#### TaskTableWidget 类
- 继承: QTableWidget
- 功能: 自定义任务表格组件
- 主要方法:
    - `init_ui()`: 初始化表格界面
    - `update_tasks()`: 更新任务列表显示

#### CalendarViewWidget 类
- 继承: QWidget
- 功能: 月历视图组件
- 主要属性:
    - `schedule_manager`: Schedule实例
    - `calendar`: CustomCalendarWidget实例
    - `task_table`: TaskTableWidget实例
- 主要方法:
    - `init_ui()`: 初始化界面
    - `update_month_title()`: 更新月份标题
    - `on_month_changed()`: 月份变化处理
    - `on_date_selected()`: 日期选择处理
    - `update_day_tasks()`: 更新所选日期的任务列表

#### WeekViewWidget 类
- 继承: QWidget
- 功能: 周视图组件，显示一周七天的任务安排
- 主要属性:
    - `schedule_manager`: Schedule实例
    - `current_week_start`: 当前周的起始日期
    - `day_task_lists`: 七天的任务列表控件
- 主要方法:
    - `init_ui()`: 初始化界面
    - `update_week_view()`: 更新周视图数据
    - `show_prev_week()/show_next_week()`: 切换周
    - `show_context_menu()`: 显示右键菜单
    - `show_task_detail()`: 显示任务详细信息

#### DayViewWidget 类
- 继承: QWidget
- 功能: 日视图组件，左侧显示24小时时间段，右侧显示当日任务列表
- 主要属性:
    - `schedule_manager`: Schedule实例
    - `current_date`: 当前显示的日期
    - `time_slots_table`: 时间段表格
    - `task_table`: 任务列表表格
    - `date_selector`: 日期选择器
- 主要方法:
    - `init_ui()`: 初始化界面
    - `update_day_view()`: 更新日视图数据
    - `show_prev_day()/show_next_day()/show_today()`: 日期导航
    - `on_go_to_date()`: 跳转到指定日期

#### ExcelExporter 类
- 功能: Excel导出工具类（静态类）
- 主要方法:
    - `export_tasks()`: 将任务导出为Excel文件

#### SettingsDialog 类
- 继承: QDialog
- 功能: 设置对话框，用于配置学号、密码、Chrome路径等
- 主要属性:
    - 各种输入控件（学号、密码、Chrome路径）
- 主要方法:
    - `init_ui()`: 初始化界面
    - `load_settings()`: 加载配置文件
    - `save_settings()`: 保存配置到文件

#### MainWindow 类
- 继承: QMainWindow
- 功能: 主窗口，整合所有功能模块
- 主要属性:
    - `pet_state`: PetState实例
    - `pet`: DesktopPet实例
    - `schedule_manager`: Schedule实例
    - `reminder`: Reminder实例
    - `tabs`: QTabWidget（包含各种视图）
    - 各种视图控件和筛选控件
- 主要方法:
    - `init_ui()`: 初始化用户界面
    - `add_task_tab()/add_calendar_tab()/add_week_tab()/add_day_tab()`: 添加各种视图选项卡
    - `update_task_list()`: 更新任务列表
    - `add_task()/edit_task()/delete_task()`: 任务管理操作
    - `toggle_task_complete()/toggle_task_reminder()`: 任务状态切换
    - `show_reminder()`: 显示任务提醒
    - `export_to_excel()`: 导出Excel
    - `import_from_web()`: 从网页导入
    - `update_all_views()`: 更新所有视图
    - `init_pet_connection()`: 初始化宠物连接
    - `update_pet_status()/update_pet_animation()`: 宠物状态更新

### 5. 网页爬虫模块（SCRAPER.py）

#### WebScraper 函数
- 功能: 异步函数，用于从北大教学网爬取课程作业信息
- 主要步骤:
    - 加载配置文件（学号、密码、Chrome路径）
    - 启动浏览器并设置反反爬虫措施
    - 自动登录教学网
    - 导航到指定课程的作业页面
- 辅助函数:
    - `antiAntiCrawler()`: 添加反反爬虫手段
    - `handle_cookie_popup()`: 处理Cookie弹窗

### 总结

- MainWindow: 作为总控制器，管理所有其他组件
- Schedule: 核心数据模型，被其他所有UI组件使用
- PetState + DesktopPet: 独立的宠物系统，通过信号与主窗口通信
- Reminder: 依赖Schedule，提供后台提醒服务
- 各种Widget: 都依赖Schedule进行数据操作，通过MainWindow进行协调
- SCRAPER: 独立的工具模块，被Schedule调用
