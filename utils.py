import os
import mimetypes
import requests
import tempfile
from base64 import b64encode
from dataclasses import dataclass
from typing import BinaryIO, Protocol, TypeVar, Generic, overload
from pydantic import BaseModel
from openai import OpenAI
from openai.types.shared.chat_model import ChatModel
from bs4 import BeautifulSoup
from hwp5.xmlmodel import Hwp5File
from hwp5.hwp5html import HTMLTransform
from contextlib import closing


class FileUploadProtocol(Protocol):
    """파일 업로드 객체의 프로토콜 정의.

    Streamlit의 UploadedFile, Flask의 FileStorage 등을 지원합니다.
    """

    @property
    def name(self) -> str: ...  # 파일명
    @property
    def type(self) -> str: ...  # MIME 타입
    def read(self) -> bytes: ...  # 파일 내용 읽기


@dataclass
class Usage:
    """API 사용량 정보를 담는 클래스.

    Attributes:
        input_tokens: 입력 토큰 수 (prompt_tokens)
        output_tokens: 출력 토큰 수 (completion_tokens)
        total_tokens: 전체 토큰 수
    """

    input_tokens: int
    output_tokens: int
    total_tokens: int


class ResponseWithUsage(str):
    """문자열처럼 동작하면서 usage 정보를 포함하는 응답 클래스.

    일반 문자열처럼 사용할 수 있으며, 추가로 usage 속성을 통해
    토큰 사용량 정보에 접근할 수 있습니다.
    """

    def __new__(cls, content: str, usage: Usage | None = None):
        """ResponseWithUsage 인스턴스 생성.

        Args:
            content: 응답 내용 문자열
            usage: 토큰 사용량 정보 (선택사항)

        주의: __init__ 대신 __new__를 사용하는 이유
        - str은 불변(immutable) 객체라서 생성 후에는 값을 변경할 수 없음
        - __new__는 객체 생성 시점에 호출되어 str 값을 설정 가능
        - __init__은 객체 생성 후 호출되므로 str 값 변경 불가
        """
        # 1. str 타입의 인스턴스를 content 값으로 생성
        instance = super().__new__(cls, content)
        # 2. 생성된 인스턴스에 usage 정보를 속성으로 추가
        instance._usage = usage
        # 3. 완성된 인스턴스 반환
        return instance

    @property
    def usage(self) -> Usage | None:
        """토큰 사용량 정보를 반환합니다."""
        return self._usage


# TypeVar for Generic support
T = TypeVar("T", bound=BaseModel)


class StructuredResponseWithUsage(Generic[T]):
    """Pydantic 모델 인스턴스와 usage 정보를 포함하는 응답 클래스.

    일반 Pydantic 모델처럼 사용하면서 추가로 usage 정보에 접근할 수 있습니다.

    Attributes:
        parsed: 파싱된 Pydantic 모델 인스턴스
        usage: 토큰 사용량 정보 (선택사항)
    """

    def __init__(self, parsed: T, usage: Usage | None = None):
        """StructuredResponseWithUsage 인스턴스 생성.

        Args:
            parsed: 파싱된 Pydantic 모델 인스턴스
            usage: 토큰 사용량 정보 (선택사항)
        """
        self.parsed = parsed
        self.usage = usage


def get_mime_type(file_path: str) -> str:
    """파일 경로에서 MIME 타입을 추론합니다.

    Args:
        file_path (str): 파일 경로

    Returns:
        str: MIME 타입 문자열

    Note:
        확장자 기반으로 추론하며, 알 수 없는 확장자의 경우
        'application/octet-stream'을 반환합니다.
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"


# Overload for when response_format is provided (returns StructuredResponseWithUsage)
@overload
def make_response(
    user_content: str,
    *,
    response_format: type[T],
    file_path: str | None = None,
    file: FileUploadProtocol | BinaryIO | None = None,
    image_path: str | None = None,
    image_file: FileUploadProtocol | BinaryIO | None = None,
    system_content: str | None = None,
    model: str | ChatModel = "gpt-4o-mini",
    temperature: float = 0.25,
    api_key: str | None = None,
) -> StructuredResponseWithUsage[T]: ...


# Overload for when response_format is not provided (returns ResponseWithUsage)
@overload
def make_response(
    user_content: str,
    file_path: str | None = None,
    file: FileUploadProtocol | BinaryIO | None = None,
    image_path: str | None = None,
    image_file: FileUploadProtocol | BinaryIO | None = None,
    system_content: str | None = None,
    model: str | ChatModel = "gpt-4o-mini",
    temperature: float = 0.25,
    api_key: str | None = None,
    *,
    response_format: None = None,
) -> ResponseWithUsage: ...


def make_response(
    user_content: str,
    file_path: str | None = None,  # 새로운 범용 파일 경로 (이미지/PDF)
    file: (
        FileUploadProtocol | BinaryIO | None
    ) = None,  # 새로운 범용 파일 객체 (이미지/PDF)
    image_path: str | None = None,  # 호환성 유지
    image_file: FileUploadProtocol | BinaryIO | None = None,  # 호환성 유지
    system_content: str | None = None,
    model: str | ChatModel = "gpt-4o-mini",
    temperature: float = 0.25,
    api_key: str | None = None,
    response_format: type[BaseModel] | None = None,  # 새로운 파라미터
) -> ResponseWithUsage | StructuredResponseWithUsage:
    """OpenAI의 Chat Completion API를 사용하여 AI의 응답을 생성합니다.

    이미지 파일(.png, .jpg, .jpeg)과 PDF 파일을 지원하며,
    Pydantic 모델을 사용한 구조화된 출력(Structured Output)도 지원합니다.

    Args:
        user_content (str): 사용자 메시지.
        file_path (str | None, optional): 파일 경로 (이미지/PDF). 기본값은 None.
        file (FileUploadProtocol | BinaryIO | None, optional): 파일 객체 (이미지/PDF). 기본값은 None.
        image_path (str | None, optional): 이미지 파일 경로 (호환성용). 기본값은 None.
        image_file (FileUploadProtocol | BinaryIO | None, optional): 이미지 파일 객체 (호환성용). 기본값은 None.
        system_content (str | None, optional): 시스템 메시지. 기본값은 None.
        model (str | ChatModel, optional): 사용할 모델. 기본값은 "gpt-4o-mini".
        temperature (float, optional): 생성 결과의 창의성. 기본값은 0.25.
        api_key (str | None, optional): OpenAI API 키. 기본값은 None.
        response_format (type[BaseModel] | None, optional): Pydantic 모델 클래스. 기본값은 None.

    Returns:
        ResponseWithUsage | StructuredResponseWithUsage:
            - response_format이 None인 경우: ResponseWithUsage (문자열처럼 사용 가능)
            - response_format이 제공된 경우: StructuredResponseWithUsage (파싱된 Pydantic 모델 포함)

    Examples:
        일반 텍스트 응답:
        >>> response = make_response("안녕하세요")
        >>> print(response)  # "안녕하세요! 무엇을 도와드릴까요?"
        >>> print(response.usage.input_tokens)  # 10

        구조화된 응답:
        >>> class UserInfo(BaseModel):
        ...     name: str
        ...     age: int
        >>> response = make_response(
        ...     "철수는 25살입니다",
        ...     response_format=UserInfo
        ... )
        >>> print(response.parsed.name)  # "철수"
        >>> print(response.parsed.age)  # 25
    """
    # 1. 호환성 처리 (간단하게)
    file_path = file_path or image_path
    file = file or image_file

    # 2. 메시지 리스트 초기화
    messages = []
    if system_content:
        messages.append({"role": "system", "content": system_content})

    # 3. 사용자 메시지 구성
    user_message_content = user_content  # 기본값: 텍스트만

    if file_path or file:
        # 파일 정보 추출 (삼항 연산자 활용)
        filename = os.path.basename(file_path) if file_path else file.name
        mime_type = get_mime_type(file_path) if file_path else file.type

        # base64 URL 생성
        base64_url = make_base64_url(file_path=file_path, file=file)

        # 파일 딕셔너리 생성 (삼항 연산자로 단순화)
        file_dict = (
            {
                "type": "image_url",
                "image_url": {"url": base64_url, "detail": "high"},
            }
            if mime_type.startswith("image/")
            else {
                "type": "file",
                "file": {"filename": filename, "file_data": base64_url},
            }
        )

        # 텍스트와 파일을 포함한 content 구성
        user_message_content = [
            {"type": "text", "text": user_content},
            file_dict,
        ]

    messages.append({"role": "user", "content": user_message_content})

    # 4. API 호출
    client = OpenAI(api_key=api_key)

    # Pydantic 모델이 제공된 경우 - Structured Output 사용
    if response_format is not None:
        # beta.chat.completions.parse를 사용하여 구조화된 출력 생성
        response = client.beta.chat.completions.parse(
            model=model,
            messages=messages,
            response_format=response_format,
            temperature=temperature,
        )

        # Usage 정보 추출
        usage = (
            Usage(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )
            if response.usage
            else None
        )

        # 파싱된 객체와 usage 정보를 함께 반환
        return StructuredResponseWithUsage(
            parsed=response.choices[0].message.parsed,
            usage=usage,
        )

    # 기존 방식 - 일반 텍스트 응답
    else:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )

        # 5. Usage 정보 추출 및 반환
        usage = (
            Usage(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )
            if response.usage
            else None
        )

        return ResponseWithUsage(
            content=response.choices[0].message.content or "",
            usage=usage,
        )


def download_file(
    file_url: str,
    filepath: str | None = None,  # default parameter
) -> None:
    """URL로부터 파일을 다운로드하여 로컬에 저장합니다.

    Args:
        file_url (str): 다운로드할 파일의 URL.
        filepath (str | None, optional): 저장할 파일 경로.
            None인 경우 URL의 파일명을 사용합니다. 기본값은 None.

    Returns:
        None

    Note:
        동일한 경로에 파일이 이미 존재할 경우 덮어씁니다.
    """
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
    file_path: str | None = None,
    file: FileUploadProtocol | BinaryIO | None = None,
    image_path: str | None = None,  # deprecated but kept for compatibility
    image_file: (
        FileUploadProtocol | BinaryIO | None
    ) = None,  # deprecated but kept for compatibility
) -> str:
    """파일을 base64 URL로 변환합니다.

    Args:
        file_path (str | None): 파일 경로 (새로운 방식)
        file (FileUploadProtocol | BinaryIO | None): 파일 객체 (새로운 방식)
        image_path (str | None): 이미지 파일 경로 (호환성 유지)
        image_file (FileUploadProtocol | BinaryIO | None): 이미지 파일 객체 (호환성 유지)

    Returns:
        str: base64로 인코딩된 data URL
    """
    # 호환성: 기존 인자가 있으면 새 인자로 매핑
    if image_path and not file_path:
        file_path = image_path
    if image_file and not file:
        file = image_file

    if file_path:
        # 파일 경로에서 MIME 타입 추론
        mime_type = get_mime_type(file_path)
        with open(file_path, "rb") as f:
            data: bytes = f.read()
    elif file:
        # 파일 객체에서 MIME 타입 가져오기
        mime_type = file.type if hasattr(file, "type") else "application/octet-stream"
        data = file.read()
    else:
        raise ValueError("file_path 혹은 file 인자를 지정해주세요.")

    b64_str: str = b64encode(data).decode()
    url = f"data:{mime_type};base64," + b64_str
    return url


def hwp_to_html(
    hwp_path: str | None = None, hwp_file: FileUploadProtocol | BinaryIO | None = None
) -> str:
    """
    HWP 파일을 HTML 문자열로 변환합니다.

    Args:
        hwp_path: HWP 파일의 경로
        hwp_file: FileUploadProtocol 또는 BinaryIO 타입의 파일 객체

    Returns:
        정제된 HTML 문자열

    Raises:
        ValueError: 입력이 잘못된 경우
        RuntimeError: HWP 변환 실패
    """
    # 입력 검증
    if not hwp_path and not hwp_file:
        raise ValueError("hwp_path 또는 hwp_file 중 하나는 필수입니다.")
    if hwp_path and hwp_file:
        raise ValueError("hwp_path와 hwp_file을 동시에 제공할 수 없습니다.")

    temp_hwp_path = None
    temp_output_dir = None

    try:
        # hwp_file이 제공된 경우 임시 파일로 저장
        if hwp_file:
            # 파일 내용 읽기
            if hasattr(hwp_file, "read"):
                content = hwp_file.read()
                # bytes가 아닌 경우 처리
                if isinstance(content, str):
                    content = content.encode("utf-8")
            else:
                raise ValueError("hwp_file은 read() 메서드를 가져야 합니다.")

            # 임시 HWP 파일 생성
            with tempfile.NamedTemporaryFile(suffix=".hwp", delete=False) as temp_hwp:
                temp_hwp.write(content)
                temp_hwp_path = temp_hwp.name
                working_hwp_path = temp_hwp_path
        else:
            working_hwp_path = hwp_path

        # xmlmodel.Hwp5File을 사용하여 HWP 파일 열기 (hwp5html과 동일한 방식)
        with closing(Hwp5File(working_hwp_path)) as hwp5file:
            # HTMLTransform 인스턴스 생성
            transform = HTMLTransform()

            # 임시 출력 디렉토리 생성
            temp_output_dir = tempfile.mkdtemp()

            # HWP를 HTML로 변환 (디렉토리에 출력)
            transform.transform_hwp5_to_dir(hwp5file, temp_output_dir)

            # 생성된 index.xhtml 파일 읽기
            html_path = os.path.join(temp_output_dir, "index.xhtml")

            if not os.path.exists(html_path):
                raise RuntimeError("HTML 변환 결과를 찾을 수 없습니다.")

            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()

        # BeautifulSoup으로 HTML 파싱 및 정제
        soup = BeautifulSoup(html_content, "html.parser")

        # 불필요한 태그 제거
        for tag in soup.find_all(["script", "style", "link", "img", "meta"]):
            tag.decompose()

        # 모든 인라인 style 속성 제거
        for tag in soup.find_all(True):  # 모든 태그 선택
            if tag.has_attr("style"):
                del tag["style"]
            # 다른 불필요한 속성들도 제거 (class는 유지)
            for attr in ["width", "height", "align", "valign", "bgcolor", "border"]:
                if tag.has_attr(attr):
                    del tag[attr]

        # head 태그 찾기 또는 생성
        head = soup.find("head")
        if not head:
            head = soup.new_tag("head")
            if soup.html:
                soup.html.insert(0, head)
            else:
                # html 태그도 없으면 생성
                html = soup.new_tag("html")
                body = soup.find("body")
                if body:
                    body.extract()
                    html.append(head)
                    html.append(body)
                else:
                    # body도 없으면 전체 콘텐츠를 body로 감싸기
                    body = soup.new_tag("body")
                    for child in list(soup.children):
                        body.append(child.extract())
                    html.append(head)
                    html.append(body)
                soup.append(html)

        # 최소한의 CSS 스타일 추가
        style_tag = soup.new_tag("style")
        style_tag.string = """
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 20px;
            }
            table {
                border-collapse: collapse;
                border: 1px solid #ddd;
                margin: 10px 0;
                width: 100%;
            }
            td, th {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f5f5f5;
                font-weight: bold;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            p {
                margin: 10px 0;
            }
        """
        head.append(style_tag)

        # HTML 문자열로 변환 (XML 선언 제거)
        html_str = str(soup)

        # XML 선언 제거 (있을 경우)
        if html_str.startswith("<?xml"):
            xml_end = html_str.find("?>")
            if xml_end != -1:
                html_str = html_str[xml_end + 2 :].strip()

        return html_str

    except Exception as e:
        raise Exception(f"HWP 변환 중 오류 발생: {e}")
    finally:
        # 임시 파일 및 디렉토리 정리
        if temp_hwp_path and os.path.exists(temp_hwp_path):
            try:
                os.unlink(temp_hwp_path)
            except:
                pass
        if temp_output_dir and os.path.exists(temp_output_dir):
            try:
                # 디렉토리 내 모든 파일 삭제
                import shutil

                shutil.rmtree(temp_output_dir)
            except:
                pass