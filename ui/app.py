from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QFileDialog, QLabel, QComboBox,
    QTabWidget, QCheckBox, QSlider, QSpinBox,
    QLineEdit
)
from PyQt5.QtCore import QObject, pyqtSignal, Qt  
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

THEMES = [
    "Scope - Default",
    "Dark",
    "Light",
    "None",
]

MODE_DEFAULT = [
    "Ask",
    "Edit"
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
        self.setStyleSheet("* { font-family: 'JetBrains Mono'; font-size: 9pt; }")
        root_layout = QVBoxLayout(self)

        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Model:"))
        self.model_selector = QComboBox()
        for m in AVAILABLE_MODELS:
            self.model_selector.addItem(m)
        model_row.addWidget(self.model_selector)
        root_layout.addLayout(model_row)

        folder_row = QHBoxLayout()
        self.button_folder = QPushButton("Select Project Folder")
        self.button_folder.clicked.connect(self.select_folder)
        folder_row.addWidget(self.button_folder)
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

        button_row = QHBoxLayout()
        self.button_ask = QPushButton("Ask AI")
        self.button_ask.clicked.connect(self.run_ai)
        button_row.addWidget(self.button_ask)

        self.button_apply = QPushButton("Apply Fixes")
        self.button_apply.clicked.connect(self.apply_fixes)
        self.button_apply.setEnabled(False)
        button_row.addWidget(self.button_apply)
        chat_layout.addLayout(button_row)

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

        history_button_row = QHBoxLayout()
        button_load = QPushButton("Load History")
        button_load.clicked.connect(self.load_history)
        history_button_row.addWidget(button_load)

        button_clear = QPushButton("Clear History")
        button_clear.clicked.connect(self.clear_history)
        history_button_row.addWidget(button_clear)
        history_layout.addLayout(history_button_row)

        self.history_display = QTextEdit()
        self.history_display.setReadOnly(True)
        self.history_display.setPlaceholderText("Click 'Load History' to view past exchanges...")
        history_layout.addWidget(self.history_display)

        self.tabs.addTab(history_tab, "History")

        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)

        settings_button_row = QHBoxLayout()
        lbl_title = QLabel("Theme:")
        settings_button_row.addWidget(lbl_title)
        self.theme_selector = QComboBox()
        for t in THEMES:
            self.theme_selector.addItem(t)
        settings_button_row.addWidget(self.theme_selector)
        settings_layout.addLayout(settings_button_row)

        settings_button_row = QHBoxLayout()
        lbl_title = QLabel("Default Model:")
        settings_button_row.addWidget(lbl_title)
        self.default_model_selector = QComboBox()
        for t in AVAILABLE_MODELS:
            self.default_model_selector.addItem(t)
        settings_button_row.addWidget(self.default_model_selector)
        settings_layout.addLayout(settings_button_row)

        settings_button_row = QHBoxLayout()
        lbl_title = QLabel("Temperature:")
        settings_button_row.addWidget(lbl_title)
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setRange(0, 100)
        self.temp_slider.setValue(10)
        settings_button_row.addWidget(self.temp_slider)
        settings_layout.addLayout(settings_button_row)

        settings_button_row = QHBoxLayout()
        lbl_title = QLabel("Max Response Length:")
        settings_button_row.addWidget(lbl_title)
        self.max_tokens = QSpinBox()
        self.max_tokens.setRange(100, 4000)
        self.max_tokens.setValue(500)
        settings_button_row.addWidget(self.max_tokens)
        settings_layout.addLayout(settings_button_row)

        settings_button_row = QHBoxLayout()
        lbl_title = QLabel("Auto-Fallback Toggle:")
        settings_button_row.addWidget(lbl_title)
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(True)
        #self.checkbox.stateChanged.connect()
        settings_button_row.addWidget(self.checkbox)
        settings_layout.addLayout(settings_button_row)

        settings_button_row = QHBoxLayout()
        lbl_title = QLabel("Mode Default:")
        settings_button_row.addWidget(lbl_title)
        self.default_mode_selector = QComboBox()
        for m in MODE_DEFAULT:
            self.default_mode_selector.addItem(m)
        settings_button_row.addWidget(self.default_mode_selector)
        settings_layout.addLayout(settings_button_row)

        settings_button_row = QHBoxLayout()
        lbl_title = QLabel("Max Files to Scan:")
        settings_button_row.addWidget(lbl_title)
        self.max_files = QSpinBox()
        self.max_files.setRange(1, 100)
        self.max_files.setValue(10)
        settings_button_row.addWidget(self.max_files)
        settings_layout.addLayout(settings_button_row)

        settings_button_row = QHBoxLayout()
        lbl_title = QLabel("File Types to Include:")
        settings_button_row.addWidget(lbl_title)
        self.file_types = QLineEdit()
        self.file_types.setText(
            ".py, .js, .ts, .jsx, .tsx, "
            ".cpp, .h, .hpp, .c, "
            ".cs, .java, .go, .rs, "
            ".html, .css, "
            ".json, .yaml, .yml, .xml, "
            ".lua, .rb, .php, .swift, .kt, "
            ".sh, .bat, .ps1, "
            ".sql, .ini, .cfg, .toml, .env, "
            ".md"
        )
        self.file_types.placeholderText = "e.g: .py, .js, .cpp, .cs"
        settings_button_row.addWidget(self.file_types)
        settings_layout.addLayout(settings_button_row)
        
        settings_button_row = QHBoxLayout()
        lbl_title = QLabel("Ignore Folders:")
        settings_button_row.addWidget(lbl_title)
        self.ignored_files = QLineEdit()
        self.ignored_files.placeholderText = "node_modules, build, dist"
        settings_button_row.addWidget(self.ignored_files)
        settings_layout.addLayout(settings_button_row)

        settings_button_row = QHBoxLayout()
        lbl_title = QLabel("Font Size:")
        settings_button_row.addWidget(lbl_title)
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 32)
        settings_button_row.addWidget(self.font_size)
        settings_layout.addLayout(settings_button_row)

        settings_button_row = QHBoxLayout()
        self.button_reset = QPushButton("Reset Default")
        #self.button_reset.clicked.connect()
        settings_button_row.addWidget(self.button_reset)
        settings_layout.addLayout(settings_button_row)

        settings_layout.addStretch(1)

        self.settings_display = QLabel()
        self.settings_display.setText("© 2026 Daniil Ovechkin. Built using Python and PyQt5.")
        self.settings_display.setAlignment(Qt.AlignCenter)
        settings_layout.addWidget(self.settings_display)


        self.tabs.addTab(settings_tab, "Settings")

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if folder:
            self.folder = folder
            self.folder_label.setText(folder)
            self.files_display.clear()
            self.output.clear()
            self.apply_output.clear()
            self.button_apply.setEnabled(False)

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
        self.button_ask.setEnabled(False)
        self.button_apply.setEnabled(False)
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
        self.button_ask.setEnabled(True)

        from core.applier import parse_fixes
        fixes = parse_fixes(text)
        self.button_apply.setEnabled(len(fixes) > 0)

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
        self.button_apply.setEnabled(False)

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