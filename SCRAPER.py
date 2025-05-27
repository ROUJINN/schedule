import asyncio
import pyppeteer as pyp
import time
import json #config.json
import os

async def antiAntiCrawler(page):
    # 为page添加反反爬虫手段
    await page.setUserAgent('Mozilla/5.0 (Windows NT 6.1; Win64; x64) \
    AppleWebKit/537.36 (KHTML, like Gecko) \
    Chrome/78.0.3904.70 Safari/537.36')
    await page.evaluateOnNewDocument(
        '() =>{ Object.defineProperties(navigator, \
    { webdriver:{ get: () => false } }) }')



#https://course.pku.edu.cn/webapps/login/
#<a href="/webapps/bb-sso-BBLEARN/login.html" class="login_stu_a">校园卡用户</a>
#https://iaaa.pku.edu.cn/iaaa/oauth.jsp



 # 处理 Cookie 弹窗
async def handle_cookie_popup(page):
    try:
        # 等待按钮加载
        await page.waitForSelector('#agree_button', timeout=5000)
        # 执行按钮的 onclick 属性
        await page.evaluate('document.querySelector("#agree_button").click()')
    except Exception as e:
        print(f"处理 Cookie 弹窗时出错: {e}")
    
    
    
    

async def WebScraper(loginUrl):
    # 加载配置
    config_path = "config.json"
    if not os.path.exists(config_path):
        print("未找到配置文件，请先设置学号、密码和Chrome地址")
        return

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    student_id = config.get("student_id")
    password = config.get("password")
    chrome_path = config.get("chrome_path")

    if not student_id or not password or not chrome_path:
        print("配置文件不完整，请检查学号、密码和Chrome地址")
        return
    
#"C:\\Users\\iyuki\\AppData\\Local\\GptChrome\\GptBrowser.exe"

    width, height = 1400, 800  # 网页宽高
    browser = await pyp.launch(executablePath=chrome_path,
                               headless=False,
                               userdataDir="c:/tmp",
                               args=[f'--window-size={width},{height}'])
    page = await browser.newPage()
    await antiAntiCrawler(page)
    await page.setViewport({'width': width, 'height': height})
    await page.goto(loginUrl)

    # 找到“校园卡用户”按钮并点击
    campus_card_button = await page.querySelector("a.login_stu_a")  # 根据 class 选择器
    if campus_card_button:
        await campus_card_button.click()
        await page.waitForNavigation()  # 等待页面跳转
    else:
        print("未找到校园卡用户按钮")
        return

    # 登录
    # 等待“学号”输入框加载
    await page.waitForXPath('/html/body/div/div[2]/form/div/div[2]/div[1]/input', timeout=10000)
    student_id_input = await page.xpath('/html/body/div/div[2]/form/div/div[2]/div[1]/input')
    # 输入学号
    if student_id_input:
        await student_id_input[0].click()  # 点击输入框，确保聚焦
        await asyncio.sleep(0.5)  # 等待输入框完全准备好
        for char in student_id:
            await student_id_input[0].type(char)  # 逐字符输入学号
            await asyncio.sleep(0.05)  # 每次输入后等待 0.1 秒
    else:
        print("未找到学号输入框")
        return

    # 等待“密码”输入框加载
    await page.waitForXPath('/html/body/div/div[2]/form/div/div[2]/div[2]/input', timeout=10000)
    password_input = await page.xpath('/html/body/div/div[2]/form/div/div[2]/div[2]/input')
    if password_input:
        await password_input[0].type(password)  # 输入密码
    else:
        print("未找到密码输入框")
        return

    # 找到登录按钮并点击
    login_button = await page.xpath('/html/body/div/div[2]/form/div/div[2]/div[8]/input[3]')
    if login_button:
        await login_button[0].click()  # 点击登录按钮
        await page.waitForNavigation()  # 等待页面跳转
        await handle_cookie_popup(page)  # 处理 Cookie 弹窗
    else:
        print("未找到登录按钮")
        return
    
    
   
    '''
    courses:
    <a href="/webapps/blackboard/execute/launcher?type=Course&amp;id=PkId{key=_78021_1, dataType=blackboard.data.course.Course, container=blackboard.persist.DatabaseContainer@1deea14c}&amp;url=" target="_top">24252-00023-02330003-190****202-00-3: 哲学导论(24-25学年第2学期本研合上)</a>
    <a href="/webapps/blackboard/execute/launcher?type=Course&amp;id=PkId{key=_80037_1, dataType=blackboard.data.course.Course, container=blackboard.persist.DatabaseContainer@1deea14c}&amp;url=" target="_top">24252-00048-04831750-100****107-00-1: 程序设计实习(24-25学年第2学期)</a>
    '''

    # 找到“程序设计实习"课程链接并点击
    await page.waitForXPath('//a[contains(text(), "程序设计实习")]', timeout=10000)
    course_link = await page.xpath('//a[contains(text(), "程序设计实习")]')
    if course_link:
        await course_link[0].click()  # 点击课程链接
        await page.waitForNavigation()  # 等待页面跳转
    else:
        print("未找到“程序设计实习”课程链接")
        return

    '''
    # 点击“显示课程菜单”,好像自动打开的页面没有这个选项！
    await page.waitForXPath('/html/body/div[5]/div[3]/nav/div/div[1]/a', timeout=10000)
    menu_button = await page.xpath('/html/body/div[5]/div[3]/nav/div/div[1]/a')
    if menu_button:
        await menu_button[0].click()  # 点击显示课程菜单
        await asyncio.sleep(0.1)  # 等待菜单展开
    else:
        print("未找到“显示课程菜单”按钮")
        return
    '''

    # 点击“课程作业”
    await page.waitForXPath('//span[@title="课程作业"]', timeout=10000)
    assignments_button = await page.xpath('//span[@title="课程作业"]')
    if assignments_button:
        await assignments_button[0].click()  # 点击课程作业
        await page.waitForNavigation()  # 等待页面跳转
    else:
        print("未找到“课程作业”按钮")
        return
    
    print("已进入教学网")
    
    '''
    await page.waitForSelector("#main>h2", timeout=30000)
    # 等待 "正在进行的比赛..." 标题出现
    element = await page.querySelector("#userMenu>li:nth-child(2)>a")
    # 找 "个人首页" 链接
    await element.click()  # 点击个人首页链接
    await page.waitForNavigation()  # 等新网页装入完毕
    elements = await page.querySelectorAll(".result-right")
    # 找所有 Accepted 链接, 其有属性 class="result-right"
    page2 = await browser.newPage()  # 新开一个页面 (标签)
    time.sleep(2)

    await antiAntiCrawler(page2)
    for element in elements[:2]:  # 只打印前两个程序
        obj = await element.getProperty("href")  # 获取href属性
        url = await obj.jsonValue()
        await page2.goto(url)  # 在新页面(标签)中装入新网页
        element = await page2.querySelector("pre")  # 查找pre tag
        obj = await element.getProperty("innerText")  # 取源代码
        text = await obj.jsonValue()
        print(text)
        print("-------------------------")
    await browser.close()

'''


def main():
    url = "https://course.pku.edu.cn/webapps/login/"
    asyncio.run(WebScraper(url))   
