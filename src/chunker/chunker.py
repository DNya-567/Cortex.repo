from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tree_sitter import Language, Parser
import tree_sitter_javascript as tsjavascript


SUPPORTED_EXTENSIONS = {".js", ".ts", ".jsx", ".tsx"}
TARGET_NODE_TYPES = {
    "function_declaration",
    "arrow_function",
    "class_declaration",
    "method_definition",
}
LANGUAGE_BY_EXTENSION = {
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
}


@dataclass
class CodeChunk:
    chunk_id: str
    file_path: str
    chunk_type: str
    chunk_name: str
    content: str
    start_line: int
    end_line: int
    language: str


_PARSER = Parser()
_PARSER.language = Language(tsjavascript.language())


def _node_text(node, source: bytes) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _name_from_field(node, source: bytes) -> str | None:
    name_node = node.child_by_field_name("name")
    if name_node is None:
        return None
    return _node_text(name_node, source).strip() or None


def _arrow_name(node, source: bytes) -> str:
    parent = node.parent
    if parent is not None:
        if parent.type == "variable_declarator":
            variable_name = _name_from_field(parent, source)
            if variable_name:
                return variable_name
        elif parent.type == "assignment_expression":
            left = parent.child_by_field_name("left")
            if left is not None:
                left_name = _node_text(left, source).strip()
                if left_name:
                    return left_name
        elif parent.type == "pair":
            key = parent.child_by_field_name("key")
            if key is not None:
                key_name = _node_text(key, source).strip()
                if key_name:
                    return key_name

    return f"anonymous_arrow_{node.start_point[0] + 1}"


def _to_chunk(node, source: bytes, file_path: Path) -> CodeChunk:
    extension = file_path.suffix.lower()
    language = LANGUAGE_BY_EXTENSION.get(extension, "javascript")

    if node.type == "function_declaration":
        chunk_type = "function"
        chunk_name = _name_from_field(node, source) or f"anonymous_function_{node.start_point[0] + 1}"
    elif node.type == "arrow_function":
        chunk_type = "arrow_function"
        chunk_name = _arrow_name(node, source)
    elif node.type == "class_declaration":
        chunk_type = "class"
        chunk_name = _name_from_field(node, source) or f"anonymous_class_{node.start_point[0] + 1}"
    else:
        chunk_type = "method"
        chunk_name = _name_from_field(node, source) or f"anonymous_method_{node.start_point[0] + 1}"

    start_line = node.start_point[0] + 1
    end_line = node.end_point[0] + 1
    chunk_id = f"{file_path.as_posix()}:{chunk_type}:{chunk_name}:{start_line}:{end_line}"

    return CodeChunk(
        chunk_id=chunk_id,
        file_path=file_path.as_posix(),
        chunk_type=chunk_type,
        chunk_name=chunk_name,
        content=_node_text(node, source),
        start_line=start_line,
        end_line=end_line,
        language=language,
    )


def _walk_and_collect(node, source: bytes, file_path: Path, chunks: list[CodeChunk]) -> None:
    if node.type in TARGET_NODE_TYPES:
        chunks.append(_to_chunk(node, source, file_path))

    for child in node.children:
        _walk_and_collect(child, source, file_path, chunks)


def chunk_file(file_path: str | Path) -> list[CodeChunk]:
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return []

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return []

    source = path.read_bytes()
    tree = _PARSER.parse(source)

    chunks: list[CodeChunk] = []
    _walk_and_collect(tree.root_node, source, path, chunks)
    return chunks


def chunk_directory(directory: str | Path) -> list[CodeChunk]:
    root = Path(directory)
    if not root.exists() or not root.is_dir():
        return []

    chunks: list[CodeChunk] = []
    stack = [root]

    while stack:
        current = stack.pop()
        if current.name == "node_modules":
            continue

        for entry in current.iterdir():
            if entry.is_dir():
                if entry.name != "node_modules":
                    stack.append(entry)
                continue

            if entry.suffix.lower() in SUPPORTED_EXTENSIONS:
                chunks.extend(chunk_file(entry))

    return chunks


def chunk_file_any(file_path: str) -> list[CodeChunk]:
    """
    Route to correct chunker based on file extension.
    .js .ts .jsx .tsx → chunk_file()
    .py → chunk_python_file()
    everything else → chunk_generic_file()
    """
    from src.chunker.python_chunker import chunk_python_file
    from src.chunker.generic_chunker import chunk_generic_file

    ext = Path(file_path).suffix.lower()
    if ext in {".js", ".ts", ".jsx", ".tsx"}:
        return chunk_file(file_path)
    elif ext == ".py":
        return chunk_python_file(file_path)
    else:
        return chunk_generic_file(file_path)


def chunk_directory_any(directory: str) -> list[CodeChunk]:
    """
    Chunk directory supporting all languages.
    Handles .js .ts .jsx .tsx .py .java .go .rs .c .h
    .cpp .cc .cxx .cs .rb .php .kt .swift
    """
    supported = {
        ".js", ".ts", ".jsx", ".tsx", ".py",
        ".java", ".go", ".rs", ".c", ".h",
        ".cpp", ".cc", ".cxx", ".cs", ".rb",
        ".php", ".kt", ".swift"
    }
    skip_dirs = {"node_modules", ".git", "venv", "__pycache__"}
    all_chunks = []

    for fp in Path(directory).rglob("*"):
        if any(part in fp.parts for part in skip_dirs):
            continue
        if fp.is_file() and fp.suffix.lower() in supported:
            all_chunks.extend(chunk_file_any(str(fp)))

    return all_chunks

