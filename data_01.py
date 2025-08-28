import pandas as pd

execl_path = (
"./assets/250825 도서목록.xlsx"
)

#dataframe 타입
# 엑셀 중에 첫번째 시트에 대해서만 반환

df = pd.read_excel(execl_path)
print(df.shape)  # (행, 열)수를 출력
print(df.head()) #첫 5줄 출력

#실행하는 방법 : python data_01.py