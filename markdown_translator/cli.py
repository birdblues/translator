import os
import argparse
from pathlib import Path
from .formatter import MarkdownFormatter
from .translator import MarkdownTranslator

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs='+', type=str, help="번역할 파일들")
    args = parser.parse_args()

    for file_path in args.files:
        path = Path(file_path)
        if path.exists():
            # 각 파일 처리
            print(f"번역 시작: {file_path}")
            original = path.read_text()
            formatted = MarkdownFormatter().format(original)
            # formatted = original
            translated = MarkdownTranslator().translate(formatted)
            output = path.with_stem(path.stem + '_ko')
            output.write_text(translated)
            print(f"처리 완료: {output}")
        else:
            print(f"파일을 찾을 수 없습니다: {file_path}")

if __name__ == "__main__":
    main()