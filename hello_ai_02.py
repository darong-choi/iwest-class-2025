import os
from dotenv import load_dotenv
from openai import OpenAI

# .env 파일에서 환경변수 불러오기
load_dotenv()

# 환경변수에서 OPENAI_API_KEY 값을 가져옴 (없으면 None)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", default=None) or None

# 명시적으로 api key를 지정하지 않으면,
# OpenAI 내부에서 알아서 OPENAI_API_KEY 환경변수 값을 찾습니다.
client = OpenAI(api_key=OPENAI_API_KEY)

messages = [
    {"role": "system", "content": "당신은 서부발전의 최주영 대리입니다."},

]
while True:
    user_content = input("Human: ").strip()
    if user_content in ["" or "quit"]:
        break

    messages.append(
        {"role": "user", "content": user_content}
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )
    # print("response.usage :", response.usage)  # 토큰 사용량 출력
    assistant_content : str = response.choices[0].message.content
    print("AI :",assistant_content)
    messages.append(
        {"role": "assistant", "content": assistant_content}
    )