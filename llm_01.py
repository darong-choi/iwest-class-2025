from dotenv import load_dotenv
from utils import make_response

load_dotenv()

image_path = "./images/gr_salad.jpg"

#todo : pdf, doc 업로드 추가
#todo : pdf -> image 변환 후에 업로드 (dpi)

ai_content = make_response(
    user_content= "이 이미지에 대해 설명해줘",
    image_path=image_path,
)

print("AI :", ai_content)
