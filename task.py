
from typing import Optional
from openai import OpenAI



def create_email_body(
    받는사람: str,
    용건: str,
    핵심내용: str,
    api_key: Optional[str] = None,
) -> str:
    """업무 이메일 자동 작성"""

    system_prompt = "당신은 전문적인 비즈니스 이메일 작성자입니다."
    user_prompt_template = """
    다음 정보로 정중하고 전문적인 업무 이메일을 작성해주세요:

    받는 사람: {받는사람}
    용건: {용건}
    핵심 내용: {핵심내용}

    형식:
    - 인사말
    - 용건 설명
    - 상세 내용
    - 마무리 인사
    """

    user_content = user_prompt_template.format(
        받는사람=받는사람, 용건=용건, 핵심내용=핵심내용,
    )

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )

    print("response.usage :", response.usage)
    return response.choices[0].message.content