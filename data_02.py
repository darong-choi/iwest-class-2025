import pandas as pd
import streamlit as st

excel_file = st.file_uploader(
    "엑셀 파일을 업로드해주세요.",
    type=["xlsx", "xls"],
    accept_multiple_files=False,
)
if excel_file is not None:
    df = pd.read_excel(excel_file)
    st.dataframe(df)

