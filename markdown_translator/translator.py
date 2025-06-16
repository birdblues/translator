from .protector import MarkdownProtector
from .chunker import AdaptiveMarkdownChunker
import requests
from typing import Optional, List


class MarkdownTranslator:
    """
    마크다운 문서를 한국어로 번역하는 클래스
    - 마크다운 구조와 포맷팅을 보존하면서 번역
    - 청킹을 통한 대용량 문서 처리
    - Ollama API를 통한 로컬 LLM 활용
    """
    
    DEFAULT_SYSTEM_PROMPT = """You are a professional Korean translator specializing in technical documentation. Your task is to translate markdown content while preserving all formatting and maintaining consistent tone and style.

TRANSLATION TONE & STYLE:
- Use consistent formal polite tone (합니다/습니다 체) throughout
- Maintain professional but accessible language suitable for technical tutorials
- Use natural Korean expressions, avoiding direct word-by-word translation
- Keep the same level of formality as Korean technical documentation

FORMATTING RULES:
1. Keep ALL markdown formatting symbols (*, **, #, ##, ###, -, `, ```, etc.) exactly as they are
2. DO NOT translate content inside code blocks (```...``` or `...`)
3. DO NOT translate code comments or inline code (e.g., `code()`)
4. DO NOT translate URLs, file paths, or technical identifiers
5. DO NOT translate programming language names, function names, or variable names
6. Keep the exact same structure and formatting
7. Only translate natural language text content
8. Preserve line breaks and spacing exactly
9. Always preserve inline math formulas in $...$ format and math blocks in $$...$$ format.
10. DO NOT translate publication notation lines with (...)= format.
11. DO NOT translate "__YAML_FRONT_MATTER__"
12. DO NOT translate "__CODE_BLOCK_{i}__"
13. DO NOT translate "__INDENT_BLOCK_{i}__"
14. DO NOT translate "__MATH_BLOCK_{i}__"
15. DO NOT translate "__TABLE_BLOCK_{i}__"
16. DO NOT translate "__HTML_TAG_{i}__"
17. DO NOT translate any placeholders or special markers
18. DO NOT translate file names, paths, or identifiers in any form (e.g., `file.txt`, `path/to/file`, `variable_name`)
19. 줄바꿈과 공백은 그대로 유지합니다.

CONSISTENCY RULES:
- Maintain consistent terminology throughout the document
- Use the same Korean terms for repeated English technical terms
- Follow the translation style established in previous sections

TONE EXAMPLES:
- "Let's check this out" → "이를 확인해보겠습니다" (not "확인해 보죠")
- "Great!" → "훌륭합니다!" (not "좋아요!")
- "You can see..." → "다음과 같이 확인할 수 있습니다" (not "볼 수 있어요")"""

    def __init__(
        self,
        model: str = "qwen3:32b",
        api_url: str = "http://localhost:11434/api/generate",
        max_tokens: int = 2048,
        temperature: float = 0.1,
        system_prompt: Optional[str] = None,
        verbose: bool = True
    ):
        """
        번역기 초기화
        
        Args:
            model: 사용할 LLM 모델명
            api_url: Ollama API URL
            max_tokens: 청크당 최대 토큰 수
            temperature: 번역 창의성 수준 (0.0-1.0)
            system_prompt: 커스텀 시스템 프롬프트 (None이면 기본값 사용)
            verbose: 진행 상황 출력 여부
        """
        self.model = model
        self.api_url = api_url
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.system_prompt = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        self.verbose = verbose
        
        # 의존성 객체들 초기화
        self.protector = MarkdownProtector()
        self.chunker = AdaptiveMarkdownChunker(max_tokens=max_tokens)
    
    def translate(self, text: str) -> str:
        """
        마크다운 텍스트를 한국어로 번역
        
        Args:
            text: 번역할 마크다운 텍스트
            
        Returns:
            번역된 마크다운 텍스트
        """
        if self.verbose:
            print("마크다운 보호 시작...")
        
        # 1. 마크다운 구조 보호
        protected_text = self.protector.protect(text)
        
        if self.verbose:
            print("텍스트 청킹 시작...")
        
        # 2. 텍스트 청킹
        chunks = self.chunker.split_text(protected_text)
        
        if self.verbose:
            print(f"총 {len(chunks)}개 청크로 분할됨")
        
        # 3. 각 청크 번역
        translated_chunks = []
        for i, chunk in enumerate(chunks):
            token_count = chunk.metadata.get('token_count', 0)
            
            if self.verbose:
                print(f"청크 {i+1}/{len(chunks)} 처리 중... ({token_count} 토큰)")
            
            translated = self._generate_text(chunk.page_content)
            translated_chunks.append(translated)
        
        # 4. 번역된 청크들 결합
        translated_text = "\n".join(translated_chunks)
        
        if self.verbose:
            print("마크다운 구조 복원 중...")
        
        # 5. 마크다운 구조 복원
        result = self.protector.restore(translated_text)
        
        if self.verbose:
            print("번역 완료!")
        
        return result
    
    def _generate_text(self, prompt: str) -> str:
        """
        LLM을 사용한 텍스트 생성
        
        Args:
            prompt: 번역할 텍스트
            
        Returns:
            번역된 텍스트
        """
        data = {
            "model": self.model,
            "temperature": self.temperature,
            "think": False,  # 생각 모드 비활성화
            "system": self.system_prompt,
            "prompt": prompt,
            "stream": False  # 스트리밍 비활성화
        }
        
        try:
            response = requests.post(self.api_url, json=data)
            
            if response.status_code == 200:
                result = response.json()
                return result['response']
            else:
                error_msg = f"API Error: {response.status_code}"
                if self.verbose:
                    print(error_msg)
                return f"Error: {response.status_code}"
                
        except requests.RequestException as e:
            error_msg = f"Request Error: {str(e)}"
            if self.verbose:
                print(error_msg)
            return f"Error: {str(e)}"
    
    def translate_file(self, input_path: str, output_path: str) -> bool:
        """
        파일을 읽어서 번역 후 저장
        
        Args:
            input_path: 입력 파일 경로
            output_path: 출력 파일 경로
            
        Returns:
            성공 여부
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            translated = self.translate(content)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(translated)
            
            if self.verbose:
                print(f"번역 완료: {input_path} → {output_path}")
            
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"파일 처리 오류: {str(e)}")
            return False
    
    def get_translation_stats(self, text: str) -> dict:
        """
        번역 작업에 대한 통계 정보 반환
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            통계 정보 딕셔너리
        """
        protected_text = self.protector.protect(text)
        chunks = self.chunker.split_text(protected_text)
        stats = self.chunker.get_chunk_stats(chunks)
        
        return {
            "original_length": len(text),
            "protected_length": len(protected_text),
            "total_chunks": stats["total_chunks"],
            "total_tokens": stats["total_tokens"],
            "avg_tokens_per_chunk": stats["avg_tokens_per_chunk"],
            "estimated_api_calls": len(chunks)
        }


# 사용 예시
if __name__ == "__main__":
    # 번역기 생성
    translator = MarkdownTranslator(
        model="qwen3:32b",
        max_tokens=2048,
        temperature=0.1,
        verbose=True
    )
    
    # 텍스트 번역
    markdown_text = """
    # Hello World
    This is a sample markdown document.
    
    ## Code Example
    ```python
    def hello():
        print("Hello, World!")
    ```
    """
    
    # 번역 수행
    translated = translator.translate(markdown_text)
    print("번역 결과:")
    print(translated)
    
    # 통계 정보
    stats = translator.get_translation_stats(markdown_text)
    print(f"번역 통계: {stats}")
    
    # 파일 번역
    # translator.translate_file("input.md", "output_ko.md")
