import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from transformers import pipeline
from time import sleep

# Selenium 드라이버 설정 함수
def get_selenium_driver():
    # Chrome 옵션 설정
    options = Options()
    options.add_argument("--headless")  # headless 모드로 실행 (브라우저 창이 뜨지 않음)
    options.add_argument("--no-sandbox")  # 샌드박스를 비활성화
    options.add_argument("--disable-dev-shm-usage")  # Docker 환경에서 발생하는 오류 방지
    options.add_argument("start-maximized")  # 최대화된 창에서 실행

    # ChromeDriver를 자동으로 설치하고 서비스로 실행
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    return driver

# 뉴스 링크를 가져오는 함수
def get_news_links():
    driver = get_selenium_driver()
    
    # 뉴스 사이트 URL (여기서는 네이버 뉴스 예시)
    url = "https://news.naver.com/main/main.naver"
    driver.get(url)
    sleep(3)  # 페이지 로딩 대기
    
    # 뉴스 기사의 링크를 가져오는 예시
    links = driver.find_elements_by_xpath("//a[contains(@class, 'news_tit')]")
    news_links = [link.get_attribute("href") for link in links]
    
    driver.quit()  # 작업 완료 후 드라이버 종료
    return news_links

# 뉴스 원문을 가져오는 함수
def get_article_content(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    
    # 기사 본문을 추출 (네이버 뉴스 기준)
    content = soup.find("div", {"id": "articleBodyContents"})
    if content:
        return content.get_text(strip=True)
    return ""

# 뉴스 요약을 위한 함수
def summarize_text(text):
    summarizer = pipeline("summarization")
    summary = summarizer(text[:1000], max_length=150, min_length=30, do_sample=False)
    return summary[0]['summary_text']

# 실제로 실행되는 부분
if __name__ == "__main__":
    # 뉴스 링크 가져오기
    news_links = get_news_links()
    print(f"Found {len(news_links)} news articles.")
    
    # 각 뉴스 링크에 대해 기사 내용 가져오기 및 요약
    for link in news_links:
        print(f"Processing: {link}")
        article = get_article_content(link)
        if article:
            summary = summarize_text(article)
            print(f"Summary: {summary}")
            print("-" * 80)
        else:
            print("No article content found.")
