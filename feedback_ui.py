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
    QFrame, QTextBrowser
)
from PySide6.QtCore import Qt, Signal, QObject, QTimer, QSettings
from PySide6.QtGui import QTextCursor, QIcon, QKeyEvent, QPalette, QColor, QFont, QClipboard
import markdown
from markdown.extensions import codehilite, fenced_code, tables, toc

class FeedbackResult(TypedDict):
    cursor_usage_opt: str

def get_apple_dark_palette(app: QApplication):
    """Apple风格深色主题调色板，更加精致的Apple设计"""
    darkPalette = app.palette()

    # 主要背景色 - Apple深色风格，更加柔和
    darkPalette.setColor(QPalette.Window, QColor(28, 28, 30))  # #1c1c1e 更深的背景
    darkPalette.setColor(QPalette.WindowText, QColor(255, 255, 255))  # 纯白文字

    # 输入框和文本区域 - 更有层次感
    darkPalette.setColor(QPalette.Base, QColor(44, 44, 46))  # #2c2c2e 输入框背景
    darkPalette.setColor(QPalette.AlternateBase, QColor(58, 58, 60))  # #3a3a3c 交替背景
    darkPalette.setColor(QPalette.Text, QColor(255, 255, 255))  # 纯白文字
    darkPalette.setColor(QPalette.PlaceholderText, QColor(142, 142, 147))  # #8e8e93 占位符

    # 按钮 - Apple风格圆角按钮色彩
    darkPalette.setColor(QPalette.Button, QColor(72, 72, 74))  # #48484a 按钮背景
    darkPalette.setColor(QPalette.ButtonText, QColor(255, 255, 255))  # 纯白按钮文字

    # 高亮和选择 - Apple蓝色系统色
    darkPalette.setColor(QPalette.Highlight, QColor(10, 132, 255))  # #0a84ff Apple蓝
    darkPalette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))  # 纯白高亮文字

    # 链接 - Apple蓝色
    darkPalette.setColor(QPalette.Link, QColor(0, 122, 255))  # #007AFF
    darkPalette.setColor(QPalette.LinkVisited, QColor(88, 86, 214))  # #5856D6

    # 工具提示
    darkPalette.setColor(QPalette.ToolTipBase, QColor(29, 29, 31))
    darkPalette.setColor(QPalette.ToolTipText, QColor(245, 245, 247))

    # 阴影和边框
    darkPalette.setColor(QPalette.Dark, QColor(0, 0, 0))
    darkPalette.setColor(QPalette.Shadow, QColor(0, 0, 0))

    # 禁用状态
    darkPalette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(152, 152, 157))
    darkPalette.setColor(QPalette.Disabled, QPalette.Text, QColor(152, 152, 157))
    darkPalette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(152, 152, 157))
    darkPalette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(44, 44, 46))
    darkPalette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(152, 152, 157))

    return darkPalette

class FeedbackTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Apple风格的文本编辑器样式 - 增大字体以提高可读性
        self.setStyleSheet("""
            QTextEdit {
                background-color: #2c2c2e;
                border: 1px solid #3a3a3c;
                border-radius: 8px;
                padding: 12px;
                font-family: "Microsoft YaHei", "PingFang SC", "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
                font-size: 22px;
                line-height: 1.5;
                color: #ffffff;
                selection-background-color: #0a84ff;
            }
            QTextEdit:focus {
                border: 2px solid #0a84ff;
                background-color: #2c2c2e;
            }
            QScrollBar:vertical {
                background-color: transparent;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(255, 255, 255, 0.5);
            }
        """)

        # 设置Apple风格的字体 - 大幅增大字体以提高可读性，优先中文字体
        font = QFont()
        font.setPointSize(24)  # 大幅增大字体大小
        font.setFamily("Microsoft YaHei, PingFang SC, SF Pro Text, Helvetica Neue, Arial, sans-serif")
        font.setWeight(QFont.Normal)
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
        self.setup_markdown()

        self.setWindowTitle("💬 AI 反馈助手")

        # 设置窗口属性 - Apple风格
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)  # 禁用透明背景以获得更好的性能

        # 设置窗口大小和位置
        self.setMinimumSize(600, 500)
        self.resize(700, 600)

        self.settings = QSettings("InteractiveFeedbackMCP", "InteractiveFeedbackMCP")

        # 设置Apple风格字体 - 大幅增大字体以提高可读性，优先中文字体
        app_font = QFont()
        app_font.setPointSize(24)  # 进一步增大字体大小
        app_font.setFamily("Microsoft YaHei, PingFang SC, SF Pro Display, SF Pro Text, Helvetica Neue, Arial, sans-serif")
        app_font.setWeight(QFont.Normal)
        app_font.setLetterSpacing(QFont.PercentageSpacing, 97.8)  # Apple的字母间距
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

    def setup_markdown(self):
        """设置Markdown渲染器"""
        self.md = markdown.Markdown(
            extensions=[
                'fenced_code',
                'codehilite',
                'tables',
                'toc',
                'nl2br',
                'sane_lists'
            ],
            extension_configs={
                'codehilite': {
                    'css_class': 'highlight',
                    'use_pygments': True,
                    'noclasses': True,
                    'pygments_style': 'monokai'
                }
            }
        )

    def render_markdown(self, text: str) -> str:
        """渲染Markdown文本为HTML，优化代码块显示"""
        if not text:
            return ""

        # 转换Markdown为HTML
        html_content = self.md.convert(text)

        # 包装在样式化的HTML中，优化代码块显示
        styled_html = f"""
        <style>
            body {{
                font-family: "Microsoft YaHei", "PingFang SC", "SF Pro Display", "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
                color: #f5f5f7;
                line-height: 1.6;
                letter-spacing: -0.022em;
                font-size: 22px;
                margin: 0;
                padding: 0;
            }}
            h1, h2, h3, h4, h5, h6 {{
                color: #ffffff;
                font-weight: 600;
                margin: 1em 0 0.5em 0;
            }}
            p {{
                margin: 0.8em 0;
                line-height: 1.6;
            }}
            code {{
                background-color: #2c2c2e;
                color: #ff6b6b;
                padding: 2px 6px;
                border-radius: 4px;
                font-family: "SF Mono", "Monaco", "Consolas", "Liberation Mono", "Courier New", monospace;
                font-size: 20px;
                font-weight: 500;
            }}
            pre {{
                background-color: #1c1c1e;
                border: 1px solid #3a3a3c;
                border-radius: 8px;
                padding: 16px;
                margin: 1em 0;
                overflow-x: auto;
                font-family: "SF Mono", "Monaco", "Consolas", "Liberation Mono", "Courier New", monospace;
                font-size: 18px;
                line-height: 1.4;
            }}
            pre code {{
                background-color: transparent;
                color: inherit;
                padding: 0;
                border-radius: 0;
                font-size: inherit;
            }}
            ul, ol {{
                margin: 0.8em 0;
                padding-left: 2em;
            }}
            li {{
                margin: 0.4em 0;
                line-height: 1.5;
            }}
            blockquote {{
                border-left: 3px solid #0a84ff;
                margin: 1em 0;
                padding-left: 1em;
                color: #d1d1d6;
                font-style: italic;
            }}
            strong {{
                color: #ffffff;
                font-weight: 600;
            }}
            em {{
                color: #d1d1d6;
                font-style: italic;
            }}
        }}
        </style>
        <body>{html_content}</body>
        """

        return styled_html

    def _create_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 设置Apple风格的主布局
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)  # Apple风格的边距
        layout.setSpacing(16)  # Apple风格的间距

        # 设置窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1c1c1e;
            }
            QGroupBox {
                font-family: "Microsoft YaHei", "PingFang SC", "SF Pro Display", "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
                font-size: 22px;
                font-weight: 600;
                color: #ffffff;
                border: 1px solid #3a3a3c;
                border-radius: 12px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: rgba(44, 44, 46, 0.6);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                color: #ffffff;
                background-color: transparent;
            }
        """)

        # Feedback section - Apple风格的卡片设计
        self.feedback_group = QGroupBox("💬 反馈内容")
        feedback_layout = QVBoxLayout(self.feedback_group)
        feedback_layout.setContentsMargins(16, 20, 16, 16)
        feedback_layout.setSpacing(12)

        # Description browser (from self.prompt) - Apple风格的文本浏览器
        self.description_browser = QTextBrowser()
        self.description_browser.setMinimumHeight(150)  # 设置最小高度
        self.description_browser.setMaximumHeight(300)  # 增加最大高度，允许更多内容显示
        self.description_browser.setOpenExternalLinks(True)

        # Apple风格的文本浏览器样式
        self.description_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #2c2c2e;
                border: 1px solid #3a3a3c;
                border-radius: 8px;
                padding: 12px;
                font-family: "Microsoft YaHei", "PingFang SC", "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
                font-size: 16px;
                line-height: 1.4;
                color: #ffffff;
                selection-background-color: #0a84ff;
            }
            QScrollBar:vertical {
                background-color: transparent;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(255, 255, 255, 0.5);
            }
        """)

        # 设置描述浏览器的字体 - 大幅增大字体以提高可读性，优先中文字体
        desc_font = QFont()
        desc_font.setPointSize(22)  # 大幅增大字体大小
        desc_font.setFamily("Microsoft YaHei, PingFang SC, SF Pro Text, Helvetica Neue, Arial, sans-serif")
        desc_font.setWeight(QFont.Normal)
        self.description_browser.setFont(desc_font)

        # 渲染Markdown内容
        if self.prompt:
            html_content = self.render_markdown(self.prompt)
            self.description_browser.setHtml(html_content)
        else:
            self.description_browser.setPlainText("无提示内容")

        feedback_layout.addWidget(self.description_browser)

        # Apple风格的预定义选项
        self.option_checkboxes = []
        if self.predefined_options and len(self.predefined_options) > 0:
            options_frame = QFrame()
            options_layout = QVBoxLayout(options_frame)
            options_layout.setContentsMargins(0, 12, 0, 12)
            options_layout.setSpacing(8)

            # Apple风格的复选框样式
            checkbox_style = """
                QCheckBox {
                    font-family: "Microsoft YaHei", "PingFang SC", "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
                    font-size: 22px;
                    color: #ffffff;
                    spacing: 8px;
                    padding: 4px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border-radius: 4px;
                    border: 2px solid #3a3a3c;
                    background-color: transparent;
                }
                QCheckBox::indicator:hover {
                    border-color: #0a84ff;
                }
                QCheckBox::indicator:checked {
                    background-color: #0a84ff;
                    border-color: #0a84ff;
                    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xMC42IDEuNEw0LjMgNy43TDEuNCA0LjgiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
                }
                QCheckBox::indicator:checked:hover {
                    background-color: #0071e3;
                    border-color: #0071e3;
                }
            """

            for option in self.predefined_options:
                checkbox = QCheckBox(option)
                checkbox.setStyleSheet(checkbox_style)

                # 设置Apple风格字体 - 大幅增大字体以提高可读性，优先中文字体
                checkbox_font = QFont()
                checkbox_font.setPointSize(22)  # 大幅增大字体大小
                checkbox_font.setFamily("Microsoft YaHei, PingFang SC, SF Pro Text, Helvetica Neue, Arial, sans-serif")
                checkbox_font.setWeight(QFont.Normal)
                checkbox.setFont(checkbox_font)

                self.option_checkboxes.append(checkbox)
                options_layout.addWidget(checkbox)

            feedback_layout.addWidget(options_frame)

            # Apple风格的分隔线
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setStyleSheet("""
                QFrame {
                    color: #3a3a3c;
                    background-color: #3a3a3c;
                    border: none;
                    height: 1px;
                    margin: 8px 0;
                }
            """)
            feedback_layout.addWidget(separator)

        # Free-form text feedback - 增大文本编辑区域
        self.feedback_text = FeedbackTextEdit()
        font_metrics = self.feedback_text.fontMetrics()
        row_height = font_metrics.height()
        # 增加行数以适应更大字体，提供更好的编辑体验
        padding = self.feedback_text.contentsMargins().top() + self.feedback_text.contentsMargins().bottom() + 20
        self.feedback_text.setMinimumHeight(8 * row_height + padding)  # 增加到8行

        # 设置占位符文本，使用更大的字体
        self.feedback_text.setPlaceholderText("请在此输入您的反馈内容... (Ctrl+Enter 提交)")

        # Apple风格的按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)  # Apple风格的按钮间距

        # Apple风格的按钮样式
        button_style = """
            QPushButton {
                background-color: #0a84ff;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-family: "Microsoft YaHei", "PingFang SC", "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
                font-size: 20px;
                font-weight: 600;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #0071e3;
            }
            QPushButton:pressed {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #3a3a3c;
                color: #8e8e93;
            }
        """

        secondary_button_style = """
            QPushButton {
                background-color: #48484a;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-family: "Microsoft YaHei", "PingFang SC", "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
                font-size: 20px;
                font-weight: 500;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #5a5a5c;
            }
            QPushButton:pressed {
                background-color: #3a3a3c;
            }
        """

        # 插入代码按钮 - 次要按钮样式
        insert_code_button = QPushButton("📋 插入代码")
        insert_code_button.setStyleSheet(secondary_button_style)
        insert_code_button.clicked.connect(self._insert_code_from_clipboard)
        insert_code_button.setShortcut("Alt+C")

        # 发送按钮 - 主要按钮样式
        submit_button = QPushButton("🚀 发送反馈")
        submit_button.setStyleSheet(button_style)
        submit_button.clicked.connect(self._submit_feedback)
        submit_button.setShortcut("Ctrl+Return")
        submit_button.setDefault(True)  # 设为默认按钮

        # 添加按钮到布局
        button_layout.addStretch()  # 左侧弹性空间
        button_layout.addWidget(insert_code_button)
        button_layout.addWidget(submit_button)

        feedback_layout.addWidget(self.feedback_text)
        feedback_layout.addLayout(button_layout)

        # Set minimum height for feedback_group
        self.feedback_group.setMinimumHeight(self.description_browser.maximumHeight() + self.feedback_text.minimumHeight() + button_layout.sizeHint().height() + feedback_layout.spacing() * 2 + feedback_layout.contentsMargins().top() + feedback_layout.contentsMargins().bottom() + 10)

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

            # 构建要插入的代码块，在```前面总是添加换行
            code_block = f"\n```\n{clipboard_text}\n```"

            # 如果是在文本开头插入，则不需要前面的换行
            if cursor.position() == 0:
                code_block = f"```\n{clipboard_text}\n```"

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

    app.setPalette(get_apple_dark_palette(app))
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
