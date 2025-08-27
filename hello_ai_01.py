import os
from dotenv import load_dotenv
from openai import OpenAI

# .env 파일에서 환경변수 불러오기
load_dotenv()

# 환경변수에서 OPENAI_API_KEY 값을 가져옴 (없으면 None)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", default=None) or None

# 명시적으로 api key를 지정하지 않으면, OpenAI 내부에서 알아서 OPENAI_API_KEY 환경변수 값을 찾습니다.
client = OpenAI(api_key=OPENAI_API_KEY)

def create_chat_completion(client: OpenAI, model: str, messages: list[dict]) -> str:
    """
    OpenAI 챗 모델에 메시지를 보내고 응답을 받아옵니다.

    Args:
        client (OpenAI): OpenAI 클라이언트 인스턴스
        model (str): 사용할 모델 이름
        messages (list[dict]): 대화 메시지 목록

    Returns:
        str: 모델의 응답 메시지
    """
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    print("response.usage :", response.usage)  # 토큰 사용량 출력
    return response.choices[0].message.content  # 모델의 응답 반환

# 대화 메시지 정의
messages = [
    # role : system, user, assistant 등
    {"role": "system", "content": "당신은 서부발전의 최주영입니다."},
    {"role": "user", "content": "자기 소개를 해주세요.이름 3행시도 해주세요"},
]

# 챗봇 응답 받기
result = create_chat_completion(client, "gpt-4o-mini", messages)
print(result)