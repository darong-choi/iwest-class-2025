import streamlit as st
from utils import make_response
from dotenv import load_dotenv

load_dotenv()

user_content = st.text_input("지시사항 : ") or "이 이미지를 설명해줘"

image_file = st.file_uploader(
    "설명이 필요한 이미지를 업로드해주세요.",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=False,
)


if image_file is not None:
    st.write(f"이미지가 업로드되었습니다.: {image_file.name}")
    ai_content = make_response(
        user_content=user_content,
        image_file=image_file,

    )
    st.write(ai_content)

                 
#실행하려면 터미널에 streamlit run streamlit_05.py 입력