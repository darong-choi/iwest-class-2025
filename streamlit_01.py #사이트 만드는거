from dotenv import load_dotenv ##모든 프로그램의 시작점에서 불러야함
import streamlit as st
from utils import make_response

load_dotenv()

st.title("한국서부발전")

st.markdown("""
안녕하세요. 최주영입니다. 제가 좋아하는 과일은


+ 수박
+ 복숭아
+ 멜론
            """
            )

question = st.text_input ("질문을 입력하세요")
# openai api 활용 : 폐쇄망에서는 사용불가
#폐쇄망이라면 : 다운로드 오픈소스 모델을 활용(ollama)
if st.button("전송") and question: 
    ai_content = make_response(user_content=question)
    st.write(f"AI : {ai_content}")

# 터미널에서  streamlit run streamlit_01.py 시행하면 인터넷 창이 떠짐
