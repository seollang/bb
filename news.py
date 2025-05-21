import streamlit as st
import requests
from bs4 import BeautifulSoup
from transformers import pipeline

# ✅ 뉴스 링크 가져오기
def get_news_links():
    url = "https://news.naver.com/main/list.naver?mode=LSD&mid=sec&sid1=105"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    links = []
    for a_tag in soup.select(".list_body a"):
        href = a_tag.get("href")
        title = a_tag.get_text(strip=True)
        if href and title and href.startswith("https://"):
            links.append((title, href))
        if len(links) >= 5:
            break
    return links

# ✅ 뉴스 본문 가져오기
def get_article_content(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    content = soup.find("div", {"id": "newsct_article"})
    if content:
        return content.get_text(strip=True)
    return "본문을 불러올 수 없습니다."

# ✅ 요약 모델 불러오기 (캐시로 속도 개선)
@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

summarizer = load_summarizer()

# ✅ Streamlit 웹 UI 구성
st.title("📰 AI 뉴스 요약 웹앱")
st.markdown("IT 분야 뉴스를 요약해주는 인공지능 요약 웹앱입니다.")

news = get_news_links()

for title, link in news:
    with st.expander(title):
        article = get_article_content(link)
        st.markdown("### 🧾 원문 내용")
        st.write(article[:1000] + ("..." if len(article) > 1000 else ""))

        if st.button(f"요약 보기: {title}"):
            if article and len(article.strip()) > 100:
                input_text = article.strip().replace('\n', ' ')[:800]
                with st.spinner("요약 중..."):
                    try:
                        summary = summarizer(
                            input_text,
                            max_length=130,
                            min_length=30,
                            do_sample=False
                        )[0]['summary_text']
                        st.markdown("### ✨ 요약 결과")
                        st.success(summary)
                    except Exception as e:
                        st.error(f"요약 중 오류 발생: {e}")
            else:
                st.warning("요약할 충분한 본문이 없습니다.")
