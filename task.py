
from typing import Optional
from openai import OpenAI

def summarize_meeting(회의록: str, api_key: str)-> str :
    """
    회의록(텍스트)을 입력받아 OpenAI API를 활용해 구조화된 요약을 반환합니다.

    Args:
        회의록 (str): 요약할 회의록 원문 텍스트
        api_key (str): OpenAI API 키

    Returns:
        str: 회의록을 구조화된 양식으로 요약한 결과 텍스트
    """
    user_prompt_template = """
다음 회의록을 분석하여 구조화된 요약을 작성해주세요:

[요약 형식]
📅 회의 개요:
- 일시:
- 참석자:
- 주제:

🎯 주요 논의사항:
1.
2.
3.

✅ 결정사항:
-

📋 Action Items:
- 담당자 | 과제 | 기한

[회의록]
{회의록}"""

    user_content = user_prompt_template.format(회의록=회의록)
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": user_content},
        ],
    )
    print("usage: ", response.usage) #비용 확인 목적
    ai_content = response.choices[0].message.content
    return ai_content

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
    pass

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