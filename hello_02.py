from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from utils import download_file

page_url = "https://www.iwest.co.kr/iwest/582/subview.do?enc=Zm5jdDF8QEB8JTJGYmJzJTJGaXdlc3QlMkYxNDglMkYyMjUxNCUyRmFydGNsVmlldy5kbyUzRnBhZ2UlM0QxJTI2c3JjaENvbHVtbiUzRCUyNnNyY2hXcmQlM0QlMjZiYnNDbFNlcSUzRCUyNmJic09wZW5XcmRTZXElM0QlMjZyZ3NCZ25kZVN0ciUzRCUyNnJnc0VuZGRlU3RyJTNEJTI2aXNWaWV3TWluZSUzRGZhbHNlJTI2cGFzc3dvcmQlM0QlMjY%3D"

#지정 주소로 get 요청을 보내고 응답을 받습니다.
response = requests.get(page_url)
html: str = response.text
soup = BeautifulSoup(html, "html.parser")
tag = soup.select_one("a[href*=download]")
print(tag["href"])
download_url = urljoin(page_url, tag["href"])
print(download_url)
download_file(download_url,".downloads/2025/08/27/리플릿.pdf")