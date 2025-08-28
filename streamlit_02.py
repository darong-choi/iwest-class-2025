import streamlit as st

# 제목 계층
st.title("# 제목 (Title)")
st.header("## 헤더 (Header)")
st.subheader("### 서브헤더 (Subheader)")

# 일반 텍스트
st.text("일반 텍스트입니다")
st.write("write는 무엇이든 표시합니다")

# 마크다운
st.markdown("""
### 마크다운 지원
- **굵게**
- *기울임*
- `코드`
- [링크](https://streamlit.io)
""")

# 코드 블록
code = '''
def hello():
    print("Hello, Streamlit!")
'''
st.code(code, language='python')

# 수식 (LaTeX)
st.latex(r'''
    효율 = \frac{발전량}{연료사용량} \times 100
''')
