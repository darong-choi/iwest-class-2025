import os
import requests

file_url = "https://www.iwest.co.kr/sites/iwest/files/plantAroundAreaPreferentialOperationFinalAnnounce.hwp"
res = requests.get(file_url)
print("res ok :", res.ok)

file_name = os.path.basename(file_url)
file_content = res.content

with open(file_name, "wb") as f:
    f.write(file_content)
    print("saved", file_name)