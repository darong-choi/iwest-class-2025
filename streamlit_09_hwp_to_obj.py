from dotenv import load_dotenv
import streamlit as st
from utils import hwp_to_html
from pydantic import BaseModel
from utils import make_response

class Person(BaseModel):
    직위: str
    성명: str
    담당업무: list[str]
    대행자 : str | None = None
    전화번호: str | None = None

class OrganizationInfo(BaseModel):
    persons: list[Person]

load_dotenv()

hwp_file = st.file_uploader(
    "변환할 한글 파일을 업로드해주세요.",
    type=["hwp"],
    accept_multiple_files=False,
)
if hwp_file is not None:
    html = hwp_to_html(hwp_file=hwp_file) #키워드 인자
    # st.markdown(html, unsafe_allow_html=True)

    prompt = f"""
            다음 HTML 문서에서 업무분장 정보를 추출해주세요.
            
            HTML 내용:
    {html}
            
            위 HTML에서 테이블 구조를 분석하여 다음 정보를 추출해주세요:
            1. 문서 제목과 날짜
            2. 부서별 구성원 정보:
               - 직위 (부장, 차장, 직원 등)
               - 성명 (이름만)
               - 전화번호 (있는 경우)
               - 담당 업무 목록 (•로 구분된 각 업무를 리스트로)
               - 대행자 (있는 경우)
            
            부서가 여러 개인 경우 각 부서별로 구분하여 추출해주세요.
            """
    response = make_response(
        user_content=prompt,
        response_format=OrganizationInfo,
        model="gpt-4o-mini",
        temperature=0.1,
        
    )

    # st.text(f"AI : {response.parsed}")

    obj: OrganizationInfo = response.parsed
    for person in obj.persons:
        st.text({"직위": person.직위, "성명": person.성명, "담당업무": person.담당업무,"전화번호": person.전화번호, "대행자": person.대행자})