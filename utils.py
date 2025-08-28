import os
import requests
from openai import OpenAI
from openai.types.shared.chat_model import ChatModel

def make_response(
        user_content: str,
        system_content: str | None = None,
        temperature: float = 0.25,
        model: str  | ChatModel = "gpt-4o-mini",
        api_key: str | None = None,
 ) -> str:
    messages = []
    if system_content:  #빈 문자열도 아니고, None도 아닐때
        messages.append({"role": "system", "content": system_content})
    messages.append({"role": "user", "content": user_content})
    client = OpenAI(api_key)
    response =  client.chat.completions.create(
        model= model,
        messages=messages,
        temperature=0.2,
    )
    return response.choices[0].message.content

def download_file(
        file_url: str, 
        filepath: str | None = None, #default parameter
) -> None:
    res = requests.get(file_url)
    print("res ok :", res.ok)

    if filepath is None:
        filepath = os.path.basename(file_url)

    file_content = res.content

    dir_path = os.path.dirname(filepath)
    os.makedirs(dir_path, exist_ok= True)

#주의 : 같인 경로의 경로일 경우, 덮어쓰기가 됩니다.
    with open(filepath, "wb") as f:
        f.write(file_content)
        print("saved", filepath) 

def multiply(a: int, b: int) -> int:
    """두 개의 정수를 곱한 결과를 반환합니다.

    Args:
        a (int): 첫 번째 정수
        b (int): 두 번째 정수

    Returns:
        int: a와 b를 곱한 값
    """
    return a * b