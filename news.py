import streamlit as st
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import html

# ✅ 뉴스 링크 + 썸네일 가져오기
def get_news_links():
    url = "https://news.naver.com/main/list.naver?mode=LSD&mid=sec&sid1=105"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # HTML 구조를 보기 전에 디코딩된 내용 출력
    decoded_html = html.unescape(soup.prettify())  # &amp;와 같은 HTML 엔터티를 실제 문자로 디코딩
    st.write(decoded_html)  # 디코딩된 HTML을 확인하기 위해 출력

    links = []
    for item in soup.select(".list_body li"):
        a_tag = item.find("a")
        title = a_tag.get_text(strip=True)
        href = a_tag.get("href")
        img_tag = item.find("img")
        img_url = img_tag["src"] if img_tag else None

        # 디버깅 로그
        print(f"제목: {title}, 링크: {href}, 이미지: {img_url}")

        if href and title and href.startswith("https://"):
            links.append((title, href, img_url))
        if len(links) >= 5:
            break
    return links

# ✅ 뉴스 본문 가져오기
def get_article_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        # HTML 구조를 디버깅
        st.write(soup.prettify())  # HTML 구조 확인을 위해 출력

        # 본문을 포함하는 다른 태그로 바꿔봅니다.
        content = soup.find("div", {"class": "article_body"})  # 여기에서 "article_body"가 본문을 담고 있는 클래스일 가능성 있음
        if not content:
            content = soup.find("div", {"id": "articleBodyContents"})  # 다른 클래스명 시도
        if not content:
            content = soup.find("div", {"class": "news_body"})  # 또 다른 클래스명 시도

        if content:
            return content.get_text(strip=True)
        return "본문을 불러올 수 없습니다."
    except Exception as e:
        return f"기사 본문을 불러오는 중 오류 발생: {e}"

# ✅ 요약 모델 캐싱
@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

summarizer = load_summarizer()

# ✅ Streamlit UI
st.title("📰 AI 뉴스 요약 웹앱")
st.markdown("최신 IT 뉴스를 인공지능이 자동으로 요약해줍니다.")

# 뉴스 목록 가져오기
news_list = get_news_links()

# 디버깅 로그
print(f"뉴스 목록: {news_list}")

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
