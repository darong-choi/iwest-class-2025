from dotenv import load_dotenv
import streamlit as st
from pydantic import BaseModel
from utils import make_response

class Person(BaseModel):
    담당: str
    업무: list[str]

class PersonList(BaseModel):
    persons: list[Person]

load_dotenv()

input_textarea = st.text_area("추출한 텍스트를 입력해주세요.") #글 입력하는 창 만드는거

if input_textarea:
    user_content = "내용에서 각각의 담당, 업무를 JSON포맷으로 추출해주세요.\n\n----\n\n" + input_textarea
    ai_response = make_response(
        user_content=user_content,
        response_format=PersonList
        
    )
    obj: PersonList = ai_response.parsed
    for person in obj.persons:
        person.담당
        person.업무 #list[str]        
    st.text(f"AI : {ai_response}")