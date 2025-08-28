#txt/csv 파일에서 1줄씩 읽어서 처리

with open("./회의록/20250825.txt","rt", encoding="utf-8") as file:
# str -> list[str]
#큰 텍스트 파일을 읽을때는, 메모리 비효울적!!
    # for line in file.read().splitlines():
    #     print(line)

#1줄씩 읽어서 line에 할당하면서, 반복. 메모리 효율적!!
   for line in file:
      print(line)
