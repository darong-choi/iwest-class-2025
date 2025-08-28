import os
for root, dirs, files in os.walk("."):
    #files: 파일명 리스트
    for filename in files:
        if filename.lower().endswith((".pdf",".hwp")):  #pdf,한글파일
            filepath= os.path.join(root, filename)  #절대경로
            print(filepath)
    
