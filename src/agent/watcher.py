from __future__ import annotations
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.indexer import index_directory
from src.graph.import_resolver import build_graph

class CodeChangeHandler(FileSystemEventHandler):
    def __init__(self, directory: str):
        self.directory = directory
        self.last_event_time = {}
        self.debounce_delay = 2.0

    def on_modified(self, event):
        if event.is_directory:
            return
        if not self._is_code_file(event.src_path):
            return
        self._handle_change(event.src_path)

    def on_created(self, event):
        if event.is_directory:
            return
        if not self._is_code_file(event.src_path):
            return
        self._handle_change(event.src_path)

    def _is_code_file(self, path: str) -> bool:
        return path.endswith(('.js', '.ts', '.jsx', '.tsx'))

    def _handle_change(self, path: str):
        now = time.time()
        last_time = self.last_event_time.get(path, 0)
        if now - last_time < self.debounce_delay:
            return
        self.last_event_time[path] = now
        print(f"Change detected: {path}")
        try:
            index_directory(self.directory)
            build_graph(self.directory)
            print(f"Re-indexed {self.directory}")
        except Exception as e:
            print(f"Error re-indexing: {e}")

def start_watcher(directory: str = "test-codebase") -> None:
    handler = CodeChangeHandler(directory)
    observer = Observer()
    observer.schedule(handler, directory, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

