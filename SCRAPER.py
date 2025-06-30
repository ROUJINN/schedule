import asyncio
import pyppeteer as pyp
from datetime import datetime
import json
import os
import re
import atexit

browser = None

async def antiAntiCrawler(page):
    await page.setUserAgent('Mozilla/5.0 (Windows NT 6.1; Win64; x64) '
                            'AppleWebKit/537.36 (KHTML, like Gecko) '
                            'Chrome/78.0.3904.70 Safari/537.36')
    await page.evaluateOnNewDocument(
        "() =>{ Object.defineProperties(navigator, { webdriver:{ get: () => false } }) }"
    )

async def parse_item(browser, item, assignments, depth=1, course_name=None):
    icon_img = await item.querySelector("img.item_icon")
    if not icon_img:
        return
    icon_alt = await (await icon_img.getProperty("alt")).jsonValue()
    title_elem = await item.querySelector("h3")
    title_text = (await (await title_elem.getProperty("textContent")).jsonValue()).strip()
    
    indent = "  " * depth
    
    if "文件夹" in icon_alt:
        link_elem = await item.querySelector("a")
        if link_elem:
            href = await (await link_elem.getProperty("href")).jsonValue()
            new_page = await browser.newPage()
            await antiAntiCrawler(new_page)
            await new_page.setViewport({'width': 1400, 'height': 800})
            await new_page.goto(href, waitUntil="networkidle2")
            await asyncio.sleep(1)
            try:
                await new_page.waitForSelector("ul.contentList > li", timeout=5000)
                sub_items = await new_page.querySelectorAll("ul.contentList > li")
                for sub_item in sub_items:
                    await parse_item(browser, sub_item, assignments, depth + 1, course_name=course_name)
            except asyncio.TimeoutError:
                print(f"{indent}该文件夹页面没有内容或加载超时")
            await new_page.close()
    
    elif "项目" in icon_alt or "文件" in icon_alt or "作业" in icon_alt:
        print(f"{indent}{title_text}")
        homework = {
            "title": title_text,
            "due_date": None,
            "link": None,
            "course_name": course_name
        }
        details = await item.querySelector("div.details")
        if details:
            inner_html = await (await details.getProperty("innerHTML")).jsonValue()
            link_match = re.search(r'href="(http[s]?://[^"]+)"', inner_html)
            time_match = re.search(
            r'(?:提交截止时间|作业截止时间|截止时间)[:：]?\s*(?:北京时间)?\s*([\d]{4}年\d{1,2}月\d{1,2}日\d{1,2}:\d{2}|[一二三四五六七八九十0-9]{1,2}月\d{1,2}日\d{1,2}:\d{2})',
            inner_html)
            if link_match:
                homework["link"] = link_match.group(1)
                print(f"{indent}链接: {homework['link']}")
            if time_match:
                raw_time = time_match.group(1).strip()
                if "年" not in raw_time:
                    current_year = datetime.now().year
                    raw_time = f"{current_year}年{raw_time}"
                homework["due_date"] = raw_time
                print(f"{indent}截止时间: {homework['due_date']}")
   
        assignments.append(homework)
    
    
async def WebScraper(loginUrl):
    config_path = "config.json"
    if not os.path.exists(config_path):
        print("未找到配置文件，请先设置学号、密码和Chrome地址")
        return []
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    student_id = config.get("student_id")
    password = config.get("password")
    chrome_path = config.get("chrome_path")
    if not student_id or not password or not chrome_path:
        print("配置文件不完整，请检查学号、密码和Chrome地址")
        return []
    
    global browser
    width, height = 1400, 800
    browser = await pyp.launch(headless=True,
                               executablePath=chrome_path,
                               userDataDir="c:/tmp",
                               args=[f'--window-size={width},{height}'])
    page = await browser.newPage()
    await antiAntiCrawler(page)
    await page.setViewport({'width': width, 'height': height})
    await page.goto(loginUrl, waitUntil="networkidle2")
    await asyncio.sleep(2)

    await (await page.querySelector("#user_name")).type(student_id)
    await (await page.querySelector("#password")).type(password)
    await asyncio.gather(
        page.waitForNavigation(waitUntil="networkidle2"),
        (await page.querySelector("#logon_button")).click()
    )

    await page.waitForSelector("ul.portletList-img.courseListing.coursefakeclass > li > a", timeout=30000)
    course_links = await page.querySelectorAll("ul.portletList-img.courseListing.coursefakeclass > li > a")
    
    assignments = []

    for i, course_link_elem in enumerate(course_links):
        course_page = None
        try:
            href = await (await course_link_elem.getProperty('href')).jsonValue()
            full_course_name = await (await course_link_elem.getProperty('textContent')).jsonValue()
            full_course_name = full_course_name.strip()
            if not re.search(r"24-25学年第\s*2\s*学期", full_course_name):
                continue
            
            parts = full_course_name.split(":")
            if len(parts) >= 2:
                course_name_raw = parts[1]
            else:
                course_name_raw = full_course_name
            course_name = re.sub(r"\(.*\)", "", course_name_raw).strip()
            
            course_page = await browser.newPage()
            await antiAntiCrawler(course_page)
            await course_page.setViewport({'width': width, 'height': height})
            await course_page.goto(href, waitUntil="networkidle2")
            await asyncio.sleep(1)
            try:
                agree_button = await course_page.waitForSelector('#agree_button', timeout=3000)
                if agree_button:
                    await agree_button.click()
                    await asyncio.sleep(1)
                    print("点击了同意按钮")
            except asyncio.TimeoutError:
                pass

            try:
                homework_link_elem = await course_page.waitForXPath(
                    "//a[.//span[contains(@title,'课程作业') or contains(text(),'课程作业')]]", timeout=5000)
                if homework_link_elem:
                    print(f"课程: {course_name}")
                    await asyncio.gather(
                        course_page.waitForNavigation(waitUntil="networkidle2"),
                        homework_link_elem.click()
                    )
                else:
                    await course_page.close()
                    continue
            except asyncio.TimeoutError:
                await course_page.close()
                continue

            items = await course_page.querySelectorAll("ul.contentList > li")
            for item in items:
                await parse_item(browser, item, assignments, course_name=course_name)

            await course_page.close()

        except Exception as e:
            print(f"处理第 {i + 1} 门课程时出错: {e}")
            if course_page:
                try:
                    await course_page.close()
                except Exception:
                    pass
            continue

    await browser.close()
    return assignments


def main():
    url = "https://course.pku.edu.cn/webapps/bb-sso-BBLEARN/login.html"
    asyncio.run(WebScraper(url))

if __name__ == "__main__":
    main()