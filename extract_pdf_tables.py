import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import warnings
warnings.filterwarnings('ignore')

# 필수 라이브러리
import camelot
import pdfplumber
import pandas as pd
from tabulate import tabulate

# tqdm 임포트 (진행 표시)
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    tqdm = lambda x, **kwargs: x  # 더미 함수


@dataclass
class TextBlock:
    """텍스트 블록 정보"""
    text: str
    block_type: str  # 'heading', 'paragraph', 'list_item', 'table'
    level: int = 0  # heading level 또는 list depth
    page_num: int = 1
    bbox: Optional[Tuple[float, float, float, float]] = None  # x0, y0, x1, y1
    metadata: Dict = None


@dataclass
class TableData:
    """테이블 데이터"""
    data: List[List[str]]
    page_num: int
    source: str  # 'pdfplumber' or 'camelot'
    confidence: float = 0.0
    bbox: Optional[Tuple[float, float, float, float]] = None


class PDFExtractor:
    """고급 PDF 추출기"""
    
    def __init__(self, pdf_path: str, output_dir: str = "output"):
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 결과 저장
        self.text_blocks: List[TextBlock] = []
        self.tables: List[TableData] = []
        self.comparison_report: List[str] = []
        
    def extract_all(self):
        """전체 추출 프로세스"""
        print(f"\n📄 PDF 파일 분석: {self.pdf_path}")
        print(f"📏 파일 크기: {self.pdf_path.stat().st_size / 1024:.1f} KB")
        
        # pdfplumber로 추출
        self._extract_with_pdfplumber()

        # Camelot으로 테이블 보완
        self._extract_tables_with_camelot()
        self._cross_validate_tables()
        
        # 결과 저장
        self._save_results()
        
        print(f"\n✅ 추출 완료!")
        print(f"📊 텍스트 블록: {len(self.text_blocks)}개")
        print(f"📊 테이블: {len(self.tables)}개")
        
    def _extract_with_pdfplumber(self):
        """pdfplumber로 텍스트와 테이블 추출"""
        print("\n🔄 pdfplumber로 추출 중...")
        
        with pdfplumber.open(str(self.pdf_path)) as pdf:
            pages = tqdm(pdf.pages, desc="페이지 처리") if TQDM_AVAILABLE else pdf.pages
            
            for page_num, page in enumerate(pages, 1):
                # 텍스트 추출 (레이아웃 보존)
                self._extract_text_with_layout(page, page_num)
                
                # 테이블 추출
                tables = page.extract_tables()
                for table_idx, table in enumerate(tables):
                    if table and len(table) > 1:  # 유효한 테이블만
                        table_data = TableData(
                            data=table,
                            page_num=page_num,
                            source='pdfplumber',
                            confidence=self._calculate_table_confidence(table)
                        )
                        self.tables.append(table_data)
                        
                        # 테이블 위치에 마커 추가
                        self.text_blocks.append(TextBlock(
                            text=f"[TABLE_{page_num}_{table_idx + 1}]",
                            block_type='table',
                            page_num=page_num
                        ))
    
    def _extract_text_with_layout(self, page, page_num: int):
        """레이아웃을 보존하며 텍스트 추출"""
        # 텍스트를 문자 단위로 추출하여 스타일 정보 분석
        chars = page.chars if hasattr(page, 'chars') else []
        
        # 폰트 크기별로 그룹화 (heading 감지용)
        font_sizes = {}
        for char in chars:
            size = round(char.get('height', 0))
            if size not in font_sizes:
                font_sizes[size] = []
            font_sizes[size].append(char)
        
        # 평균 폰트 크기 계산
        if font_sizes:
            sizes = list(font_sizes.keys())
            avg_size = sum(sizes) / len(sizes) if sizes else 12
        else:
            avg_size = 12
        
        # 텍스트 라인별로 추출
        text = page.extract_text()
        if not text:
            return
        
        lines = text.split('\n')
        current_paragraph = []
        
        for line in lines:
            line = line.strip()
            if not line:
                # 빈 줄 = 단락 구분
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    self._add_text_block(paragraph_text, page_num, avg_size)
                    current_paragraph = []
                continue
            
            current_paragraph.append(line)
        
        # 마지막 단락 처리
        if current_paragraph:
            paragraph_text = ' '.join(current_paragraph)
            self._add_text_block(paragraph_text, page_num, avg_size)
    
    def _add_text_block(self, text: str, page_num: int, avg_font_size: float):
        """텍스트 블록 추가 (타입 자동 판별)"""
        if not text:
            return
        
        # Heading 판별 (짧고 대문자가 많거나 특별한 패턴)
        is_heading = False
        heading_level = 0
        
        # 제목 패턴들
        if len(text) < 100:  # 짧은 텍스트
            # 숫자로 시작하는 섹션
            if re.match(r'^\d+[\.\)]\s+', text):
                is_heading = True
                heading_level = 2
            # 대문자로 시작하고 짧은 경우
            elif text.isupper() or (text[0].isupper() and len(text) < 50):
                is_heading = True
                heading_level = 1
            # 특수 키워드
            elif any(keyword in text.lower() for keyword in ['장', '절', '부', '팀', '담당']):
                is_heading = True
                heading_level = 2
        
        # List item 판별
        is_list = False
        list_depth = 0

        list_patterns = [
            (r'^[○●▪▫•·]\s+', 1),  # 불릿 포인트
            (r'^[-*+]\s+', 1),       # 대시, 별표
            (r'^\d+[\.\)]\s+', 1),   # 숫자 리스트
            (r'^[가-하][\.\)]\s+', 2),  # 한글 리스트
            (r'^[a-z][\.\)]\s+', 2),   # 영문 소문자 리스트
        ]
        
        for pattern, depth in list_patterns:
            if re.match(pattern, text):
                is_list = True
                list_depth = depth
                break
        
        # 들여쓰기 감지 (추가 depth)
        leading_spaces = len(text) - len(text.lstrip())
        if leading_spaces > 4:
            list_depth += 1
        
        # 블록 타입 결정
        if is_heading:
            block_type = 'heading'
            level = heading_level
        elif is_list:
            block_type = 'list_item'
            level = list_depth
        else:
            block_type = 'paragraph'
            level = 0
        
        # 텍스트 블록 추가
        self.text_blocks.append(TextBlock(
            text=text,
            block_type=block_type,
            level=level,
            page_num=page_num
        ))
    
    def _extract_tables_with_camelot(self):
        """Camelot으로 테이블 추출"""

        print("\n🔄 Camelot으로 테이블 보완 중...")
        
        try:
            # 모든 페이지에서 테이블 추출 시도
            # stream 모드: 테이블 경계가 명확하지 않은 경우
            tables_stream = camelot.read_pdf(
                str(self.pdf_path),
                pages='all',
                flavor='stream',
                suppress_stdout=True
            )
            
            for table in tables_stream:
                if len(table.df) > 1:  # 유효한 테이블만
                    table_data = TableData(
                        data=table.df.values.tolist(),
                        page_num=table.page,
                        source='camelot_stream',
                        confidence=table.accuracy
                    )
                    self.tables.append(table_data)
            
            # lattice 모드: 테이블 경계가 명확한 경우
            try:
                tables_lattice = camelot.read_pdf(
                    str(self.pdf_path),
                    pages='all',
                    flavor='lattice',
                    suppress_stdout=True
                )
                
                for table in tables_lattice:
                    if len(table.df) > 1:
                        table_data = TableData(
                            data=table.df.values.tolist(),
                            page_num=table.page,
                            source='camelot_lattice',
                            confidence=table.accuracy
                        )
                        self.tables.append(table_data)
            except:
                pass  # lattice 모드 실패 시 무시
                
        except Exception as e:
            self.comparison_report.append(f"Camelot 오류: {str(e)}")
    
    def _calculate_table_confidence(self, table: List[List]) -> float:
        """테이블 신뢰도 계산"""
        if not table:
            return 0.0
        
        # 기준: 셀이 비어있지 않은 비율, 열 일관성 등
        total_cells = sum(len(row) for row in table)
        non_empty_cells = sum(1 for row in table for cell in row if cell and str(cell).strip())
        
        if total_cells == 0:
            return 0.0
        
        # 비어있지 않은 셀 비율
        fill_rate = non_empty_cells / total_cells
        
        # 열 수 일관성
        col_counts = [len(row) for row in table]
        if col_counts:
            most_common_cols = max(set(col_counts), key=col_counts.count)
            consistency_rate = col_counts.count(most_common_cols) / len(col_counts)
        else:
            consistency_rate = 0
        
        # 종합 신뢰도
        confidence = (fill_rate * 0.6 + consistency_rate * 0.4) * 100
        return round(confidence, 2)
    
    def _cross_validate_tables(self):
        """여러 소스의 테이블 교차 검증 및 병합"""

        print("\n🔄 테이블 교차 검증 중...")
        
        # 페이지별로 테이블 그룹화
        tables_by_page = {}
        for table in self.tables:
            if table.page_num not in tables_by_page:
                tables_by_page[table.page_num] = []
            tables_by_page[table.page_num].append(table)
        
        # 각 페이지에서 최적 테이블 선택
        validated_tables = []
        
        for page_num, page_tables in tables_by_page.items():
            if len(page_tables) == 1:
                validated_tables.append(page_tables[0])
            else:
                # 여러 소스가 있는 경우 비교
                sources = {}
                for table in page_tables:
                    if table.source not in sources:
                        sources[table.source] = []
                    sources[table.source].append(table)
                
                # 소스별 최고 신뢰도 테이블 선택
                best_tables = []
                for source, tables in sources.items():
                    best = max(tables, key=lambda t: t.confidence)
                    best_tables.append(best)
                
                # 전체에서 최고 신뢰도 선택
                if best_tables:
                    best_table = max(best_tables, key=lambda t: t.confidence)
                    validated_tables.append(best_table)
                    
                    # 비교 리포트 추가
                    self.comparison_report.append(
                        f"Page {page_num}: 선택된 소스 = {best_table.source} "
                        f"(신뢰도: {best_table.confidence:.1f}%)"
                    )
        
        # 검증된 테이블로 교체
        self.tables = validated_tables
    
    def _save_results(self):
        """결과 저장"""
        print("\n💾 결과 저장 중...")
        
        # 1. Markdown 저장
        self._save_markdown()
        
        # 2. HTML 저장
        self._save_html()
        
        # 3. JSON 저장
        self._save_json()
        
        # 4. 테이블 CSV/Excel 저장
        self._save_tables()
        
        # 5. 비교 리포트 저장
        if self.comparison_report:
            report_path = self.output_dir / "comparison_report.txt"
            report_path.write_text('\n'.join(self.comparison_report), encoding='utf-8')
            print(f"  ✅ 비교 리포트: {report_path}")
    
    def _save_markdown(self):
        """Markdown 형식으로 저장"""
        md_lines = []
        current_page = 0
        
        for block in self.text_blocks:
            # 페이지 구분
            if block.page_num != current_page:
                current_page = block.page_num
                md_lines.append(f"\n---\n\n# 📄 Page {current_page}\n")
            
            # 블록 타입별 포맷팅
            if block.block_type == 'heading':
                prefix = '#' * (block.level + 1)
                md_lines.append(f"\n{prefix} {block.text}\n")
            elif block.block_type == 'list_item':
                indent = '  ' * (block.level - 1)
                md_lines.append(f"{indent}- {block.text}")
            elif block.block_type == 'table':
                # 테이블 마커 찾기
                table_match = re.match(r'\[TABLE_(\d+)_(\d+)\]', block.text)
                if table_match:
                    page_num = int(table_match.group(1))
                    table_idx = int(table_match.group(2))
                    
                    # 해당 테이블 찾기
                    for table in self.tables:
                        if table.page_num == page_num:
                            md_lines.append(f"\n### 📊 Table {table_idx}\n")
                            if table.data:
                                # 테이블을 Markdown 형식으로 변환
                                md_table = tabulate(
                                    table.data[1:] if len(table.data) > 1 else table.data,
                                    headers=table.data[0] if table.data else [],
                                    tablefmt='pipe'
                                )
                                md_lines.append(md_table)
                                md_lines.append(f"\n*Source: {table.source}, Confidence: {table.confidence:.1f}%*\n")
                            break
            else:  # paragraph
                md_lines.append(f"\n{block.text}\n")
        
        # 파일 저장
        md_path = self.output_dir / "extracted_text.md"
        md_path.write_text('\n'.join(md_lines), encoding='utf-8')
        print(f"  ✅ Markdown: {md_path}")
    
    def _save_html(self):
        """HTML 형식으로 저장"""
        html_lines = ["""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF 추출 결과</title>
    <style>
        body { font-family: 'Malgun Gothic', sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }
        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; }
        h3 { color: #7f8c8d; }
        .page-break { border-top: 3px double #bdc3c7; margin: 40px 0; padding-top: 20px; }
        .list-item { margin-left: 20px; }
        .list-item-2 { margin-left: 40px; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .table-info { font-size: 0.9em; color: #7f8c8d; font-style: italic; }
        .paragraph { margin: 15px 0; line-height: 1.6; }
    </style>
</head>
<body>
    <h1>📄 PDF 추출 결과</h1>
        """]
        
        current_page = 0
        
        for block in self.text_blocks:
            # 페이지 구분
            if block.page_num != current_page:
                if current_page > 0:
                    html_lines.append('</div>')
                current_page = block.page_num
                html_lines.append(f'<div class="page-break"><h2>Page {current_page}</h2>')
            
            # 블록 타입별 HTML
            if block.block_type == 'heading':
                tag = f'h{min(block.level + 2, 6)}'
                html_lines.append(f'<{tag}>{block.text}</{tag}>')
            elif block.block_type == 'list_item':
                class_name = f'list-item-{block.level}' if block.level > 1 else 'list-item'
                html_lines.append(f'<div class="{class_name}">• {block.text}</div>')
            elif block.block_type == 'table':
                # 테이블 HTML
                table_match = re.match(r'\[TABLE_(\d+)_(\d+)\]', block.text)
                if table_match:
                    page_num = int(table_match.group(1))
                    table_idx = int(table_match.group(2))
                    
                    for table in self.tables:
                        if table.page_num == page_num:
                            html_lines.append(f'<h3>Table {table_idx}</h3>')
                            if table.data:
                                html_lines.append('<table>')
                                # 헤더
                                if len(table.data) > 0:
                                    html_lines.append('<thead><tr>')
                                    for cell in table.data[0]:
                                        html_lines.append(f'<th>{cell if cell else ""}</th>')
                                    html_lines.append('</tr></thead>')
                                # 본문
                                if len(table.data) > 1:
                                    html_lines.append('<tbody>')
                                    for row in table.data[1:]:
                                        html_lines.append('<tr>')
                                        for cell in row:
                                            html_lines.append(f'<td>{cell if cell else ""}</td>')
                                        html_lines.append('</tr>')
                                    html_lines.append('</tbody>')
                                html_lines.append('</table>')
                                html_lines.append(f'<div class="table-info">Source: {table.source}, Confidence: {table.confidence:.1f}%</div>')
                            break
            else:  # paragraph
                html_lines.append(f'<p class="paragraph">{block.text}</p>')
        
        if current_page > 0:
            html_lines.append('</div>')
        
        html_lines.append('</body></html>')
        
        # 파일 저장
        html_path = self.output_dir / "extracted_text.html"
        html_path.write_text('\n'.join(html_lines), encoding='utf-8')
        print(f"  ✅ HTML: {html_path}")
    
    def _save_json(self):
        """JSON 형식으로 저장"""
        data = {
            'pdf_file': str(self.pdf_path),
            'total_pages': max([b.page_num for b in self.text_blocks]) if self.text_blocks else 0,
            'total_blocks': len(self.text_blocks),
            'total_tables': len(self.tables),
            'content': []
        }
        
        # 페이지별로 구성
        pages = {}
        for block in self.text_blocks:
            if block.page_num not in pages:
                pages[block.page_num] = {
                    'page_number': block.page_num,
                    'blocks': [],
                    'tables': []
                }
            
            if block.block_type != 'table':
                pages[block.page_num]['blocks'].append({
                    'type': block.block_type,
                    'level': block.level,
                    'text': block.text
                })
        
        # 테이블 추가
        for table in self.tables:
            if table.page_num in pages:
                pages[table.page_num]['tables'].append({
                    'source': table.source,
                    'confidence': table.confidence,
                    'data': table.data
                })
        
        data['content'] = list(pages.values())
        
        # 파일 저장
        json_path = self.output_dir / "extracted_data.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  ✅ JSON: {json_path}")
    
    def _save_tables(self):
        """테이블을 CSV와 Excel로 저장"""
        if not self.tables:
            return
        
        tables_dir = self.output_dir / "tables"
        tables_dir.mkdir(exist_ok=True)
        
        # 개별 CSV 저장
        for idx, table in enumerate(self.tables, 1):
            if table.data:
                df = pd.DataFrame(table.data[1:], columns=table.data[0] if table.data else None)
                csv_path = tables_dir / f"page{table.page_num}_table{idx}.csv"
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        # 통합 Excel 저장
        excel_path = tables_dir / "all_tables.xlsx"
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            for idx, table in enumerate(self.tables, 1):
                if table.data:
                    df = pd.DataFrame(table.data[1:], columns=table.data[0] if table.data else None)
                    sheet_name = f'Page{table.page_num}_T{idx}'[:31]  # Excel 시트명 제한
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"  ✅ Tables: {tables_dir}/")


def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print("사용법: python extract_pdf_advanced.py <PDF파일>")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    
    # 파일 존재 확인
    if not Path(pdf_file).exists():
        print(f"❌ PDF 파일을 찾을 수 없습니다: {pdf_file}")
        sys.exit(1)
    
    # 추출기 실행
    extractor = PDFExtractor(pdf_file)
    extractor.extract_all()


if __name__ == "__main__":
    main()