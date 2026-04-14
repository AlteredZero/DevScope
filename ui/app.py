from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QFileDialog, QLabel, QComboBox,
    QTabWidget
)
from PyQt5.QtCore import QObject, pyqtSignal
import threading

AVAILABLE_MODELS = [
    "nvidia/nemotron-3-super-120b-a12b:free",
    "qwen/qwen3-coder:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemma-4-31b-it:free",
    "openai/gpt-oss-120b:free",
    "z-ai/glm-4.5-air:free",
    "openrouter/free",
]


class AIWorker(QObject):
    finished = pyqtSignal(str)
    files_found = pyqtSignal(list)

    def __init__(self, folder, prompt, model):
        super().__init__()
        self.folder = folder
        self.prompt = prompt
        self.model = model

    def run(self):
        from core.detector import detect_project_type
        from core.analyzer import find_relevant_files
        from core.reader import read_specific_files
        from core.ai import ask_ai

        try:
            project_types = detect_project_type(self.folder)
            files = find_relevant_files(self.folder, self.prompt)

            if not files:
                self.finished.emit(
                    "No relevant files found for your request.\n\n"
                    "Tips:\n"
                    "- Mention the file name directly (e.g. 'in main.py')\n"
                    "- Use more specific keywords\n"
                    "- Make sure the project folder is correct"
                )
                return

            self.files_found.emit(files)
            codebase = read_specific_files(files)
            response = ask_ai(self.prompt, codebase, project_types, model=self.model)
            self.finished.emit(response)

        except Exception as e:
            self.finished.emit(f"Unexpected error: {str(e)}")


class DevScopeUi(QWidget):
    def __init__(self):
        super().__init__()
        self.folder = ""
        self.last_response = ""
        self.setWindowTitle("DevScope")
        self._build_ui()

    def _build_ui(self):
        root_layout = QVBoxLayout(self)

        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Model:"))
        self.model_selector = QComboBox()
        for m in AVAILABLE_MODELS:
            self.model_selector.addItem(m)
        model_row.addWidget(self.model_selector)
        root_layout.addLayout(model_row)

        folder_row = QHBoxLayout()
        self.btn_folder = QPushButton("Select Project Folder")
        self.btn_folder.clicked.connect(self.select_folder)
        folder_row.addWidget(self.btn_folder)
        self.folder_label = QLabel("No project selected")
        folder_row.addWidget(self.folder_label)
        root_layout.addLayout(folder_row)

        self.tabs = QTabWidget()
        root_layout.addWidget(self.tabs)

        chat_tab = QWidget()
        chat_layout = QVBoxLayout(chat_tab)

        chat_layout.addWidget(QLabel("Files searched:"))
        self.files_display = QTextEdit()
        self.files_display.setReadOnly(True)
        self.files_display.setMaximumHeight(70)
        chat_layout.addWidget(self.files_display)

        chat_layout.addWidget(QLabel("Your request:"))
        self.input = QTextEdit()
        self.input.setPlaceholderText("Ask something about your code...")
        self.input.setMaximumHeight(100)
        chat_layout.addWidget(self.input)

        btn_row = QHBoxLayout()
        self.btn_ask = QPushButton("Ask AI")
        self.btn_ask.clicked.connect(self.run_ai)
        btn_row.addWidget(self.btn_ask)

        self.btn_apply = QPushButton("Apply Fixes")
        self.btn_apply.clicked.connect(self.apply_fixes)
        self.btn_apply.setEnabled(False)
        btn_row.addWidget(self.btn_apply)
        chat_layout.addLayout(btn_row)

        chat_layout.addWidget(QLabel("AI Response:"))
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        chat_layout.addWidget(self.output)

        chat_layout.addWidget(QLabel("Apply Result:"))
        self.apply_output = QTextEdit()
        self.apply_output.setReadOnly(True)
        self.apply_output.setMaximumHeight(120)
        chat_layout.addWidget(self.apply_output)

        self.tabs.addTab(chat_tab, "Chat")

        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)

        history_btn_row = QHBoxLayout()
        btn_load = QPushButton("Load History")
        btn_load.clicked.connect(self.load_history)
        history_btn_row.addWidget(btn_load)

        btn_clear = QPushButton("Clear History")
        btn_clear.clicked.connect(self.clear_history)
        history_btn_row.addWidget(btn_clear)
        history_layout.addLayout(history_btn_row)

        self.history_display = QTextEdit()
        self.history_display.setReadOnly(True)
        self.history_display.setPlaceholderText("Click 'Load History' to view past exchanges...")
        history_layout.addWidget(self.history_display)

        self.tabs.addTab(history_tab, "History")

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if folder:
            self.folder = folder
            self.folder_label.setText(folder)
            self.files_display.clear()
            self.output.clear()
            self.apply_output.clear()
            self.btn_apply.setEnabled(False)

    def run_ai(self):
        if not self.folder:
            self.output.setText("Select a project folder first.")
            return

        prompt = self.input.toPlainText().strip()
        if not prompt:
            self.output.setText("Please type a request.")
            return

        self.output.setText("Thinking...")
        self.apply_output.clear()
        self.files_display.clear()
        self.btn_ask.setEnabled(False)
        self.btn_apply.setEnabled(False)
        self.last_response = ""

        model = self.model_selector.currentText()
        self.worker = AIWorker(self.folder, prompt, model)
        self.worker.finished.connect(self.display_result)
        self.worker.files_found.connect(self.display_files)
        threading.Thread(target=self.worker.run, daemon=True).start()

    def display_files(self, files):
        self.files_display.setText("\n".join(f"• {f}" for f in files))

    def display_result(self, text):
        self.output.setText(text)
        self.last_response = text
        self.btn_ask.setEnabled(True)

        from core.applier import parse_fixes
        fixes = parse_fixes(text)
        self.btn_apply.setEnabled(len(fixes) > 0)

        try:
            from core.history import save_exchange
            prompt = self.input.toPlainText().strip()
            save_exchange(self.folder, prompt, text)
        except Exception:
            pass

    def apply_fixes(self):
        if not self.last_response:
            return

        from core.applier import parse_fixes, apply_fixes

        fixes = parse_fixes(self.last_response)
        if not fixes:
            self.apply_output.setText("No fixes found in the AI response.")
            return

        result = apply_fixes(fixes, self.folder)
        self.apply_output.setText(result)
        self.btn_apply.setEnabled(False)

    def load_history(self):
        from core.history import load_history, format_history_entry
        entries = load_history()
        if not entries:
            self.history_display.setText("No history saved yet.")
            return
        separator = "\n" + "─" * 60 + "\n"
        self.history_display.setText(
            separator.join(format_history_entry(e) for e in entries)
        )

    def clear_history(self):
        import os
        from core.history import HISTORY_DIR
        history_file = os.path.join(HISTORY_DIR, "history.json")
        if os.path.exists(history_file):
            os.remove(history_file)
        self.history_display.setText("History cleared.")