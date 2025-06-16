import re
from typing import Dict, Tuple


class MarkdownProtector:
    """
    마크다운 텍스트의 특수 블록들을 플레이스홀더로 보호하고 복원하는 클래스
    
    지원하는 블록 타입:
    - YAML front matter
    - 수식 블록 ($$...$$)
    - 코드 블록 (```...```)
    - 들여쓰기 블록
    - 테이블 블록
    - HTML 태그 블록
    """
    
    def __init__(self):
        """MarkdownProtector 인스턴스 초기화"""
        self.protected_blocks = {
            'yaml': {},
            'math': {},
            'code': {},
            'indent': {},
            'table': {},
            'html': {}
        }
    
    def protect(self, text: str) -> str:
        """
        모든 특수 블록을 보호하는 통합 메서드
        
        Args:
            text: 보호할 마크다운 텍스트
            
        Returns:
            보호된 텍스트
        """
        protected_text = text
        
        # 순서가 중요합니다 - 우선순위에 따라 보호
        protected_text, self.protected_blocks['yaml'] = self._protect_yaml_front_matter(protected_text)
        protected_text, self.protected_blocks['math'] = self._protect_math_blocks(protected_text)
        protected_text, self.protected_blocks['code'] = self._protect_code_blocks(protected_text)
        protected_text, self.protected_blocks['indent'] = self._protect_indent_blocks(protected_text)
        protected_text, self.protected_blocks['table'] = self._protect_table_blocks(protected_text)
        protected_text, self.protected_blocks['html'] = self._protect_html_blocks(protected_text)
        
        return protected_text
    
    def restore(self, text: str) -> str:
        """
        모든 보호된 블록을 복원하는 통합 메서드
        
        Args:
            text: 복원할 텍스트
            
        Returns:
            복원된 텍스트
        """
        restored_text = text
        
        # 보호와 역순으로 복원
        restored_text = self._restore_html_blocks(restored_text, self.protected_blocks['html'])
        restored_text = self._restore_table_blocks(restored_text, self.protected_blocks['table'])
        restored_text = self._restore_indent_blocks(restored_text, self.protected_blocks['indent'])
        restored_text = self._restore_code_blocks(restored_text, self.protected_blocks['code'])
        restored_text = self._restore_math_blocks(restored_text, self.protected_blocks['math'])
        restored_text = self._restore_yaml_front_matter(restored_text, self.protected_blocks['yaml'])
        
        return restored_text
    
    def _protect_yaml_front_matter(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        YAML front matter를 보호하기 위해 플레이스홀더로 치환
        
        Args:
            text: 입력 텍스트
            
        Returns:
            (보호된 텍스트, YAML 블록 딕셔너리)
        """
        yaml_blocks = {}
        protected_text = text
        
        # YAML front matter 패턴
        yaml_pattern = r'^---\n([\s\S]*?)\n---'
        match = re.search(yaml_pattern, text)
        
        if match:
            placeholder = "__YAML_FRONT_MATTER__"
            yaml_content = match.group(0)
            yaml_blocks[placeholder] = yaml_content
            
            # 플레이스홀더로 치환
            protected_text = protected_text[:match.start()] + placeholder + protected_text[match.end():]
        
        return protected_text, yaml_blocks
    
    def _restore_yaml_front_matter(self, text: str, yaml_blocks: Dict[str, str]) -> str:
        """플레이스홀더를 원래 YAML front matter로 복원"""
        result = text
        for placeholder, yaml_block in yaml_blocks.items():
            result = result.replace(placeholder, yaml_block)
        return result
    
    def _protect_math_blocks(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        수식 블록을 보호하기 위해 플레이스홀더로 치환
        
        Args:
            text: 입력 텍스트
            
        Returns:
            (보호된 텍스트, 수식 블록 딕셔너리)
        """
        math_blocks = {}
        protected_text = text
        
        # 블록 수식 패턴 (전체 수식 블록을 캡처)
        block_math_pattern = r'(\$\$\s*\n?.*?\n?\s*\$\$)'
        matches = list(re.finditer(block_math_pattern, text, re.DOTALL))
        
        # 역순으로 처리하여 인덱스 변화 방지
        for i, match in enumerate(reversed(matches)):
            placeholder = f"__MATH_BLOCK_{len(matches) - 1 - i}__"
            math_content = match.group(1)  # 전체 수식 블록을 그대로 보존
            math_blocks[placeholder] = math_content
            
            # 플레이스홀더로 치환
            protected_text = protected_text[:match.start()] + placeholder + protected_text[match.end():]
        
        return protected_text, math_blocks
    
    def _restore_math_blocks(self, text: str, math_blocks: Dict[str, str]) -> str:
        """플레이스홀더를 원래 수식 블록으로 복원"""
        result = text
        for placeholder, math_block in math_blocks.items():
            result = result.replace(placeholder, math_block)
        return result
    
    def _protect_code_blocks(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        백틱 코드 블록을 보호하기 위해 플레이스홀더로 치환
        
        Args:
            text: 입력 텍스트
            
        Returns:
            (보호된 텍스트, 코드 블록 딕셔너리)
        """
        code_blocks = {}
        protected_text = text
        
        # 백틱 코드 블록 패턴 (언어 지정 포함)
        # ```` 또는 ``` 로 시작하고 선택적 언어 지정
        # code_pattern = r'(````\w*\n[\s\S]*?````|```\w*\n[\s\S]*?```)'
        code_pattern = r'(````[^\n]*\n[\s\S]*?````|```[^\n]*\n[\s\S]*?```)'
        matches = list(re.finditer(code_pattern, text, re.MULTILINE))
        
        # 역순으로 처리하여 인덱스 변화 방지
        for i, match in enumerate(reversed(matches)):
            placeholder = f"__CODE_BLOCK_{len(matches) - 1 - i}__"
            code_content = match.group(1)
            code_blocks[placeholder] = code_content
            
            # 플레이스홀더로 치환
            protected_text = protected_text[:match.start()] + placeholder + protected_text[match.end():]
        
        return protected_text, code_blocks
    
    def _restore_code_blocks(self, text: str, code_blocks: Dict[str, str]) -> str:
        """플레이스홀더를 원래 코드 블록으로 복원"""
        result = text
        for placeholder, code_block in code_blocks.items():
            result = result.replace(placeholder, code_block)
        return result
    
    def _protect_indent_blocks(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        들여쓰기 블록을 보호하기 위해 플레이스홀더로 치환
        
        Args:
            text: 입력 텍스트
            
        Returns:
            (보호된 텍스트, 들여쓰기 블록 딕셔너리)
        """
        indent_blocks = {}
        protected_text = text
        
        # 들여쓰기 블록 패턴
        # 빈 줄로 구분되고 스페이스나 탭으로 시작하는 연속된 줄들
        indent_pattern = r'(?<=\n\n)(?:[ \t]+[^\n]+\n)+(?=\n|$)'
        matches = list(re.finditer(indent_pattern, text))
        
        # 역순으로 처리하여 인덱스 변화 방지
        for i, match in enumerate(reversed(matches)):
            placeholder = f"__INDENT_BLOCK_{len(matches) - 1 - i}__"
            indent_content = match.group(0)
            indent_blocks[placeholder] = indent_content
            
            # 플레이스홀더로 치환
            protected_text = protected_text[:match.start()] + placeholder + protected_text[match.end():]
        
        return protected_text, indent_blocks
    
    def _restore_indent_blocks(self, text: str, indent_blocks: Dict[str, str]) -> str:
        """플레이스홀더를 원래 들여쓰기 블록으로 복원"""
        result = text
        for placeholder, indent_block in indent_blocks.items():
            result = result.replace(placeholder, indent_block)
        return result
    
    def _protect_table_blocks(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        마크다운 테이블 블록을 보호하기 위해 플레이스홀더로 치환
        
        Args:
            text: 입력 텍스트
            
        Returns:
            (보호된 텍스트, 테이블 블록 딕셔너리)
        """
        table_blocks = {}
        protected_text = text
        
        # 테이블 패턴
        # 1. 헤더 행: |로 시작하고 끝나는 행
        # 2. 구분 행: |-로 구성된 행
        # 3. 데이터 행들: |로 시작하고 끝나는 행들
        table_pattern = r'(\|[^\n]+\|\n\|[-|\s]+\|\n(?:\|[^\n]+\|\n?)+)'
        matches = list(re.finditer(table_pattern, text))
        
        # 역순으로 처리하여 인덱스 변화 방지
        for i, match in enumerate(reversed(matches)):
            placeholder = f"__TABLE_BLOCK_{len(matches) - 1 - i}__"
            table_content = match.group(1)
            table_blocks[placeholder] = table_content
            
            # 플레이스홀더로 치환
            protected_text = protected_text[:match.start()] + placeholder + protected_text[match.end():]
        
        return protected_text, table_blocks
    
    def _restore_table_blocks(self, text: str, table_blocks: Dict[str, str]) -> str:
        """플레이스홀더를 원래 테이블 블록으로 복원"""
        result = text
        for placeholder, table_block in table_blocks.items():
            result = result.replace(placeholder, table_block)
        return result
    
    def _protect_html_blocks(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        HTML 태그들을 보호하기 위해 플레이스홀더로 치환
        
        Args:
            text: 입력 텍스트
            
        Returns:
            (보호된 텍스트, HTML 블록 딕셔너리)
        """
        html_blocks = {}
        protected_text = text
        block_counter = 0
        
        # 1단계: 주석과 스크립트/스타일 태그 먼저 처리 (내부 파싱 방지)
        priority_patterns = [
            r'<!--[\s\S]*?-->',                    # HTML 주석
            r'<script[^>]*>[\s\S]*?</script>',     # 스크립트 태그
            r'<style[^>]*>[\s\S]*?</style>',       # 스타일 태그
        ]
        
        for pattern in priority_patterns:
            matches = list(re.finditer(pattern, protected_text, re.MULTILINE | re.IGNORECASE))
            for match in reversed(matches):
                placeholder = f"__HTML_TAG_{block_counter}__"
                html_blocks[placeholder] = match.group(0)
                protected_text = protected_text[:match.start()] + placeholder + protected_text[match.end():]
                block_counter += 1
        
        # 2단계: 가장 바깥쪽 태그부터 처리 (greedy 매칭으로 최대한 큰 블록 우선)
        # 모든 HTML 태그 패턴을 한 번에 처리
        html_pattern = r'<[^>]+(?:\s*/>|>[\s\S]*?</[^>]+>|>)'
        
        # 텍스트를 순차적으로 스캔하면서 가장 바깥쪽 태그 찾기
        pos = 0
        while pos < len(protected_text):
            # 다음 HTML 태그 시작점 찾기
            tag_start = protected_text.find('<', pos)
            if tag_start == -1:
                break
            
            # 이미 플레이스홀더인지 확인
            if protected_text[tag_start:tag_start+12] == '__HTML_TAG_':
                # 플레이스홀더 끝까지 건너뛰기
                placeholder_end = protected_text.find('__', tag_start + 12)
                if placeholder_end != -1:
                    pos = placeholder_end + 2
                else:
                    pos = tag_start + 1
                continue
            
            # 태그 이름 추출
            tag_match = re.match(r'<(\w+)', protected_text[tag_start:])
            if not tag_match:
                pos = tag_start + 1
                continue
            
            tag_name = tag_match.group(1).lower()
            
            # 자체 닫힘 태그 또는 단일 태그 확인
            self_closing_match = re.match(r'<[^>]+\s*/>', protected_text[tag_start:])
            single_tags = {'br', 'hr', 'img', 'input', 'meta', 'link', 'area', 'base', 'col', 'embed', 'source', 'track', 'wbr'}
            
            if self_closing_match or tag_name in single_tags:
                # 자체 닫힘 또는 단일 태그
                if self_closing_match:
                    tag_end = tag_start + self_closing_match.end()
                else:
                    # 단일 태그의 > 찾기
                    close_bracket = protected_text.find('>', tag_start)
                    if close_bracket == -1:
                        pos = tag_start + 1
                        continue
                    tag_end = close_bracket + 1
                
                placeholder = f"__HTML_TAG_{block_counter}__"
                html_blocks[placeholder] = protected_text[tag_start:tag_end]
                protected_text = protected_text[:tag_start] + placeholder + protected_text[tag_end:]
                block_counter += 1
                pos = tag_start + len(placeholder)
            else:
                # 쌍 태그 - 매칭되는 닫힌 태그 찾기
                tag_end = self._find_complete_tag(protected_text, tag_start, tag_name)
                if tag_end != -1:
                    placeholder = f"__HTML_TAG_{block_counter}__"
                    html_blocks[placeholder] = protected_text[tag_start:tag_end]
                    protected_text = protected_text[:tag_start] + placeholder + protected_text[tag_end:]
                    block_counter += 1
                    pos = tag_start + len(placeholder)
                else:
                    pos = tag_start + 1
        
        return protected_text, html_blocks
    
    def _find_complete_tag(self, text: str, start_pos: int, tag_name: str) -> int:
        """완전한 태그 블록의 끝 위치를 찾는 함수"""
        # 시작 태그의 끝 찾기
        tag_start_end = text.find('>', start_pos)
        if tag_start_end == -1:
            return -1
        
        pos = tag_start_end + 1
        open_count = 1
        
        while pos < len(text) and open_count > 0:
            # 다음 태그 찾기
            next_tag = text.find('<', pos)
            if next_tag == -1:
                return -1
            
            # 플레이스홀더인지 확인
            if text[next_tag:next_tag+12] == '__HTML_TAG_':
                # 플레이스홀더 건너뛰기
                placeholder_end = text.find('__', next_tag + 12)
                if placeholder_end != -1:
                    pos = placeholder_end + 2
                else:
                    pos = next_tag + 1
                continue
            
            # 태그 타입 확인
            if text[next_tag:next_tag+2] == '</':
                # 닫힌 태그
                close_tag_match = re.match(rf'</{tag_name}>', text[next_tag:], re.IGNORECASE)
                if close_tag_match:
                    open_count -= 1
                    if open_count == 0:
                        return next_tag + close_tag_match.end()
                    pos = next_tag + close_tag_match.end()
                else:
                    pos = next_tag + 1
            else:
                # 열린 태그인지 확인
                open_tag_match = re.match(rf'<{tag_name}[^>]*>', text[next_tag:], re.IGNORECASE)
                if open_tag_match:
                    # 자체 닫힘 태그가 아닌 경우만 카운트 증가
                    if not open_tag_match.group(0).endswith('/>'):
                        open_count += 1
                    pos = next_tag + open_tag_match.end()
                else:
                    pos = next_tag + 1
        
        return -1
    
    def _restore_html_blocks(self, text: str, html_blocks: Dict[str, str]) -> str:
        """플레이스홀더를 원래 HTML 블록으로 복원"""
        result = text
        for placeholder, html_block in html_blocks.items():
            result = result.replace(placeholder, html_block)
        return result
