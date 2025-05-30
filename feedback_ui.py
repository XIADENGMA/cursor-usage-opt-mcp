# Interactive Feedback MCP UI
# Developed by Fábio Ferreira (https://x.com/fabiomlferreira)
# Inspired by/related to dotcursorrules.com (https://dotcursorrules.com/)
# Enhanced by Pau Oliva (https://x.com/pof) with ideas from https://github.com/ttommyth/interactive-mcp
import os
import sys
import json
import argparse
from typing import Optional, TypedDict, List

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QTextEdit, QGroupBox,
    QFrame
)
from PySide6.QtCore import Qt, Signal, QObject, QTimer, QSettings
from PySide6.QtGui import QTextCursor, QIcon, QKeyEvent, QPalette, QColor, QFont, QClipboard

class FeedbackResult(TypedDict):
    cursor_usage_opt: str

def get_dark_mode_palette(app: QApplication):
    darkPalette = app.palette()
    darkPalette.setColor(QPalette.Window, QColor(53, 53, 53))
    darkPalette.setColor(QPalette.WindowText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.Base, QColor(42, 42, 42))
    darkPalette.setColor(QPalette.AlternateBase, QColor(66, 66, 66))
    darkPalette.setColor(QPalette.ToolTipBase, QColor(53, 53, 53))
    darkPalette.setColor(QPalette.ToolTipText, Qt.white)
    darkPalette.setColor(QPalette.Text, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.Dark, QColor(35, 35, 35))
    darkPalette.setColor(QPalette.Shadow, QColor(20, 20, 20))
    darkPalette.setColor(QPalette.Button, QColor(53, 53, 53))
    darkPalette.setColor(QPalette.ButtonText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.BrightText, Qt.red)
    darkPalette.setColor(QPalette.Link, QColor(42, 130, 218))
    darkPalette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    darkPalette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80))
    darkPalette.setColor(QPalette.HighlightedText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.PlaceholderText, QColor(127, 127, 127))
    return darkPalette

class FeedbackTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置更大的字体以支持中文输入
        font = QFont()
        font.setPointSize(16)  # 进一步增大字体大小
        font.setFamily("Microsoft YaHei, SimHei, Arial Unicode MS, sans-serif")  # 支持中文字体
        self.setFont(font)

        # 确保支持中文输入法
        self.setAttribute(Qt.WA_InputMethodEnabled, True)
        self.setAcceptRichText(False)  # 只接受纯文本，避免输入法问题

        # 设置输入法属性 - 更全面的中文输入支持
        self.setInputMethodHints(
            Qt.ImhMultiLine |
            Qt.ImhPreferLowercase |
            Qt.ImhNoPredictiveText |
            Qt.ImhSensitiveData
        )

        # 确保焦点策略支持输入法
        self.setFocusPolicy(Qt.StrongFocus)

        # 强制激活输入法
        self.activateInputMethod()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
            # Find the parent FeedbackUI instance and call submit
            parent = self.parent()
            while parent and not isinstance(parent, FeedbackUI):
                parent = parent.parent()
            if parent:
                parent._submit_feedback()
        else:
            super().keyPressEvent(event)

    def focusInEvent(self, event):
        # 确保获得焦点时输入法可用
        super().focusInEvent(event)
        self.setAttribute(Qt.WA_InputMethodEnabled, True)
        # 重新激活输入法
        self.activateInputMethod()

    def activateInputMethod(self):
        """强制激活输入法"""
        try:
            app = QApplication.instance()
            if app and app.inputMethod():
                app.inputMethod().show()
                app.inputMethod().setVisible(True)
        except Exception:
            pass  # 忽略输入法激活错误

class FeedbackUI(QMainWindow):
    def __init__(self, prompt: str, predefined_options: Optional[List[str]] = None):
        super().__init__()
        self.prompt = prompt
        self.predefined_options = predefined_options or []

        self.feedback_result = None

        self.setWindowTitle("Cursor继续对话")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "images", "feedback.png")
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self.settings = QSettings("InteractiveFeedbackMCP", "InteractiveFeedbackMCP")

        # 设置应用程序字体
        app_font = QFont()
        app_font.setPointSize(14)  # 进一步增大整体界面字体
        app_font.setFamily("Microsoft YaHei, SimHei, Arial Unicode MS, sans-serif")
        QApplication.instance().setFont(app_font)

        # Load general UI settings for the main window (geometry, state)
        self.settings.beginGroup("MainWindow_General")
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(900, 700)  # 增大默认窗口大小
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - 900) // 2
            y = (screen.height() - 700) // 2
            self.move(x, y)
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)
        self.settings.endGroup() # End "MainWindow_General" group

        self._create_ui()

    def _create_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Feedback section
        self.feedback_group = QGroupBox("反馈内容")
        feedback_layout = QVBoxLayout(self.feedback_group)

        # Description label (from self.prompt) - Support multiline
        self.description_label = QLabel(self.prompt)
        self.description_label.setWordWrap(True)
        # 设置描述标签的字体
        desc_font = QFont()
        desc_font.setPointSize(15)  # 增大描述标签字体
        desc_font.setFamily("Microsoft YaHei, SimHei, Arial Unicode MS, sans-serif")
        self.description_label.setFont(desc_font)
        feedback_layout.addWidget(self.description_label)

        # Add predefined options if any
        self.option_checkboxes = []
        if self.predefined_options and len(self.predefined_options) > 0:
            options_frame = QFrame()
            options_layout = QVBoxLayout(options_frame)
            options_layout.setContentsMargins(0, 10, 0, 10)

            for option in self.predefined_options:
                checkbox = QCheckBox(option)
                # 设置复选框字体
                checkbox_font = QFont()
                checkbox_font.setPointSize(14)  # 增大复选框字体
                checkbox_font.setFamily("Microsoft YaHei, SimHei, Arial Unicode MS, sans-serif")
                checkbox.setFont(checkbox_font)
                self.option_checkboxes.append(checkbox)
                options_layout.addWidget(checkbox)

            feedback_layout.addWidget(options_frame)

            # Add a separator
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            feedback_layout.addWidget(separator)

        # Free-form text feedback
        self.feedback_text = FeedbackTextEdit()
        font_metrics = self.feedback_text.fontMetrics()
        row_height = font_metrics.height()
        # Calculate height for 7 lines + some padding for margins (进一步增加行数以适应更大字体)
        padding = self.feedback_text.contentsMargins().top() + self.feedback_text.contentsMargins().bottom() + 15
        self.feedback_text.setMinimumHeight(7 * row_height + padding)

        self.feedback_text.setPlaceholderText("请在此输入您的反馈 (Ctrl+Enter 提交)")

        # 创建按钮布局
        button_layout = QHBoxLayout()

        # 插入代码按钮
        insert_code_button = QPushButton("插入代码(&C)")
        # 设置按钮字体
        button_font = QFont()
        button_font.setPointSize(14)  # 增大按钮字体
        button_font.setFamily("Microsoft YaHei, SimHei, Arial Unicode MS, sans-serif")
        insert_code_button.setFont(button_font)
        insert_code_button.clicked.connect(self._insert_code_from_clipboard)

        submit_button = QPushButton("再次发送请求(&S)")
        # 设置按钮字体
        submit_button.setFont(button_font)
        submit_button.clicked.connect(self._submit_feedback)

        # 添加按钮到布局
        button_layout.addWidget(insert_code_button)
        button_layout.addWidget(submit_button)

        feedback_layout.addWidget(self.feedback_text)
        feedback_layout.addLayout(button_layout)

        # Set minimum height for feedback_group
        self.feedback_group.setMinimumHeight(self.description_label.sizeHint().height() + self.feedback_text.minimumHeight() + button_layout.sizeHint().height() + feedback_layout.spacing() * 2 + feedback_layout.contentsMargins().top() + feedback_layout.contentsMargins().bottom() + 10)

        # Add widgets
        layout.addWidget(self.feedback_group)

    def _insert_code_from_clipboard(self):
        """从剪贴板获取内容并插入为代码块格式"""
        clipboard = QApplication.clipboard()
        clipboard_text = clipboard.text()

        if clipboard_text:
            # 获取当前光标位置
            cursor = self.feedback_text.textCursor()
            current_text = self.feedback_text.toPlainText()

            # 构建要插入的代码块
            code_block = f"```\n{clipboard_text}\n```"

            # 如果光标不在文本末尾且当前行不为空，先添加换行
            if cursor.position() < len(current_text) and current_text:
                # 检查光标前面是否有内容，如果有且不是换行符，则添加换行
                if cursor.position() > 0 and not current_text[cursor.position()-1:cursor.position()] == '\n':
                    code_block = '\n' + code_block

            # 插入代码块
            cursor.insertText(code_block)

            # 将光标移动到代码块末尾
            cursor.movePosition(QTextCursor.End)
            self.feedback_text.setTextCursor(cursor)

            # 聚焦到文本框
            self.feedback_text.setFocus()

    def _submit_feedback(self):
        feedback_text = self.feedback_text.toPlainText().strip()
        selected_options = []

        # Get selected predefined options if any
        if self.option_checkboxes:
            for i, checkbox in enumerate(self.option_checkboxes):
                if checkbox.isChecked():
                    selected_options.append(self.predefined_options[i])

        # Combine selected options and feedback text
        final_feedback_parts = []

        # Add selected options
        if selected_options:
            final_feedback_parts.append("; ".join(selected_options))

        # Add user's text feedback
        if feedback_text:
            final_feedback_parts.append(feedback_text)

        # Join with a newline if both parts exist
        final_feedback = "\n\n".join(final_feedback_parts)

        self.feedback_result = FeedbackResult(
            cursor_usage_opt=final_feedback,
        )
        self.close()

    def closeEvent(self, event):
        # Save general UI settings for the main window (geometry, state)
        self.settings.beginGroup("MainWindow_General")
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.endGroup()

        super().closeEvent(event)

    def run(self) -> FeedbackResult:
        self.show()
        QApplication.instance().exec()

        if not self.feedback_result:
            return FeedbackResult(cursor_usage_opt="")

        return self.feedback_result

def feedback_ui(prompt: str, predefined_options: Optional[List[str]] = None, output_file: Optional[str] = None) -> Optional[FeedbackResult]:
    # 设置环境变量以支持Wayland下的中文输入法
    # 强制设置中文输入法环境变量
    if os.environ.get('WAYLAND_DISPLAY'):
        # Wayland 环境
        os.environ['QT_IM_MODULE'] = 'wayland'
        os.environ['XMODIFIERS'] = '@im=fcitx5'
        os.environ['GTK_IM_MODULE'] = 'fcitx5'
        os.environ['QT_QPA_PLATFORM'] = 'wayland'
    else:
        # X11 环境
        os.environ['QT_IM_MODULE'] = 'fcitx5'
        os.environ['XMODIFIERS'] = '@im=fcitx5'
        os.environ['GTK_IM_MODULE'] = 'fcitx5'
        os.environ['QT_QPA_PLATFORM'] = 'xcb'

    # 强制设置locale
    os.environ['LANG'] = 'zh_CN.UTF-8'
    os.environ['LC_ALL'] = 'zh_CN.UTF-8'
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'

    app = QApplication.instance() or QApplication()

    # 确保应用程序支持输入法
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # 强制启用输入法
    app.inputMethod().reset()

    app.setPalette(get_dark_mode_palette(app))
    app.setStyle("Fusion")
    ui = FeedbackUI(prompt, predefined_options)
    result = ui.run()

    if output_file and result:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
        # Save the result to the output file
        with open(output_file, "w", encoding='utf-8') as f:  # 添加utf-8编码支持
            json.dump(result, f, ensure_ascii=False, indent=2)  # 确保中文字符正确保存
        return None

    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="运行反馈界面")
    parser.add_argument("--prompt", default="我已经实现了您请求的更改。", help="向用户显示的提示信息")
    parser.add_argument("--predefined-options", default="", help="预定义选项列表，用|||分隔")
    parser.add_argument("--output-file", help="将反馈结果保存为JSON文件的路径")
    args = parser.parse_args()

    predefined_options = [opt for opt in args.predefined_options.split("|||") if opt] if args.predefined_options else None

    result = feedback_ui(args.prompt, predefined_options, args.output_file)
    if result:
        print(f"\n收到反馈:\n{result['cursor_usage_opt']}")
    sys.exit(0)
