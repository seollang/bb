import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from transformers import pipeline

# Selenium 드라이버 설정 함수
def get_selenium_driver():
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("start-maximized")
        options.binary_location = "/usr/bin/chromium"
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
        print("ChromeDriver started successfully")
        return driver
    except Exception as e:
        print(f"Error starting ChromeDriver: {e}")
        raise

# 뉴스 링크를 가져오는 함수
def get_news_links():
    driver = get_selenium_driver()
    try:
        url = "https://news.naver.com/main/main.naver"
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, 'read.naver')]"))
        )
        links = driver.find_elements(By.XPATH, "//a[contains(@href, 'read.naver')]")
        news_links = [link.get_attribute("href") for link in links]
        return news_links
    finally:
        driver.quit()

# 뉴스 원문을 가져오는 함수
def get_article_content(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        content = soup.find("div", {"id": "dic_area"})
        return content.get_text(strip=True) if content else ""
    except Exception as e:
        print(f"Error fetching article content: {e}")
        return ""

# 뉴스 요약을 위한 함수
def summarize_text(text):
    try:
        summarizer = pipeline("summarization", model="gogamza/kobart-summarization")
        max_input_length = 512
        summary = summarizer(text[:max_input_length], max_length=150, min_length=30, do_sample=False)
        return summary[0]['summary_text']
    except Exception as e:
        print(f"Error summarizing text: {e}")
        return ""

# 실제로 실행되는 부분
if __name__ == "__main__":
    news_links = get_news_links()
    print(f"Found {len(news_links)} news articles.")
    
    for link in news_links:
        print(f"Processing: {link}")
        article = get_article_content(link)
        if article:
            summary = summarize_text(article)
            print(f"Summary: {summary}")
            print("-" * 80)
        else:
            print("No article content found.")
