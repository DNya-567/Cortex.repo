from __future__ import annotations

import ast
from pathlib import Path

from src.chunker.chunker import CodeChunk


def chunk_python_file(file_path: str) -> list[CodeChunk]:
    """
    Parse a Python file and extract functions, classes, and methods as chunks.
    Uses Python's built-in ast module.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        tree = ast.parse(source_code)
    except Exception:
        return []

    chunks = []
    lines = source_code.split("\n")

    class ChunkVisitor(ast.NodeVisitor):
        def __init__(self):
            self.class_stack = []

        def visit_ClassDef(self, node):
            # ← emit the class chunk itself first
            start_line = node.lineno
            end_line = node.end_lineno or node.lineno
            content = "\n".join(lines[start_line - 1: end_line])
            chunk_id = f"{file_path}::{node.name}::{start_line}"
            chunks.append(CodeChunk(
                chunk_id=chunk_id,
                file_path=file_path,
                chunk_type="class",
                chunk_name=node.name,
                content=content,
                start_line=start_line,
                end_line=end_line,
                language="python",
            ))

            # then visit children (methods) with class on the stack
            self.class_stack.append(node.name)
            self.generic_visit(node)
            self.class_stack.pop()

        def visit_FunctionDef(self, node):
            self._process_function(node)
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node):
            self._process_function(node)
            self.generic_visit(node)

        def _process_function(self, node):
            start_line = node.lineno
            end_line = node.end_lineno or node.lineno
            chunk_type = "method" if self.class_stack else "function"
            content = "\n".join(lines[start_line - 1: end_line])
            chunk_id = f"{file_path}::{node.name}::{start_line}"
            chunks.append(CodeChunk(
                chunk_id=chunk_id,
                file_path=file_path,
                chunk_type=chunk_type,
                chunk_name=node.name,
                content=content,
                start_line=start_line,
                end_line=end_line,
                language="python",
            ))

    visitor = ChunkVisitor()
    visitor.visit(tree)

    return chunks