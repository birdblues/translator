from markdown_it import MarkdownIt
from mdit_py_plugins.dollarmath import dollarmath_plugin
from pprint import pprint
import re

class MarkdownFormatter:
    def __init__(self):
        # markdown-it 파서 초기화
        self.md = MarkdownIt().use(dollarmath_plugin).enable('table')
        # .enable('')  # 테이블 플러그인 활성화
    
    def format(self, raw_text):
        """
        마크다운 텍스트를 포맷팅합니다.
        - YAML front matter를 별도로 처리
        - 수식 블록 ($$...$$)을 별도로 처리
        - 일반 텍스트 단락의 줄바꿈만 제거하여 연속된 텍스트로 병합
        - 헤딩, 코드 블록, 리스트, 테이블 등 다른 마크다운 문법은 그대로 유지
        """
        # YAML front matter 분리
        yaml_front_matter, markdown_content = self._extract_yaml_front_matter(raw_text)
        
        # 마크다운 부분만 파싱
        tokens = self.md.parse(markdown_content)

        # pprint(tokens)
        
        formatted_parts = []
        
        # YAML front matter가 있으면 먼저 추가
        if yaml_front_matter:
            formatted_parts.append(yaml_front_matter)
            formatted_parts.append('')  # YAML과 마크다운 사이 구분용 빈 줄
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            # print("Token type:", token.type, "Content:", token.content)
            
            # 헤딩 처리
            if token.type == 'heading_open':
                heading_text = self._process_heading(tokens, i)
                if heading_text:
                    formatted_parts.append(heading_text)
                    formatted_parts.append('')  # 헤딩 구분용 빈 줄
                i = self._skip_to_closing_token(tokens, i, 'heading_close')
                    
            # 일반 단락 처리 (paragraph만 줄바꿈 병합)
            elif token.type == 'paragraph_open':
                paragraph_text = self._process_paragraph(tokens, i)
                if paragraph_text:
                    formatted_parts.append(paragraph_text)
                    formatted_parts.append('')  # 단락 구분용 빈 줄
                i = self._skip_to_closing_token(tokens, i, 'paragraph_close')
                    
            # 코드 블록 처리 (그대로 유지)
            elif token.type == 'fence':
                code_block = self._reconstruct_code_block(token)
                formatted_parts.append(code_block)
                formatted_parts.append('')  # 구분용 빈 줄
                i += 1
            
            # 들여쓰기 코드 블록 처리 (그대로 유지)
            elif token.type == 'code_block':
                code_block = self._reconstruct_indent_code_block(token)
                formatted_parts.append(code_block)
                formatted_parts.append('')
                i += 1
                
            # 리스트 처리 (원본 그대로 유지)
            elif token.type in ['bullet_list_open', 'ordered_list_open']:
                list_content = self._reconstruct_list(tokens, i, markdown_content)
                formatted_parts.append(list_content)
                formatted_parts.append('')  # 구분용 빈 줄
                i = self._skip_list_tokens(tokens, i)
                
            # 테이블 처리 (원본 그대로 유지)
            elif token.type == 'table_open':
                print("Table found")
                table_content = self._reconstruct_table(tokens, i, markdown_content)
                formatted_parts.append(table_content)
                formatted_parts.append('')  # 구분용 빈 줄
                i = self._skip_table_tokens(tokens, i)
                
            # 인용구 처리 (원본 그대로 유지)
            elif token.type == 'blockquote_open':
                blockquote_content = self._reconstruct_blockquote(tokens, i, markdown_content)
                formatted_parts.append(blockquote_content)
                formatted_parts.append('')  # 구분용 빈 줄
                i = self._skip_blockquote_tokens(tokens, i)
            
            elif token.type == 'math_block':
                block_math_content = token.content.strip()
                formatted_parts.append(f"$$\n{block_math_content}\n$$")
                formatted_parts.append('')
                i += 1
                
            elif token.type == 'html_block':
                block_html_content = token.content.strip()
                formatted_parts.append(block_html_content)
                i += 1  # HTML 블록은 그대로 유지하므로 건너뜀
                
            # 수평선 처리 (그대로 유지)
            elif token.type == 'hr':
                formatted_parts.append('---')
                # formatted_parts.append('')  # 구분용 빈 줄
                i += 1
                
            else:
                i += 1
        
        # 결과 조합 및 정리
        result = '\n'.join(formatted_parts)
        
       
        return result
    
    def _extract_yaml_front_matter(self, text):
        """
        YAML front matter를 추출하고 나머지 마크다운 텍스트와 분리
        Returns: (yaml_front_matter, markdown_content)
        """
        text = text.strip()
        
        # YAML front matter 패턴 매칭
        yaml_pattern = r'^---\s*\n(.*?\n)---\s*\n(.*)$'
        match = re.match(yaml_pattern, text, re.DOTALL)
        
        if match:
            yaml_content = match.group(1).rstrip('\n')
            markdown_content = match.group(2)
            yaml_front_matter = f"---\n{yaml_content}\n---"
            return yaml_front_matter, markdown_content
        else:
            return None, text
    
    def _process_heading(self, tokens, start_idx):
        """헤딩을 처리하여 반환"""
        if start_idx + 1 < len(tokens) and tokens[start_idx + 1].type == 'inline':
            level = int(tokens[start_idx].tag[1])  # h1 -> 1, h2 -> 2, h3 -> 3
            heading_prefix = '#' * level
            heading_content = tokens[start_idx + 1].content.strip()
            return f"{heading_prefix} {heading_content}"
        return None
    
    def _process_paragraph(self, tokens, start_idx):
        """단락을 처리하여 줄바꿈을 제거하고 반환"""
        # print("Processing paragraph at index:", start_idx)
        if start_idx + 1 < len(tokens) and tokens[start_idx + 1].type == 'inline':
            # pprint(tokens[start_idx + 1])
            paragraph_content = tokens[start_idx + 1].content.strip()
            # 일반 텍스트의 줄바꿈을 공백으로 병합
            merged_content = ' '.join(paragraph_content.split())
            return merged_content
        return None
    
    def _skip_to_closing_token(self, tokens, start_idx, closing_type):
        """특정 닫는 토큰까지 건너뛰고 다음 인덱스 반환"""
        i = start_idx + 1
        while i < len(tokens) and tokens[i].type != closing_type:
            i += 1
        return i + 1 if i < len(tokens) else len(tokens)
    
    def _reconstruct_indent_code_block(self, token):
        """들여쓰기 코드 블록을 원본 형태로 재구성"""
        code_content = token.content.strip()
        # 들여쓰기 코드 블록은 ``` 없이 시작하므로, ``` 없이 재구성
        return f"    {code_content.replace('\n', '\n    ')}"

    def _reconstruct_code_block(self, token):
        """코드 블록을 원본 형태로 재구성"""
        lang = token.info.strip() if token.info else ''
        code_content = token.content.rstrip('\n')
        
        if lang:
            return f"```{lang}\n{code_content}\n```"
        else:
            return f"```\n{code_content}\n```"
    
    def _reconstruct_list(self, tokens, start_idx, raw_text):
        """리스트를 원본 형태로 재구성"""
        # 토큰의 위치 정보를 이용해 원본 텍스트에서 리스트 부분 추출
        start_token = tokens[start_idx]
        end_idx = self._find_list_end(tokens, start_idx)
        
        if end_idx < len(tokens):
            end_token = tokens[end_idx - 1]
            
            # 토큰에 위치 정보가 있는 경우 원본에서 추출
            if hasattr(start_token, 'map') and hasattr(end_token, 'map') and start_token.map and end_token.map:
                lines = raw_text.split('\n')
                list_lines = lines[start_token.map[0]:end_token.map[1]]
                return '\n'.join(list_lines)
        
        # 위치 정보가 없는 경우 간단한 재구성
        return self._simple_list_reconstruction(tokens, start_idx)
    
    def _simple_list_reconstruction(self, tokens, start_idx):
        """간단한 리스트 재구성 (fallback)"""
        result = []
        i = start_idx + 1
        is_ordered = tokens[start_idx].type == 'ordered_list_open'
        item_counter = 1
        
        while i < len(tokens) and tokens[i].type != tokens[start_idx].type.replace('_open', '_close'):
            if tokens[i].type == 'list_item_open':
                # pprint(tokens[i])
                # pprint(tokens[i+1])
                # pprint(tokens[i+2])
                # 다음 inline 토큰에서 내용 추출
                if i + 1 < len(tokens) and tokens[i + 1].type == 'paragraph_open':
                    if i + 2 < len(tokens) and tokens[i + 2].type == 'inline':
                        content = tokens[i + 2].content.strip()
                        # 줄바꿈을 공백으로 병합 (단락 내에서)
                        content = ' '.join(content.split())
                        # print("level ", tokens[i].level)
                        level = '  ' * int(tokens[i].level / 2)
                        if is_ordered:
                            result.append(f"{level}{item_counter}. {content}")
                            item_counter += 1
                        else:
                            result.append(f"{level}- {content}")
            i += 1
        
        return '\n'.join(result) if result else "<!-- List content preserved -->"
    
    def _find_list_end(self, tokens, start_idx):
        """리스트의 끝 인덱스를 찾기"""
        return self._skip_list_tokens(tokens, start_idx)
    
    def _skip_list_tokens(self, tokens, start_idx):
        """리스트 토큰들을 건너뛰고 다음 인덱스 반환"""
        depth = 1
        i = start_idx + 1
        
        while i < len(tokens) and depth > 0:
            if tokens[i].type in ['bullet_list_open', 'ordered_list_open']:
                depth += 1
            elif tokens[i].type in ['bullet_list_close', 'ordered_list_close']:
                depth -= 1
            i += 1
            
        return i
    
    def _reconstruct_table(self, tokens, start_idx, raw_text):
        """테이블을 원본 형태로 재구성"""
        result = []
        i = start_idx + 1
        is_header = True
        
        while i < len(tokens) and tokens[i].type != 'table_close':
            if tokens[i].type == 'tr_open':
                row_cells = []
                j = i + 1
                
                while j < len(tokens) and tokens[j].type != 'tr_close':
                    if tokens[j].type in ['td_open', 'th_open']:
                        if j + 1 < len(tokens) and tokens[j + 1].type == 'inline':
                            cell_content = tokens[j + 1].content.strip()
                            row_cells.append(cell_content)
                    j += 1
                
                if row_cells:
                    # 테이블 행 생성
                    result.append('| ' + ' | '.join(row_cells) + ' |')
                    
                    # 첫 번째 행(헤더) 다음에만 구분선 추가
                    if is_header:
                        separator = '| ' + ' | '.join(['---'] * len(row_cells)) + ' |'
                        result.append(separator)
                        is_header = False
                
                i = j
            else:
                i += 1
        
        return '\n'.join(result) if result else "<!-- Table content preserved -->"
    
    def _skip_table_tokens(self, tokens, start_idx):
        """테이블 토큰들을 건너뛰고 다음 인덱스 반환"""
        i = start_idx + 1
        while i < len(tokens) and tokens[i].type != 'table_close':
            i += 1
        return i + 1 if i < len(tokens) else i
    
    def _reconstruct_blockquote(self, tokens, start_idx, raw_text):
        """인용구를 원본 형태로 재구성"""
        result = []
        i = start_idx + 1
        
        while i < len(tokens) and tokens[i].type != 'blockquote_close':
            if tokens[i].type == 'paragraph_open':
                if i + 1 < len(tokens) and tokens[i + 1].type == 'inline':
                    content = tokens[i + 1].content.strip()
                    # 줄바꿈을 공백으로 병합 (단락 내에서)
                    merged_content = ' '.join(content.split())
                    result.append(f"> {merged_content}")
            i += 1
        
        return '\n'.join(result) if result else "<!-- Blockquote content preserved -->"
    
    def _skip_blockquote_tokens(self, tokens, start_idx):
        """인용구 토큰들을 건너뛰고 다음 인덱스 반환"""
        i = start_idx + 1
        while i < len(tokens) and tokens[i].type != 'blockquote_close':
            i += 1
        return i + 1 if i < len(tokens) else i

