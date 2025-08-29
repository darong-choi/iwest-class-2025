from utils import make_response, hwp_to_html


PROMPT_TEMPLATE_01 = """
안녕하세요. 저는 {name}입니다.
"""

with open("./prompts/업무분장.txt","rt", encoding="utf-8") as f:
    PROMPT_TEMPLATE = f.read()

html = hwp_to_html(hwp_file=hwp_file) #키워드 인자
user_content = PROMPT_TEMPLATE.format(html=html)
make_response(user_content=user_content)

