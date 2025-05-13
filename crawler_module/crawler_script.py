import csv
import re
from time import sleep
from datetime import datetime
import pandas as pd
import urllib.parse  # 用來解碼中文網址
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# ====== 參數設定 ======
INPUT_CSV_PATH = "../electiondataset.csv"  # 資料集
OUTPUT_CSV_PATH = "follow.csv"  # 儲存爬蟲結果
LOG_FILE = "crawler_log.txt"  # 儲存過程 log

# ====== 建立 log 記錄器（同時印出與寫入檔案）======
def init_logger(log_path):
    def logger(msg):
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        full_msg = f"{timestamp} {msg}"
        print(full_msg)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(full_msg + "\n")
    return logger

logger = init_logger(LOG_FILE)

# ====== Facebook ID 萃取函式（強化版本）======
def extract_fb_id_from_url(url):
    """
    從 Facebook URL 中萃取 ID，支援：
    - profile.php?id=...
    - /p/中文名稱-123456789/
    - /username?locale=...
    """
    url = urllib.parse.unquote(url.strip())  # ✅ decode 中文與參數

    if "profile.php?id=" in url:
        m = re.search(r"profile\.php\?id=(\d+)", url)
        return m.group(1) if m else "profile.php"

    elif "/p/" in url:
        # 抓末尾數字（頁面 ID）
        m = re.search(r"/p/.*?-([0-9]+)", url)
        return m.group(1) if m else "page.p"

    else:
        # 一般 username，排除 query string
        m = re.match(r"https://www\.facebook\.com/([^/?]+)", url)
        return m.group(1) if m else "unknown"

# ====== 讀取原始 CSV 並萃取 name + facebook ID ======
def extract_facebook_ids_from_csv(csv_path):
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    candidates = []
    for _, row in df.iterrows():
        fb_link = str(row.get('臉書連結', '')).strip()
        name = str(row.get('姓名', '')).strip()
        if fb_link.startswith('https://www.facebook.com/'):
            fb_id = extract_fb_id_from_url(fb_link)
            candidates.append((name, fb_id))
    return candidates

# ====== 抓追蹤的粉專清單 ======
def get_username_from_url(url):
    return extract_fb_id_from_url(url)

def get_following_list(driver, person_name, person_id, logger):
    url = f"https://www.facebook.com/{person_id}/following"
    logger(f"[INFO] 前往 {person_name} 的追蹤頁：{url}")
    driver.get(url)
    sleep(5)

    # 若頁面錯誤或限制，回報錯誤
    if "找不到內容" in driver.page_source or "content_not_found" in driver.page_source:
        logger(f"[ERROR] 無法存取 {person_name} ({person_id}) 的追蹤頁")
        return []

    logger(f"[INFO] 開始滑動追蹤頁內容以載入更多")

    scroll_pause_time = 3
    max_scrolls = 50
    previous_count = 0

    for i in range(max_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(scroll_pause_time)
        links = driver.find_elements(By.CSS_SELECTOR, "a[role='link']")
        current_count = len(links)
        if current_count == previous_count:
            logger(f"  ⤷ 第 {i+1} 次滑動後無新增，停止")
            break
        previous_count = current_count
        logger(f"  ⤷ 第 {i+1} 次滑動：目前共 {current_count} 筆")

    # 擷取每一筆連結
    records = []
    links = driver.find_elements(By.CSS_SELECTOR, "a[role='link']")
    for link in links:
        followname = link.text.strip()
        href = link.get_attribute("href")
        if followname and href and "facebook.com" in href:
            followid = get_username_from_url(href)
            records.append((person_name, person_id, followname, followid, href))

    logger(f"[INFO] 擷取 {len(records)} 筆 {person_name} 的追蹤紀錄")
    return records

# ====== 主程式流程 ======
def main():
    logger("[START] 開始 Facebook 追蹤名單爬蟲作業")

    # 萃取候選人名單與 Facebook ID
    candidates = extract_facebook_ids_from_csv(INPUT_CSV_PATH)
    logger(f"[INFO] 找到 {len(candidates)} 位含臉書連結的候選人")

    # 啟動 Selenium 並連接已登入的 Chrome（需先開啟 remote debugging）
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=chrome_options)

    # 對每一位候選人爬取追蹤資料
    all_records = []
    for name, fb_id in candidates:
        try:
            records = get_following_list(driver, name, fb_id, logger)
            all_records.extend(records)
        except Exception as e:
            logger(f"[ERROR] {name} ({fb_id}) 發生例外錯誤：{e}")
            continue

    driver.quit()

    # 匯出成 CSV
    logger(f"[INFO] 儲存 {len(all_records)} 筆資料至 {OUTPUT_CSV_PATH}")
    with open(OUTPUT_CSV_PATH, "w", newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'nameid', 'followname', 'followid', 'url'])
        writer.writerows(all_records)

    logger("[DONE] 所有爬蟲工作完成 ✅")

if __name__ == "__main__":
    main()
