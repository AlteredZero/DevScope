from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QFileDialog, QLabel, QComboBox,
    QTabWidget, QCheckBox, QSlider, QSpinBox,
    QLineEdit
)
from PyQt5.QtCore import QObject, pyqtSignal, Qt
import threading
import markdown

AVAILABLE_MODELS = [
    "nvidia/nemotron-3-super-120b-a12b:free",
    "qwen/qwen3-coder:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemma-4-31b-it:free",
    "openai/gpt-oss-120b:free",
    "z-ai/glm-4.5-air:free",
    "openrouter/free",
]

THEMES = {
    "Scope - Default": """
        * { font-family: 'JetBrains Mono'; }
        QWidget { background-color: #0f1117; color: #c9d1d9; }
        QTabWidget::pane { border: 1px solid #21262d; }
        QTabBar::tab { background: #161b22; color: #8b949e; padding: 6px 16px; border: 1px solid #21262d; }
        QTabBar::tab:selected { background: #0f1117; color: #58a6ff; border-bottom: 2px solid #58a6ff; }
        QPushButton { background-color: #21262d; color: #c9d1d9; border: 1px solid #30363d; border-radius: 6px; padding: 5px 12px; }
        QPushButton:hover { background-color: #30363d; border-color: #58a6ff; }
        QPushButton:disabled { color: #484f58; background-color: #161b22; }
        QTextEdit, QLineEdit { background-color: #161b22; border: 1px solid #21262d; color: #c9d1d9; border-radius: 4px; padding: 4px; }
        QComboBox { background-color: #21262d; border: 1px solid #30363d; color: #c9d1d9; border-radius: 4px; padding: 4px; }
        QComboBox::drop-down { border: none; }
        QComboBox QAbstractItemView { background-color: #161b22; color: #c9d1d9; selection-background-color: #21262d; }
        QSpinBox { background-color: #21262d; border: 1px solid #30363d; color: #c9d1d9; border-radius: 4px; padding: 4px; }
        QSlider::groove:horizontal { background: #21262d; height: 4px; border-radius: 2px; }
        QSlider::handle:horizontal { background: #58a6ff; width: 14px; height: 14px; border-radius: 7px; margin: -5px 0; }
        QLabel { color: #8b949e; }
        QCheckBox { color: #c9d1d9; }
        QScrollBar:vertical { background: #161b22; width: 8px; }
        QScrollBar::handle:vertical { background: #30363d; border-radius: 4px; }
    """,
    "Dark": """
        * { font-family: 'JetBrains Mono'; }
        QWidget { background-color: #1e1e1e; color: #d4d4d4; }
        QTabWidget::pane { border: 1px solid #3c3c3c; }
        QTabBar::tab { background: #2d2d2d; color: #969696; padding: 6px 16px; }
        QTabBar::tab:selected { background: #1e1e1e; color: #ffffff; border-bottom: 2px solid #007acc; }
        QPushButton { background-color: #2d2d2d; color: #d4d4d4; border: 1px solid #3c3c3c; border-radius: 4px; padding: 5px 12px; }
        QPushButton:hover { background-color: #3c3c3c; }
        QPushButton:disabled { color: #555555; }
        QTextEdit, QLineEdit { background-color: #252526; border: 1px solid #3c3c3c; color: #d4d4d4; padding: 4px; }
        QComboBox { background-color: #2d2d2d; border: 1px solid #3c3c3c; color: #d4d4d4; padding: 4px; }
        QComboBox QAbstractItemView { background-color: #252526; color: #d4d4d4; }
        QSpinBox { background-color: #2d2d2d; border: 1px solid #3c3c3c; color: #d4d4d4; padding: 4px; }
        QSlider::groove:horizontal { background: #3c3c3c; height: 4px; }
        QSlider::handle:horizontal { background: #007acc; width: 14px; height: 14px; border-radius: 7px; margin: -5px 0; }
        QLabel { color: #969696; }
        QCheckBox { color: #d4d4d4; }
    """,
    "Light": """
        * { font-family: 'JetBrains Mono'; }
        QWidget { background-color: #ffffff; color: #24292e; }
        QTabWidget::pane { border: 1px solid #e1e4e8; }
        QTabBar::tab { background: #f6f8fa; color: #586069; padding: 6px 16px; border: 1px solid #e1e4e8; }
        QTabBar::tab:selected { background: #ffffff; color: #0366d6; border-bottom: 2px solid #0366d6; }
        QPushButton { background-color: #f6f8fa; color: #24292e; border: 1px solid #e1e4e8; border-radius: 6px; padding: 5px 12px; }
        QPushButton:hover { background-color: #e1e4e8; }
        QPushButton:disabled { color: #959da5; }
        QTextEdit, QLineEdit { background-color: #ffffff; border: 1px solid #e1e4e8; color: #24292e; padding: 4px; }
        QComboBox { background-color: #f6f8fa; border: 1px solid #e1e4e8; color: #24292e; padding: 4px; }
        QComboBox QAbstractItemView { background-color: #ffffff; color: #24292e; }
        QSpinBox { background-color: #f6f8fa; border: 1px solid #e1e4e8; color: #24292e; padding: 4px; }
        QSlider::groove:horizontal { background: #e1e4e8; height: 4px; }
        QSlider::handle:horizontal { background: #0366d6; width: 14px; height: 14px; border-radius: 7px; margin: -5px 0; }
        QLabel { color: #586069; }
        QCheckBox { color: #24292e; }
    """,
    "None": "",
}

MODE_DEFAULT = ["Edit", "Ask"]

DEFAULTS = {
    "theme": "Scope - Default",
    "model": AVAILABLE_MODELS[0],
    "temperature": 10,
    "max_tokens": 500,
    "auto_fallback": True,
    "mode": "Edit",
    "max_files": 10,
    "file_types": ".py, .js, .ts, .jsx, .tsx, .cpp, .h, .hpp, .c, .cs, .java, .go, .rs, .html, .css, .json, .yaml, .yml, .xml, .lua, .rb, .php, .swift, .kt, .sh, .bat, .ps1, .sql, .ini, .cfg, .toml, .env, .md",
    "ignore_folders": "",
    "font_size": 9,
}


class AIWorker(QObject):
    finished = pyqtSignal(str)
    files_found = pyqtSignal(list)

    def __init__(self, folder, prompt, model, temperature, max_tokens, auto_fallback):
        super().__init__()
        self.folder = folder
        self.prompt = prompt
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.auto_fallback = auto_fallback

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
            response = ask_ai(
                self.prompt, codebase, project_types,
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                auto_fallback=self.auto_fallback,
            )
            self.finished.emit(response)

        except Exception as e:
            self.finished.emit(f"Unexpected error: {str(e)}")


class DevScopeUi(QWidget):
    def __init__(self):
        super().__init__()
        self.folder = ""
        self.last_response = ""
        self.font_size = DEFAULTS["font_size"]
        self.setWindowTitle("DevScope")
        self._build_ui()
        self.apply_theme(DEFAULTS["theme"])

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

        def add_row(label, widget):
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            row.addWidget(widget)
            settings_layout.addLayout(row)

        self.theme_selector = QComboBox()
        for t in THEMES:
            self.theme_selector.addItem(t)
        self.theme_selector.currentTextChanged.connect(self.apply_theme)
        add_row("Theme:", self.theme_selector)

        self.default_model_selector = QComboBox()
        for m in AVAILABLE_MODELS:
            self.default_model_selector.addItem(m)
        self.default_model_selector.currentTextChanged.connect(
            lambda m: self.model_selector.setCurrentText(m)
        )
        add_row("Default Model:", self.default_model_selector)

        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setRange(0, 100)
        self.temp_slider.setValue(DEFAULTS["temperature"])
        self.temp_label = QLabel(f"{DEFAULTS['temperature'] / 100:.2f}")
        self.temp_slider.valueChanged.connect(
            lambda v: self.temp_label.setText(f"{v / 100:.2f}")
        )
        temp_row = QHBoxLayout()
        temp_row.addWidget(QLabel("Temperature:"))
        temp_row.addWidget(self.temp_slider)
        temp_row.addWidget(self.temp_label)
        settings_layout.addLayout(temp_row)

        self.max_tokens = QSpinBox()
        self.max_tokens.setRange(100, 4000)
        self.max_tokens.setValue(DEFAULTS["max_tokens"])
        add_row("Max Response Length:", self.max_tokens)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(DEFAULTS["auto_fallback"])
        add_row("Auto-Fallback:", self.checkbox)

        self.default_mode_selector = QComboBox()
        for m in MODE_DEFAULT:
            self.default_mode_selector.addItem(m)
        add_row("Mode Default:", self.default_mode_selector)

        self.max_files = QSpinBox()
        self.max_files.setRange(1, 100)
        self.max_files.setValue(DEFAULTS["max_files"])
        add_row("Max Files to Scan:", self.max_files)

        self.file_types = QLineEdit()
        self.file_types.setText(DEFAULTS["file_types"])
        self.file_types.setPlaceholderText("e.g: .py, .js, .cpp, .cs")
        add_row("File Types to Include:", self.file_types)

        self.ignored_files = QLineEdit()
        self.ignored_files.setPlaceholderText("node_modules, build, dist")
        add_row("Ignore Folders:", self.ignored_files)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 32)
        self.font_size_spin.setValue(DEFAULTS["font_size"])
        self.font_size_spin.valueChanged.connect(self.change_font)
        add_row("Font Size:", self.font_size_spin)

        reset_row = QHBoxLayout()
        self.button_reset = QPushButton("Reset Defaults")
        self.button_reset.clicked.connect(self.reset_default_settings)
        reset_row.addWidget(self.button_reset)
        settings_layout.addLayout(reset_row)

        settings_layout.addStretch(1)

        self.settings_display = QLabel("© 2026 Daniil Ovechkin. Built using Python and PyQt5.")
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
        temperature = self.temp_slider.value() / 100.0
        max_tokens = self.max_tokens.value()
        auto_fallback = self.checkbox.isChecked()

        self.worker = AIWorker(self.folder, prompt, model, temperature, max_tokens, auto_fallback)
        self.worker.finished.connect(self.display_result)
        self.worker.files_found.connect(self.display_files)
        threading.Thread(target=self.worker.run, daemon=True).start()

    def display_files(self, files):
        self.files_display.setText("\n".join(f"• {f}" for f in files))

    def display_result(self, text):
        self.output.setHtml(self.markdown_to_html(text))
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

    def apply_theme(self, theme_name):
        stylesheet = THEMES.get(theme_name, "")
        font_rule = f"* {{ font-size: {self.font_size}pt; }}"
        self.setStyleSheet(stylesheet + font_rule)

    def change_font(self, size):
        self.font_size = size
        current_theme = self.theme_selector.currentText()
        self.apply_theme(current_theme)

    def reset_default_settings(self):
        self.theme_selector.setCurrentText(DEFAULTS["theme"])
        self.default_model_selector.setCurrentText(DEFAULTS["model"])
        self.model_selector.setCurrentText(DEFAULTS["model"])
        self.temp_slider.setValue(DEFAULTS["temperature"])
        self.max_tokens.setValue(DEFAULTS["max_tokens"])
        self.checkbox.setChecked(DEFAULTS["auto_fallback"])
        self.default_mode_selector.setCurrentIndex(0)
        self.max_files.setValue(DEFAULTS["max_files"])
        self.file_types.setText(DEFAULTS["file_types"])
        self.ignored_files.setText(DEFAULTS["ignore_folders"])
        self.font_size_spin.setValue(DEFAULTS["font_size"])

    def markdown_to_html(self, text):
        return markdown.markdown(text, extensions=["fenced_code", "tables"])