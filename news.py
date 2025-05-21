import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from transformers import pipeline

# Selenium 설정
def get_selenium_driver():
    options = Options()
    options.headless = True  # 브라우저 창을 띄우지 않음
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# 뉴스 제목 및 링크 가져오기
def get_news_links():
    url = "https://news.naver.com/main/list.naver?mode=LSD&mid=sec&sid1=105"
    driver = get_selenium_driver()
    driver.get(url)

    # 페이지가 완전히 로드될 때까지 기다림
    driver.implicitly_wait(10)

    links = []
    articles = driver.find_elements(By.CSS_SELECTOR, ".list_body li")
    
    for article in articles:
        title_tag = article.find_element(By.CSS_SELECTOR, "a")
        title = title_tag.text
        link = title_tag.get_attribute("href")
        img_tag = article.find_element(By.CSS_SELECTOR, "img")
        img_url = img_tag.get_attribute("src") if img_tag else None
        if link and title:
            links.append((title, link, img_url))
        if len(links) >= 5:
            break
    
    driver.quit()
    return links

# 뉴스 본문 가져오기
def get_article_content(url):
    driver = get_selenium_driver()
    driver.get(url)
    driver.implicitly_wait(10)
    
    # 본문을 포함하는 태그를 찾기 (예시로 ID나 class 사용)
    try:
        content = driver.find_element(By.CSS_SELECTOR, "#articleBodyContents")  # 네이버 뉴스 기사 본문 ID
        article_text = content.text
    except Exception as e:
        article_text = f"본문을 불러오는 중 오류 발생: {e}"

    driver.quit()
    return article_text

# 요약 모델
@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

summarizer = load_summarizer()

# Streamlit UI
st.title("📰 AI 뉴스 요약 웹앱")
st.markdown("최신 IT 뉴스를 인공지능이 자동으로 요약해줍니다.")

# 뉴스 목록 가져오기
news_list = get_news_links()

for title, link, img_url in news_list:
    with st.container():
        st.markdown("---")
        cols = st.columns([2, 8])

        # 이미지
        with cols[0]:
            if img_url:
                st.image(img_url, width=120)
            else:
                st.image("https://via.placeholder.com/120x80?text=No+Image")

        # 제목과 링크
        with cols[1]:
            st.markdown(f"### {title}")
            st.markdown(f'[🔗 원문 보러가기]({link}){{:target="_blank"}}', unsafe_allow_html=True)

            # 기사 내용 출력
            article = get_article_content(link)
            st.markdown("##### 📄 기사 일부:")
            st.write(article[:1000] + ("..." if len(article) > 1000 else ""))  # 1000자까지만 출력

            if st.button(f"✂ 요약 보기: {title}"):
                cleaned = article.strip().replace('\n', ' ')
                num_sentences = cleaned.count('.') + cleaned.count('!') + cleaned.count('?')

                if len(cleaned) > 200 and num_sentences >= 3:
                    input_text = cleaned[:800]
                    with st.spinner("요약 중..."):
                        try:
                            summary = summarizer(
                                input_text,
                                max_length=130,
                                min_length=30,
                                do_sample=False
                            )[0]['summary_text']
                            st.markdown("#### ✨ 요약 결과")
                            st.success(summary)
                        except Exception as e:
                            st.error(f"요약 중 오류 발생: {e}")
                else:
                    st.warning("요약할 충분한 본문이 없습니다.")
