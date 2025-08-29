import streamlit as st
from utils import hwp_to_html

hwp_file = st.file_uploader(
    "변환할 한글 파일을 업로드해주세요.",
    type=["hwp"],
    accept_multiple_files=False,
)
if hwp_file is not None:
    # html = hwp_to_html(None,hwp_file) #위치 인자
    html = hwp_to_html(hwp_file=hwp_file) #키워드 인자
    st.markdown(html, unsafe_allow_html=True)
