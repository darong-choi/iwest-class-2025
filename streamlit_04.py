import streamlit as st

# 숫자 입력
발전량 = st.number_input(
    '발전량 입력 (MWh)',
    min_value=0.0,
    max_value=10000.0,
    value=1000.0,
    step=100.0
)

# 슬라이더
가동률 = st.slider(
    '목표 가동률 (%)',
    min_value=0,
    max_value=100,
    value=85,
    step=5
)

# 범위 슬라이더
범위 = st.slider(
    '분석 기간 선택',
    min_value=1,
    max_value=30,
    value=(7, 14)  # 튜플로 범위 지정
)
st.write(f'{범위[0]}일부터 {범위[1]}일까지')

# 날짜 입력
import datetime
날짜 = st.date_input(
    "분석 날짜",
    datetime.date.today()
)

# 시간 입력
시간 = st.time_input('점검 시작 시간', datetime.time(8, 0))
