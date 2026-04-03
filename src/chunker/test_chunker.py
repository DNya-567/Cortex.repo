from pathlib import Path

from chunker import chunk_directory


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    target_directory = project_root / "test-codebase"

    chunks = chunk_directory(target_directory)

    for chunk in chunks:
        preview = " ".join(chunk.content.split())[:60]
        print(
            f"{chunk.chunk_name} | {chunk.file_path} | "
            f"{chunk.start_line}-{chunk.end_line} | {preview}"
        )

    print(f"Total chunks: {len(chunks)}")


if __name__ == "__main__":
    main()

