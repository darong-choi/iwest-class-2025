import streamlit as st

# 버튼
if st.button('실행'):
    st.write('버튼이 클릭되었습니다!')

# 체크박스
agree = st.checkbox('동의합니다')
if agree:
    st.write('동의하셨습니다!')

# 라디오 버튼
발전소 = st.radio(
    "발전소를 선택하세요",
    ['태안', '평택', '서인천', '군산']
)
st.write(f'선택: {발전소}')

# 선택 박스 (드롭다운)
옵션 = st.selectbox(
    '분석 유형을 선택하세요',
    ['일일 분석', '주간 분석', '월간 분석', '연간 분석']
)

# 멀티 선택
선택항목 = st.multiselect(
    '분석할 발전소를 선택하세요',
    ['태안', '평택', '서인천', '군산'],
    ['태안', '평택']  # 기본 선택
)

##실행하려면 터미널에 streamlit run streamlit_03.py 입력