# iwest-class-2025

OpenAI API, 파일 다운로드, 웹 크롤링 등 다양한 Python 실습 예제 코드 모음입니다.

## 폴더/파일 구조 및 설명

- `hello_01.py` : 파일 다운로드 예제 (requests 사용)
- `hello_02.py` : 웹페이지에서 파일 링크 추출 및 다운로드 예제 (BeautifulSoup, utils 활용)
- `hello_ai_01.py` : OpenAI 챗 API 함수화 예제 (환경변수, dotenv, openai)
- `hello_ai_02.py` : OpenAI 챗봇 대화 예제 (콘솔 기반)
- `utils.py` : 파일 다운로드 함수, 곱셈 함수 등 유틸리티
- `requirements.txt` : 필요한 패키지 목록

## 가상환경 생성 및 활성화 (Windows 기준)

1. 가상환경 생성

```
python -m venv venv
```

2. 가상환경 활성화

```
venv\Scripts\activate
```

3. 가상환경 비활성화

```
deactivate
```

## 패키지 설치

가상환경이 활성화된 상태에서 아래 명령어로 필요한 패키지를 설치하세요.

```
pip install -r requirements.txt
```

## 실행 방법 예시

```
python hello_01.py
python hello_02.py
python hello_ai_01.py
python hello_ai_02.py
```

## 참고
- .env 파일에 OpenAI API 키를 저장하여 사용합니다.
- 일부 예제는 인터넷 연결이 필요합니다.
