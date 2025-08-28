import os
import requests
from base64 import b64encode
from openai import OpenAI
from openai.types.shared.chat_model import ChatModel


def make_response(
    user_content: str,
    image_path: str | None = None,
    image_file = None,
    system_content: str | None = None,
    model: str | ChatModel = "gpt-4o-mini",
    temperature: float = 0.25,
    api_key: str | None = None,
) -> str:
    """OpenAI의 Chat Completion API를 사용하여 AI의 응답을 생성합니다.

    Args:
        user_content (str): 사용자 메시지.
        system_content (str | None, optional): 시스템 메시지. 기본값은 None.
        model (str | ChatModel, optional): 사용할 모델. 기본값은 "gpt-4o-mini".
        temperature (float, optional): 생성 결과의 창의성. 기본값은 0.25.
        api_key (str | None, optional): OpenAI API 키. 기본값은 None.

    Returns:
        str: AI가 생성한 응답 메시지.
    """
    messages = []
    if system_content:  # 빈 문자열도 아니고, None도 아닐 때
        messages.append({"role": "system", "content": system_content})
    messages.append({"role": "user", "content": user_content})

    if image_path:
        image_url = make_base64_url(image_path=image_path)

    elif image_file:
        image_url = make_base64_url(image_file=image_file)
    else:
        image_url = None

    if image_url:        
        image_dict = {
            "type": "image_url",
            "image_url": {
                "url": image_url,
                "detail": "high",
            },
        }
        messages.append({"role": "user", "content": [image_dict]})

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content


def download_file(
    file_url: str,
    filepath: str | None = None,  # default parameter
) -> None:
    res = requests.get(file_url)
    print("res ok :", res.ok)

    if filepath is None:
        filepath = os.path.basename(file_url)

    file_content = res.content

    dir_path = os.path.dirname(filepath)
    os.makedirs(dir_path, exist_ok=True)

    # 주의 : 같은 경로의 경로일 경우, 덮어쓰기가 됩니다.
    with open(filepath, "wb") as f:
        f.write(file_content)
        print("saved", filepath)


def multiply(a: int, b: int) -> int:
    """두 개의 숫자를 곱한 결과를 반환합니다.

    Args:
        a (int): 첫 번째 숫자.
        b (int): 두 번째 숫자.

    Returns:
        int: a와 b를 곱한 값.
    """
    return a * b


def make_base64_url(
        image_path: str | None = None,
        image_file=None,
        ) -> str:
    if image_path:
    # 다른 언어의 3항 연산자와 같은 역할
        mime_type = "image/png" if image_path.endswith(".png") else "image/jpeg"
        with open(image_path, "rb") as f:
            image_data: bytes = f.read()
    elif image_file:
        mime_type = image_file.type
        image_data= image_file.read()
    else:
        raise ValueError("image_path 또는 image_file 중 하나는 제공되어야 합니다.")        

    b64_str: str = b64encode(image_data).decode()
    image_url = f"data:{mime_type};base64," + b64_str
    return image_url
