import os
from dotenv import load_dotenv
from task import create_email_body

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", default=None) or None

email_body = create_email_body(
    받는사람="이진석 대리", #keyword parameters
    용건="8월 업무보고",
    핵심내용="8월 휴가 계획 알려줘",
    api_key=OPENAI_API_KEY
)
print(email_body)