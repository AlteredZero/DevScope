from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QFileDialog, QLabel, QComboBox
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
    "openrouter/free", # fallback
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
        self.setWindowTitle("DevScope")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Model:"))
        self.model_selector = QComboBox()
        for m in AVAILABLE_MODELS:
            self.model_selector.addItem(m)
        model_row.addWidget(self.model_selector)
        layout.addLayout(model_row)

        folder_row = QHBoxLayout()
        self.btn_folder = QPushButton("Select Project Folder")
        self.btn_folder.clicked.connect(self.select_folder)
        folder_row.addWidget(self.btn_folder)
        self.folder_label = QLabel("No project selected")
        folder_row.addWidget(self.folder_label)
        layout.addLayout(folder_row)

        layout.addWidget(QLabel("Files searched:"))
        self.files_display = QTextEdit()
        self.files_display.setReadOnly(True)
        self.files_display.setMaximumHeight(80)
        layout.addWidget(self.files_display)

        layout.addWidget(QLabel("Your request:"))
        self.input = QTextEdit()
        self.input.setPlaceholderText("Ask something about your code...")
        layout.addWidget(self.input)

        self.btn_ask = QPushButton("Ask AI")
        self.btn_ask.clicked.connect(self.run_ai)
        layout.addWidget(self.btn_ask)

        layout.addWidget(QLabel("AI Response:"))
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if folder:
            self.folder = folder
            self.folder_label.setText(folder)
            self.files_display.clear()
            self.output.clear()

    def run_ai(self):
        if not self.folder:
            self.output.setText("Select a project folder first.")
            return

        prompt = self.input.toPlainText().strip()
        if not prompt:
            self.output.setText("Please type a request.")
            return

        self.output.setText("Thinking...")
        self.files_display.clear()
        self.btn_ask.setEnabled(False)

        model = self.model_selector.currentText()
        self.worker = AIWorker(self.folder, prompt, model)
        self.worker.finished.connect(self.display_result)
        self.worker.files_found.connect(self.display_files)
        threading.Thread(target=self.worker.run, daemon=True).start()

    def display_files(self, files):
        self.files_display.setText("\n".join(f"• {f}" for f in files))

    def display_result(self, text):
        self.output.setText(text)
        self.btn_ask.setEnabled(True)