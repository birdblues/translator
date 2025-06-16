from langchain.text_splitter import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter
)
import tiktoken
from typing import List, Optional
from langchain.schema import Document


class AdaptiveMarkdownChunker:
    """
    적응형 마크다운 청킹 클래스
    - 헤더 기반 분할 후 토큰 수에 따라 병합/분할
    """
    
    def __init__(
        self, 
        max_tokens: int = 1000,
        encoding_name: str = "cl100k_base",
        chunk_overlap: int = 0
    ):
        """
        Args:
            max_tokens: 최대 토큰 수
            encoding_name: tiktoken 인코딩 이름 (GPT-3.5/4 호환)
            chunk_overlap: 청크 간 겹침 토큰 수
        """
        self.max_tokens = max_tokens
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding(encoding_name)
        
        # 마크다운 헤더 분할 설정
        self.headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
            ("####", "Header 4"),
            ("#####", "Header 5"),
            ("######", "Header 6"),
        ]
        
        # 마크다운 헤더 분할기 초기화
        self.markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on,
            return_each_line=True,
            strip_headers=False
        )
        
        # 재귀적 텍스트 분할기 초기화
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.max_tokens * 3,  # 문자 기준 근사치
            chunk_overlap=self.chunk_overlap,
            length_function=self.count_tokens
        )
    
    def count_tokens(self, text: str) -> int:
        """텍스트의 토큰 수 계산"""
        return len(self.encoding.encode(text))
    
    def split_text(self, markdown_text: str) -> List[Document]:
        """
        적응형 마크다운 청킹 수행
        
        Args:
            markdown_text: 분할할 마크다운 텍스트
            
        Returns:
            분할된 Document 객체들의 리스트
        """
        # 1. 헤더 기반 초기 분할
        header_chunks = self.markdown_splitter.split_text(markdown_text)
        
        # 2. 적응적 처리
        final_chunks = []
        accumulator = None  # 병합용 임시 저장소
        
        for chunk in header_chunks:
            token_count = self.count_tokens(chunk.page_content)
            
            if accumulator is None:
                accumulator = chunk
                accumulator_tokens = token_count
            else:
                # 이전 청크와 병합 시도
                merged_content = accumulator.page_content + "\n\n" + chunk.page_content
                merged_tokens = self.count_tokens(merged_content)
                
                if merged_tokens <= self.max_tokens:
                    # 병합 가능: 계속 누적
                    accumulator.page_content = merged_content
                    accumulator.metadata.update(chunk.metadata)
                    accumulator_tokens = merged_tokens
                else:
                    # 병합 불가: 이전 청크 처리 후 새로 시작
                    final_chunks.extend(self._process_chunk(accumulator))
                    accumulator = chunk
                    accumulator_tokens = token_count
        
        # 마지막 누적 청크 처리
        if accumulator:
            final_chunks.extend(self._process_chunk(accumulator))
        
        return final_chunks
    
    def _process_chunk(self, chunk: Document) -> List[Document]:
        """
        개별 청크 처리: 분할 또는 그대로 반환
        
        Args:
            chunk: 처리할 Document 객체
            
        Returns:
            처리된 Document 객체들의 리스트
        """
        token_count = self.count_tokens(chunk.page_content)
        
        if token_count <= self.max_tokens:
            # 적정 크기: 그대로 반환
            chunk.metadata["token_count"] = token_count
            return [chunk]
        else:
            # 너무 큰 경우: 재귀적 분할
            split_chunks = self.text_splitter.split_documents([chunk])
            
            # 각 분할된 청크에 토큰 수 메타데이터 추가
            for split_chunk in split_chunks:
                split_chunk.metadata["token_count"] = self.count_tokens(split_chunk.page_content)
            
            return split_chunks
    
    def get_chunk_stats(self, chunks: List[Document]) -> dict:
        """
        청킹 결과 통계 반환
        
        Args:
            chunks: 분할된 청크들
            
        Returns:
            통계 정보 딕셔너리
        """
        token_counts = [chunk.metadata.get("token_count", 0) for chunk in chunks]
        
        return {
            "total_chunks": len(chunks),
            "total_tokens": sum(token_counts),
            "avg_tokens_per_chunk": sum(token_counts) / len(chunks) if chunks else 0,
            "max_tokens": max(token_counts) if token_counts else 0,
            "chunks_over_limit": sum(1 for count in token_counts if count > self.max_tokens)
        }


# 사용 예시
if __name__ == "__main__":
    # 청킹 객체 생성
    chunker = AdaptiveMarkdownChunker(
        max_tokens=1000,
        chunk_overlap=0
    )
    
    # 마크다운 텍스트 분할
    markdown_content = """
    # 제목 1
    이것은 첫 번째 섹션입니다.
    
    ## 부제목 1.1
    더 많은 내용이 여기에 있습니다.
    
    ### 소제목 1.1.1
    세부 내용입니다.
    """
    
    chunks = chunker.split_text(markdown_content)
    
    # 결과 출력
    for i, chunk in enumerate(chunks):
        print(f"청크 {i+1}:")
        print(f"토큰 수: {chunk.metadata.get('token_count', 'Unknown')}")
        print(f"내용: {chunk.page_content[:100]}...")
        print(f"메타데이터: {chunk.metadata}")
        print("-" * 50)
    
    # 통계 정보
    stats = chunker.get_chunk_stats(chunks)
    print(f"청킹 통계: {stats}")
