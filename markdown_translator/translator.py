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
17. DO NOT translate "__OBSIDIAN_LINK_{i}__
18. DO NOT delete any placeholders(__YAML_FRONT_MATTER__, __CODE_BLOCK_{i}__, ...) or special markers
19. DO NOT translate file names, paths, or identifiers in any form (e.g., `file.txt`, `path/to/file`, `variable_name`)
20. 줄바꿈과 공백은 그대로 유지합니다.

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
        max_tokens: int = 1024,
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
        
        # print(f"[START PROTECTOR]\n{protected_text}\n[END PROTECTOR]")

        if self.verbose:
            print(f"텍스트 청킹 시작... {self.max_tokens} 토큰 기준")
        
        # 2. 텍스트 청킹
        chunks = self.chunker.split_text(protected_text)
        
        # print(chunks)
        
        if self.verbose:
            print(f"총 {len(chunks)}개 청크로 분할됨")
        
        # 3. 각 청크 번역
        translated_chunks = []
        for i, chunk in enumerate(chunks):
            token_count = chunk.metadata.get('token_count', 0)
            
            if self.verbose:
                print(f"청크 {i+1}/{len(chunks)} 처리 중... ({token_count} 토큰)")

            # print("청크 내용:") 
            # print(chunk.page_content)
            translated = self._generate_text(chunk.page_content)
            # print("번역 결과:")
            # print(translated)
            translated_chunks.append(translated)
        
        # 4. 번역된 청크들 결합
        translated_text = "\n".join(translated_chunks)
        
        # print(translated_text)
        
        if self.verbose:
            print("마크다운 구조 복원 중...")
        
        # 5. 마크다운 구조 복원
        result = self.protector.restore(translated_text)
        
        # print(result)
        
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
        max_tokens=1024, # 모델에 따라 조정 필요 32b 모델은 현재 비디오 메모리 제한으로 context가 4096 토큰까지 가능하므로 한글 특성상 1/4로 설정 
        temperature=0.1,
        verbose=True
    )
    
    # 텍스트 번역
    markdown_text = r"""
---
created: 2025-06-17T17:22:07 (UTC +09:00)
tags: []
source: https://docling-project.github.io/docling/usage/
author: 
---

# Usage - Docling

> ## Excerpt
> To convert individual PDF documents, use convert(), for example:

---
## Conversion

### Convert a single document

To convert individual PDF documents, use `convert()`, for example:

```python
from docling.document_converter import DocumentConverter

source = "https://arxiv.org/pdf/2408.09869"  # PDF path or URL
converter = DocumentConverter()
result = converter.convert(source)
print(result.document.export_to_markdown())  # output: "### Docling Technical Report[...]"
```

### CLI

You can also use Docling directly from your command line to convert individual files —be it local or by URL— or whole directories.

```
docling https://arxiv.org/pdf/2206.01062
```

You can also use 🥚[SmolDocling](https://huggingface.co/ds4sd/SmolDocling-256M-preview) and other VLMs via Docling CLI:

```
docling --pipeline vlm --vlm-model smoldocling https://arxiv.org/pdf/2206.01062
```

This will use MLX acceleration on supported Apple Silicon hardware.

To see all available options (export formats etc.) run `docling --help`. More details in the [CLI reference page](https://docling-project.github.io/docling/reference/cli/).

### Advanced options

#### Model prefetching and offline usage

By default, models are downloaded automatically upon first usage. If you would prefer to explicitly prefetch them for offline use (e.g. in air-gapped environments) you can do that as follows:

**Step 1: Prefetch the models**

Use the `docling-tools models download` utility:

```
$ docling-tools models download
Downloading layout model...
Downloading tableformer model...
Downloading picture classifier model...
Downloading code formula model...
Downloading easyocr models...
Models downloaded into $HOME/.cache/docling/models.
```

Alternatively, models can be programmatically downloaded using `docling.utils.model_downloader.download_models()`.

**Step 2: Use the prefetched models**

```python
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import EasyOcrOptions, PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

artifacts_path = "/local/path/to/models"

pipeline_options = PdfPipelineOptions(artifacts_path=artifacts_path)
doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)
```

Or using the CLI:

```
docling --artifacts-path="/local/path/to/models" FILE
```

Or using the `DOCLING_ARTIFACTS_PATH` environment variable:

```
export DOCLING_ARTIFACTS_PATH="/local/path/to/models"
python my_docling_script.py
```

#### Using remote services

The main purpose of Docling is to run local models which are not sharing any user data with remote services. Anyhow, there are valid use cases for processing part of the pipeline using remote services, for example invoking OCR engines from cloud vendors or the usage of hosted LLMs.

In Docling we decided to allow such models, but we require the user to explicitly opt-in in communicating with external services.

```python
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

pipeline_options = PdfPipelineOptions(enable_remote_services=True)
doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)
```

When the value `enable_remote_services=True` is not set, the system will raise an exception `OperationNotAllowed()`.

_Note: This option is only related to the system sending user data to remote services. Control of pulling data (e.g. model weights) follows the logic described in [Model prefetching and offline usage](https://docling-project.github.io/docling/usage/#model-prefetching-and-offline-usage)._

##### List of remote model services

The options in this list require the explicit `enable_remote_services=True` when processing the documents.

-   `PictureDescriptionApiOptions`: Using vision models via API calls.

#### Adjust pipeline features

The example file [custom\_convert.py](https://docling-project.github.io/docling/examples/custom_convert/) contains multiple ways one can adjust the conversion pipeline and features.

You can control if table structure recognition should map the recognized structure back to PDF cells (default) or use text cells from the structure prediction itself. This can improve output quality if you find that multiple columns in extracted tables are erroneously merged into one.

```python
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions

pipeline_options = PdfPipelineOptions(do_table_structure=True)
pipeline_options.table_structure_options.do_cell_matching = False  # uses text cells predicted from table structure model

doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)
```

Since docling 1.16.0: You can control which TableFormer mode you want to use. Choose between `TableFormerMode.FAST` (faster but less accurate) and `TableFormerMode.ACCURATE` (default) to receive better quality with difficult table structures.

```python
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode

pipeline_options = PdfPipelineOptions(do_table_structure=True)
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE  # use more accurate TableFormer model

doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)
```

#### Impose limits on the document size

You can limit the file size and number of pages which should be allowed to process per document:

```python
from pathlib import Path
from docling.document_converter import DocumentConverter

source = "https://arxiv.org/pdf/2408.09869"
converter = DocumentConverter()
result = converter.convert(source, max_num_pages=100, max_file_size=20971520)
```

#### Convert from binary PDF streams

You can convert PDFs from a binary stream instead of from the filesystem as follows:

```python
from io import BytesIO
from docling.datamodel.base_models import DocumentStream
from docling.document_converter import DocumentConverter

buf = BytesIO(your_binary_stream)
source = DocumentStream(name="my_doc.pdf", stream=buf)
converter = DocumentConverter()
result = converter.convert(source)
```

#### Limit resource usage

You can limit the CPU threads used by Docling by setting the environment variable `OMP_NUM_THREADS` accordingly. The default setting is using 4 CPU threads.

#### Use specific backend converters

Note

This section discusses directly invoking a [backend](https://docling-project.github.io/docling/concepts/architecture/), i.e. using a low-level API. This should only be done when necessary. For most cases, using a `DocumentConverter` (high-level API) as discussed in the sections above should suffice — and is the recommended way.

By default, Docling will try to identify the document format to apply the appropriate conversion backend (see the list of [supported formats](https://docling-project.github.io/docling/usage/supported_formats/)). You can restrict the `DocumentConverter` to a set of allowed document formats, as shown in the [Multi-format conversion](https://docling-project.github.io/docling/examples/run_with_formats/) example. Alternatively, you can also use the specific backend that matches your document content. For instance, you can use `HTMLDocumentBackend` for HTML pages:

```python
import urllib.request
from io import BytesIO
from docling.backend.html_backend import HTMLDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import InputDocument

url = "https://en.wikipedia.org/wiki/Duck"
text = urllib.request.urlopen(url).read()
in_doc = InputDocument(
    path_or_stream=BytesIO(text),
    format=InputFormat.HTML,
    backend=HTMLDocumentBackend,
    filename="duck.html",
)
backend = HTMLDocumentBackend(in_doc=in_doc, path_or_stream=BytesIO(text))
dl_doc = backend.convert()
print(dl_doc.export_to_markdown())
```

## Chunking

You can chunk a Docling document using a [chunker](https://docling-project.github.io/docling/concepts/chunking/), such as a `HybridChunker`, as shown below (for more details check out [this example](https://docling-project.github.io/docling/examples/hybrid_chunking/)):

```python
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker

conv_res = DocumentConverter().convert("https://arxiv.org/pdf/2206.01062")
doc = conv_res.document

chunker = HybridChunker(tokenizer="BAAI/bge-small-en-v1.5")  # set tokenizer as needed
chunk_iter = chunker.chunk(doc)
```

An example chunk would look like this:

```python
print(list(chunk_iter)[11])
# {
#   "text": "In this paper, we present the DocLayNet dataset. [...]",
#   "meta": {
#     "doc_items": [{
#       "self_ref": "#/texts/28",
#       "label": "text",
#       "prov": [{
#         "page_no": 2,
#         "bbox": {"l": 53.29, "t": 287.14, "r": 295.56, "b": 212.37, ...},
#       }], ...,
#     }, ...],
#     "headings": ["1 INTRODUCTION"],
#   }
# }
```
    """
    
    # 번역 수행
    translated = translator.translate(markdown_text)
    print("번역 결과:")
    print(translated[:500])
    
    # 통계 정보
    stats = translator.get_translation_stats(markdown_text)
    print(f"번역 통계: {stats}")
    

    # 파일 번역
    # input = "tests/Usage - Docling.md"
    # output = "tests/Usage - Docling_ko.md"
    # translator.translate_file(input, output)
