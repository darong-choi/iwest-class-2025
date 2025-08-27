import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# like dict
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY" , default=None) or None

#명시적으로 api key를 지정하지 않으면, OpenAI 내부에서 알아서 OPENAI_API_KEY 환경변수 값을 찾습니다.
client = OpenAI(api_key=OPENAI_API_KEY)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        #role : system, user, assistant etc.
        {"role": "system","content": "당신은 서부발전의 최주영입니다."},
        {"role": "user", "content": "자기 소개를 해주세요.이름 3행시도 해주세요"},
    ],
)
print("response.usage :", response.usage)
print(response.choices[0].message.content)