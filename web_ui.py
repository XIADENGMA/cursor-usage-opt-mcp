# Web UI for Interactive Feedback MCP
# Enhanced version supporting both GUI and Web modes for SSH remote usage
import os
import json
import threading
import time
import tempfile
from typing import Optional, List, Dict
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import markdown
from markdown.extensions import codehilite, fenced_code, tables, toc

class WebFeedbackUI:
    def __init__(self, prompt: str, predefined_options: Optional[List[str]] = None,
                 host: str = "0.0.0.0", port: int = 8080, persistent: bool = False):
        self.prompt = prompt
        self.predefined_options = predefined_options or []
        self.host = host
        self.port = port
        self.persistent = persistent  # 是否持续运行模式
        self.feedback_result = None
        self.current_prompt = prompt if prompt else ""  # 当前显示的提示
        self.current_options = predefined_options or []  # 当前选项
        self.has_content = bool(prompt)  # 是否有有效内容
        self.initial_empty = not bool(prompt)  # 标记是否初始就为空
        self.app = Flask(__name__)
        CORS(self.app)
        self.setup_markdown()
        self.setup_routes()

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
        """渲染Markdown文本为HTML"""
        if not text:
            return ""
        return self.md.convert(text)

    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template_string(self.get_html_template())

        @self.app.route('/api/config')
        def get_config():
            return jsonify({
                'prompt': self.current_prompt,
                'prompt_html': self.render_markdown(self.current_prompt) if self.has_content else "",
                'predefined_options': self.current_options,
                'persistent': self.persistent,
                'has_content': self.has_content,
                'initial_empty': self.initial_empty
            })

        @self.app.route('/api/close', methods=['POST'])
        def close_interface():
            """关闭界面的API端点"""
            if not self.persistent:
                threading.Timer(0.5, self.shutdown_server).start()
                return jsonify({'status': 'success', 'message': '界面即将关闭'})
            return jsonify({'status': 'error', 'message': '持续模式下无法关闭'})

        @self.app.route('/api/submit', methods=['POST'])
        def submit_feedback():
            data = request.json
            feedback_text = data.get('feedback_text', '').strip()
            selected_options = data.get('selected_options', [])

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

            self.feedback_result = {
                'cursor_usage_opt': final_feedback
            }

            # 如果不是持续模式，关闭服务器
            if not self.persistent:
                threading.Timer(1.0, self.shutdown_server).start()
                return jsonify({'status': 'success', 'message': '反馈已提交，服务器即将关闭'})
            else:
                # 持续模式下，清空内容并等待下一次调用
                self.current_prompt = ""
                self.current_options = []
                self.has_content = False
                return jsonify({
                    'status': 'success',
                    'message': '反馈已提交',
                    'persistent': True,
                    'clear_content': True
                })

        @self.app.route('/api/update', methods=['POST'])
        def update_content():
            """更新页面内容（仅在持续模式下可用）"""
            if not self.persistent:
                return jsonify({'error': '非持续模式下不支持更新'}), 400

            data = request.json
            new_prompt = data.get('prompt', '')
            new_options = data.get('predefined_options', [])

            # 更新内容
            self.current_prompt = new_prompt
            self.current_options = new_options if new_options is not None else []
            self.has_content = bool(new_prompt)

            return jsonify({
                'status': 'success',
                'message': '内容已更新',
                'prompt': self.current_prompt,
                'prompt_html': self.render_markdown(self.current_prompt) if self.has_content else "",
                'predefined_options': self.current_options,
                'has_content': self.has_content
            })

    def shutdown_server(self):
        """Gracefully shutdown the Flask server"""
        import signal
        os.kill(os.getpid(), signal.SIGINT)

    def get_html_template(self):
        return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cursor继续对话 - Web版</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", "Microsoft YaHei", "PingFang SC", Arial, sans-serif;
            background: #000000;
            background-image:
                radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.15) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(120, 119, 198, 0.1) 0%, transparent 50%);
            color: #f5f5f7;
            min-height: 100vh;
            padding: 0;
            line-height: 1.47059;
            font-weight: 400;
            letter-spacing: -0.022em;
            overflow-x: hidden;
        }

        .container {
            max-width: 680px;
            margin: 0 auto;
            background: rgba(29, 29, 31, 0.72);
            backdrop-filter: saturate(180%) blur(20px);
            -webkit-backdrop-filter: saturate(180%) blur(20px);
            border: 0.5px solid rgba(255, 255, 255, 0.18);
            border-radius: 20px;
            padding: 0;
            box-shadow:
                0 32px 64px rgba(0, 0, 0, 0.35),
                0 0 0 0.5px rgba(255, 255, 255, 0.05) inset;
            margin-top: 3rem;
            margin-bottom: 3rem;
            overflow: hidden;
            position: relative;
        }

        .container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
        }

        .header {
            background: rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            padding: 1.25rem 1.75rem;
            border-bottom: 0.5px solid rgba(255, 255, 255, 0.1);
            position: relative;
        }

        .header::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 1.75rem;
            right: 1.75rem;
            height: 0.5px;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        }

        h1 {
            color: #f5f5f7;
            margin: 0;
            font-size: 1.375rem;
            font-weight: 600;
            letter-spacing: -0.01em;
            display: flex;
            align-items: center;
            gap: 0.625rem;
        }

        .header-icon {
            width: 20px;
            height: 20px;
            background: linear-gradient(135deg, rgba(0, 122, 255, 0.8), rgba(88, 86, 214, 0.8));
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
        }

        .content {
            padding: 1.75rem;
        }

        .feedback-group {
            background: transparent;
            border: none;
            padding: 0;
            margin: 0;
        }

        .group-title {
            font-size: 1.0625rem;
            font-weight: 600;
            margin-bottom: 1.25rem;
            color: #f5f5f7;
            letter-spacing: -0.01em;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .group-title::before {
            content: "💬";
            font-size: 0.875rem;
        }

        .description {
            font-size: 0.9375rem;
            margin-bottom: 1.25rem;
            padding: 1.125rem 1.375rem;
            background: rgba(0, 122, 255, 0.06);
            border: 0.5px solid rgba(0, 122, 255, 0.2);
            border-radius: 16px;
            color: #f5f5f7;
            line-height: 1.47059;
            letter-spacing: -0.022em;
            position: relative;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }

        .description::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 0.5px;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
            border-radius: 16px 16px 0 0;
        }

        .options-container {
            margin-bottom: 1.25rem;
            display: flex;
            flex-direction: column;
            gap: 1rem;  /* 增加选项间距 */
        }

        .option-item {
            display: flex;
            align-items: center;
            padding: 1rem 1.25rem;  /* 增加内边距 */
            background: rgba(255, 255, 255, 0.03);
            border: 0.5px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
            cursor: pointer;
            position: relative;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            margin-bottom: 0.5rem;  /* 添加底部边距 */
        }

        .option-item::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 0.5px;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
            border-radius: 12px 12px 0 0;
        }

        .option-item:hover {
            background: rgba(255, 255, 255, 0.06);
            border-color: rgba(0, 122, 255, 0.3);
            transform: translateY(-1px);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        }

        .option-item input[type="checkbox"] {
            margin-right: 1rem;  /* 增加复选框与文字的间距 */
            width: 18px;  /* 增大复选框尺寸 */
            height: 18px;
            accent-color: #007AFF;
            cursor: pointer;
        }

        .option-item label {
            font-size: 1rem;  /* 增大字体 */
            cursor: pointer;
            color: #f5f5f7;
            flex: 1;
            font-weight: 400;
            letter-spacing: -0.022em;
            line-height: 1.5;  /* 增加行高 */
        }

        .separator {
            height: 0.5px;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
            margin: 1.25rem 0;
        }

        .feedback-textarea {
            width: 100%;
            min-height: 160px;
            padding: 1.125rem 1.375rem;
            font-size: 0.9375rem;
            font-family: "SF Mono", ui-monospace, SFMono-Regular, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
            background: rgba(255, 255, 255, 0.03);
            color: #f5f5f7;
            border: 0.5px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            resize: vertical;
            margin-bottom: 1rem;
            transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
            line-height: 1.47059;
            letter-spacing: -0.022em;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            position: relative;
        }

        .feedback-textarea:focus {
            outline: none;
            border-color: rgba(0, 122, 255, 0.6);
            box-shadow:
                0 0 0 4px rgba(0, 122, 255, 0.08),
                0 1px 3px rgba(0, 0, 0, 0.1);
            background: rgba(255, 255, 255, 0.06);
            transform: translateY(-1px);
        }

        .feedback-textarea::placeholder {
            color: rgba(245, 245, 247, 0.6);
            font-weight: 400;
        }

        .button-container {
            display: flex;
            gap: 0.625rem;
            justify-content: flex-end;
            margin-top: 1.25rem;
        }

        .btn {
            padding: 0.8125rem 1.375rem;
            font-size: 0.9375rem;
            font-weight: 590;
            font-family: inherit;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
            display: flex;
            align-items: center;
            gap: 0.375rem;
            min-width: 110px;
            justify-content: center;
            letter-spacing: -0.022em;
            position: relative;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }

        .btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 0.5px;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            border-radius: 12px 12px 0 0;
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.08);
            color: #f5f5f7;
            border: 0.5px solid rgba(255, 255, 255, 0.2);
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.12);
            border-color: rgba(255, 255, 255, 0.3);
            transform: translateY(-1px);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        }

        .btn-primary {
            background: linear-gradient(135deg, #007AFF 0%, #5856D6 100%);
            color: white;
            border: 0.5px solid rgba(0, 122, 255, 0.3);
            box-shadow:
                0 1px 3px rgba(0, 0, 0, 0.12),
                0 1px 2px rgba(0, 0, 0, 0.24);
        }

        .btn-primary:hover {
            background: linear-gradient(135deg, #0056CC 0%, #4C44B3 100%);
            transform: translateY(-1px);
            box-shadow:
                0 4px 8px rgba(0, 0, 0, 0.15),
                0 2px 4px rgba(0, 0, 0, 0.12);
        }

        .btn:disabled {
            background: rgba(255, 255, 255, 0.03);
            color: rgba(245, 245, 247, 0.3);
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
            border-color: rgba(255, 255, 255, 0.05);
        }

        .status-message {
            margin-top: 1rem;
            padding: 0.875rem 1.125rem;
            border-radius: 12px;
            text-align: center;
            display: none;
            font-size: 0.9375rem;
            font-weight: 500;
            letter-spacing: -0.022em;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            position: relative;
        }

        .status-message::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 0.5px;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
            border-radius: 12px 12px 0 0;
        }

        .status-success {
            background: rgba(52, 199, 89, 0.08);
            color: #34C759;
            border: 0.5px solid rgba(52, 199, 89, 0.2);
        }

        .status-error {
            background: rgba(255, 69, 58, 0.08);
            color: #FF453A;
            border: 0.5px solid rgba(255, 69, 58, 0.2);
        }

        .shortcut-hint {
            font-size: 0.8125rem;
            color: rgba(245, 245, 247, 0.6);
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.375rem;
            font-weight: 400;
            letter-spacing: -0.022em;
        }

        .shortcut-hint::before {
            content: "⌨️";
            font-size: 0.8125rem;
            opacity: 0.8;
        }

        /* Markdown渲染样式 */
        .markdown-content {
            line-height: 1.47059;
            letter-spacing: -0.022em;
        }

        .markdown-content h1,
        .markdown-content h2,
        .markdown-content h3,
        .markdown-content h4,
        .markdown-content h5,
        .markdown-content h6 {
            color: #f5f5f7;
            font-weight: 600;
            margin: 1rem 0 0.5rem 0;
            letter-spacing: -0.01em;
        }

        .markdown-content h1 { font-size: 1.5rem; }
        .markdown-content h2 { font-size: 1.25rem; }
        .markdown-content h3 { font-size: 1.125rem; }
        .markdown-content h4 { font-size: 1rem; }

        .markdown-content p {
            margin: 0.75rem 0;
            color: #f5f5f7;
        }

        .markdown-content ul,
        .markdown-content ol {
            margin: 0.75rem 0;
            padding-left: 1.5rem;
            color: #f5f5f7;
        }

        .markdown-content li {
            margin: 0.25rem 0;
        }

        .markdown-content blockquote {
            margin: 1rem 0;
            padding: 0.75rem 1rem;
            background: rgba(0, 122, 255, 0.08);
            border-left: 3px solid #007AFF;
            border-radius: 0 8px 8px 0;
            color: #f5f5f7;
        }

        .markdown-content code {
            background: rgba(255, 255, 255, 0.1);
            color: #FF453A;
            padding: 0.125rem 0.375rem;
            border-radius: 4px;
            font-family: "SF Mono", ui-monospace, SFMono-Regular, Monaco, Consolas, monospace;
            font-size: 0.875rem;
        }

        .markdown-content pre {
            background: rgba(0, 0, 0, 0.6);
            border: 0.5px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 1rem 1.25rem;
            margin: 1rem 0;
            overflow-x: auto;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }

        .markdown-content pre code {
            background: none;
            color: #f5f5f7;
            padding: 0;
            border-radius: 0;
            font-size: 0.875rem;
        }

        .markdown-content table {
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 8px;
            overflow: hidden;
        }

        .markdown-content th,
        .markdown-content td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 0.5px solid rgba(255, 255, 255, 0.1);
            color: #f5f5f7;
        }

        .markdown-content th {
            background: rgba(0, 122, 255, 0.1);
            font-weight: 600;
        }

        .markdown-content a {
            color: #007AFF;
            text-decoration: none;
        }

        .markdown-content a:hover {
            text-decoration: underline;
        }

        .markdown-content hr {
            border: none;
            height: 0.5px;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            margin: 1.5rem 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <div class="header-icon">💬</div>
                Cursor继续对话
            </h1>
        </div>

        <!-- 无有效内容页面 -->
        <div id="no-content-container" style="display: none; flex-direction: column; align-items: center; justify-content: center; min-height: 400px; text-align: center;">
            <div style="font-size: 4rem; margin-bottom: 1rem; opacity: 0.3;">⏳</div>
            <h2 style="color: #8e8e93; font-size: 1.5rem; margin-bottom: 0.5rem;">无有效内容</h2>
            <p style="color: #8e8e93; font-size: 1rem; margin-bottom: 2rem;">等待新的反馈请求...</p>
            <div style="width: 200px; height: 4px; background: rgba(255, 255, 255, 0.1); border-radius: 2px; overflow: hidden;">
                <div style="width: 100%; height: 100%; background: linear-gradient(90deg, transparent, #0a84ff, transparent); animation: loading 2s infinite;"></div>
            </div>
            <div class="button-container" id="no-content-buttons" style="display: none; margin-top: 2rem;">
                <button class="btn btn-secondary" id="close-btn">
                    ❌ 关闭界面
                </button>
            </div>
        </div>

        <!-- 正常内容页面 -->
        <div id="content-container" class="content">
            <div class="feedback-group">
                <div class="group-title">反馈内容</div>

                <div class="description markdown-content" id="description">
                    加载中...
                </div>

                <div class="options-container" id="options-container" style="display: none;">
                    <!-- 预定义选项将在这里动态加载 -->
                </div>

                <div class="separator" id="separator" style="display: none;"></div>

                <textarea
                    class="feedback-textarea"
                    id="feedback-text"
                    placeholder="请在此输入您的反馈内容..."
                ></textarea>

                <div class="shortcut-hint">
                    按 Ctrl+Enter 快速提交反馈
                </div>

                <div class="button-container">
                    <button class="btn btn-secondary" id="insert-code-btn">
                        📋 插入代码
                    </button>
                    <button class="btn btn-primary" id="submit-btn">
                        🚀 发送请求
                    </button>
                </div>

                <div class="status-message" id="status-message"></div>
            </div>
        </div>
    </div>

    <script>
        let config = null;

        // 加载配置
        async function loadConfig() {
            try {
                const response = await fetch('/api/config');
                config = await response.json();

                // 检查是否有有效内容
                if (!config.has_content) {
                    showNoContentPage();
                    // 如果初始就没有内容，即使是持续模式也应该关闭
                    // 如果不是持续模式且没有内容，也自动关闭
                    if (config.initial_empty || !config.persistent) {
                        setTimeout(() => {
                            const message = config.initial_empty ?
                                '没有输入内容，持续模式结束，页面将在3秒后关闭...' :
                                '没有反馈内容，页面将在3秒后关闭...';
                            showStatus(message, 'info');
                            setTimeout(() => {
                                window.close();
                            }, 3000);
                        }, 1000);
                    }
                    return;
                }

                // 显示正常内容页面
                showContentPage();

                // 更新描述 - 使用Markdown渲染的HTML
                const descriptionElement = document.getElementById('description');
                if (config.prompt_html) {
                    descriptionElement.innerHTML = config.prompt_html;
                } else {
                    descriptionElement.textContent = config.prompt;
                }

                // 加载预定义选项
                if (config.predefined_options && config.predefined_options.length > 0) {
                    const optionsContainer = document.getElementById('options-container');
                    const separator = document.getElementById('separator');

                    config.predefined_options.forEach((option, index) => {
                        const optionDiv = document.createElement('div');
                        optionDiv.className = 'option-item';

                        const checkbox = document.createElement('input');
                        checkbox.type = 'checkbox';
                        checkbox.id = `option-${index}`;
                        checkbox.value = option;

                        const label = document.createElement('label');
                        label.htmlFor = `option-${index}`;
                        label.textContent = option;

                        optionDiv.appendChild(checkbox);
                        optionDiv.appendChild(label);
                        optionsContainer.appendChild(optionDiv);
                    });

                    optionsContainer.style.display = 'block';
                    separator.style.display = 'block';
                }
            } catch (error) {
                console.error('加载配置失败:', error);
                showStatus('加载配置失败', 'error');
            }
        }

        // 显示无内容页面
        function showNoContentPage() {
            document.getElementById('content-container').style.display = 'none';
            document.getElementById('no-content-container').style.display = 'flex';

            // 如果不是持续模式，显示关闭按钮
            if (config && !config.persistent) {
                document.getElementById('no-content-buttons').style.display = 'block';
            }
        }

        // 显示内容页面
        function showContentPage() {
            document.getElementById('content-container').style.display = 'block';
            document.getElementById('no-content-container').style.display = 'none';
            enableSubmitButton();
        }

        // 禁用提交按钮
        function disableSubmitButton() {
            const submitBtn = document.getElementById('submit-btn');
            const insertBtn = document.getElementById('insert-code-btn');
            const feedbackText = document.getElementById('feedback-text');

            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.style.backgroundColor = '#3a3a3c';
                submitBtn.style.color = '#8e8e93';
                submitBtn.style.cursor = 'not-allowed';
            }
            if (insertBtn) {
                insertBtn.disabled = true;
                insertBtn.style.backgroundColor = '#3a3a3c';
                insertBtn.style.color = '#8e8e93';
                insertBtn.style.cursor = 'not-allowed';
            }
            if (feedbackText) {
                feedbackText.disabled = true;
                feedbackText.style.backgroundColor = '#2c2c2e';
                feedbackText.style.color = '#8e8e93';
                feedbackText.style.cursor = 'not-allowed';
            }
        }

        // 启用提交按钮
        function enableSubmitButton() {
            const submitBtn = document.getElementById('submit-btn');
            const insertBtn = document.getElementById('insert-code-btn');
            const feedbackText = document.getElementById('feedback-text');

            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.style.backgroundColor = '#0a84ff';
                submitBtn.style.color = '#ffffff';
                submitBtn.style.cursor = 'pointer';
            }
            if (insertBtn) {
                insertBtn.disabled = false;
                insertBtn.style.backgroundColor = '#48484a';
                insertBtn.style.color = '#ffffff';
                insertBtn.style.cursor = 'pointer';
            }
            if (feedbackText) {
                feedbackText.disabled = false;
                feedbackText.style.backgroundColor = 'rgba(255, 255, 255, 0.03)';
                feedbackText.style.color = '#f5f5f7';
                feedbackText.style.cursor = 'text';
            }
        }

        // 显示状态消息
        function showStatus(message, type) {
            const statusElement = document.getElementById('status-message');
            statusElement.textContent = message;
            statusElement.className = `status-message status-${type}`;
            statusElement.style.display = 'block';

            if (type === 'success') {
                setTimeout(() => {
                    statusElement.style.display = 'none';
                }, 3000);
            }
        }

        // 插入代码功能 - 与GUI版本逻辑完全一致
        async function insertCodeFromClipboard() {
            try {
                const text = await navigator.clipboard.readText();
                if (text) {
                    const textarea = document.getElementById('feedback-text');
                    const cursorPos = textarea.selectionStart;
                    const currentText = textarea.value;
                    const textBefore = currentText.substring(0, cursorPos);
                    const textAfter = currentText.substring(cursorPos);

                    // 构建要插入的代码块，在```前面总是添加换行
                    let codeBlock = `\n\`\`\`\n${text}\n\`\`\``;

                    // 如果是在文本开头插入，则不需要前面的换行
                    if (cursorPos === 0) {
                        codeBlock = `\`\`\`\n${text}\n\`\`\``;
                    }

                    // 插入代码块
                    textarea.value = textBefore + codeBlock + textAfter;

                    // 将光标移动到代码块末尾（与GUI版本一致）
                    const newCursorPos = textBefore.length + codeBlock.length;
                    textarea.setSelectionRange(newCursorPos, newCursorPos);
                    textarea.focus();

                    showStatus('代码已插入', 'success');
                } else {
                    showStatus('剪贴板为空', 'error');
                }
            } catch (error) {
                console.error('读取剪贴板失败:', error);
                showStatus('无法读取剪贴板，请手动粘贴代码', 'error');
            }
        }

        // 提交反馈
        async function submitFeedback() {
            const feedbackText = document.getElementById('feedback-text').value.trim();
            const selectedOptions = [];

            // 获取选中的预定义选项
            if (config && config.predefined_options) {
                config.predefined_options.forEach((option, index) => {
                    const checkbox = document.getElementById(`option-${index}`);
                    if (checkbox && checkbox.checked) {
                        selectedOptions.push(option);
                    }
                });
            }

            if (!feedbackText && selectedOptions.length === 0) {
                // 如果是持续模式且没有任何输入，关闭持续模式
                if (config && config.persistent) {
                    showStatus('没有输入内容，持续模式结束...', 'info');
                    setTimeout(() => {
                        window.close();
                    }, 1500);
                    return;
                } else {
                    showStatus('请输入反馈内容或选择预定义选项', 'error');
                    return;
                }
            }

            try {
                const submitBtn = document.getElementById('submit-btn');
                submitBtn.disabled = true;
                submitBtn.textContent = '提交中...';

                const response = await fetch('/api/submit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        feedback_text: feedbackText,
                        selected_options: selectedOptions
                    })
                });

                const result = await response.json();

                if (response.ok) {
                    showStatus(result.message, 'success');
                    // 清空表单
                    document.getElementById('feedback-text').value = '';
                    // 取消选中所有复选框
                    document.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);

                    // 检查是否为持续模式
                    if (result.persistent) {
                        // 持续模式：隐藏反馈内容，禁用提交按钮，显示等待状态
                        showNoContentPage();
                        disableSubmitButton();
                        setTimeout(() => {
                            showStatus('等待新的反馈请求...', 'info');
                        }, 1000);
                    } else {
                        // 单次模式：显示关闭提示
                        setTimeout(() => {
                            showStatus('页面将在3秒后关闭...', 'info');
                            setTimeout(() => {
                                window.close();
                            }, 3000);
                        }, 1000);
                    }
                } else {
                    showStatus(result.message || '提交失败', 'error');
                }
            } catch (error) {
                console.error('提交失败:', error);
                showStatus('网络错误，请重试', 'error');
            } finally {
                const submitBtn = document.getElementById('submit-btn');
                submitBtn.disabled = false;
                submitBtn.textContent = '🚀 提交反馈';
            }
        }

        // 关闭界面
        async function closeInterface() {
            try {
                showStatus('正在关闭界面...', 'info');
                const response = await fetch('/api/close', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                const result = await response.json();
                if (response.ok) {
                    showStatus('界面即将关闭...', 'success');
                    setTimeout(() => {
                        window.close();
                    }, 1000);
                } else {
                    showStatus(result.message || '关闭失败', 'error');
                }
            } catch (error) {
                console.error('关闭界面失败:', error);
                showStatus('关闭界面失败', 'error');
            }
        }

        // 内容轮询检查
        let pollingInterval = null;
        function startContentPolling() {
            if (pollingInterval) return; // 避免重复启动

            pollingInterval = setInterval(async () => {
                try {
                    const response = await fetch('/api/config');
                    const newConfig = await response.json();

                    // 检查是否有新内容
                    if (newConfig.has_content && (!config || !config.has_content)) {
                        // 从无内容状态变为有内容状态
                        config = newConfig;
                        showContentPage();
                        updatePageContent();
                        showStatus('收到新的反馈请求！', 'success');
                    } else if (!newConfig.has_content && config && config.has_content) {
                        // 从有内容状态变为无内容状态
                        config = newConfig;
                        showNoContentPage();
                        disableSubmitButton();
                    } else if (newConfig.has_content && config && config.has_content) {
                        // 内容更新
                        if (newConfig.prompt !== config.prompt ||
                            JSON.stringify(newConfig.predefined_options) !== JSON.stringify(config.predefined_options)) {
                            config = newConfig;
                            updatePageContent();
                            showStatus('内容已更新！', 'success');
                        }
                    }
                } catch (error) {
                    console.error('轮询错误:', error);
                }
            }, 2000); // 每2秒检查一次
        }

        function stopContentPolling() {
            if (pollingInterval) {
                clearInterval(pollingInterval);
                pollingInterval = null;
            }
        }

        // 更新页面内容
        function updatePageContent() {
            if (!config) return;

            // 更新提示内容
            const descriptionElement = document.getElementById('description');
            if (descriptionElement) {
                if (config.prompt_html) {
                    descriptionElement.innerHTML = config.prompt_html;
                } else {
                    descriptionElement.textContent = config.prompt;
                }
            }

            // 更新预定义选项
            const optionsContainer = document.getElementById('options-container');
            if (optionsContainer) {
                optionsContainer.innerHTML = '';

                if (config.predefined_options && config.predefined_options.length > 0) {
                    config.predefined_options.forEach((option, index) => {
                        const optionDiv = document.createElement('div');
                        optionDiv.className = 'option-item';
                        optionDiv.innerHTML = `
                            <input type="checkbox" id="option-${index}" value="${option}">
                            <label for="option-${index}">${option}</label>
                        `;
                        optionsContainer.appendChild(optionDiv);
                    });
                    optionsContainer.style.display = 'block';
                    document.getElementById('separator').style.display = 'block';
                } else {
                    optionsContainer.style.display = 'none';
                    document.getElementById('separator').style.display = 'none';
                }
            }
        }

        // 事件监听器
        document.addEventListener('DOMContentLoaded', () => {
            loadConfig();

            // 如果是持续模式，启动轮询
            setTimeout(() => {
                if (config && config.persistent) {
                    startContentPolling();
                }
            }, 1000);

            // 按钮事件
            document.getElementById('insert-code-btn').addEventListener('click', insertCodeFromClipboard);
            document.getElementById('submit-btn').addEventListener('click', submitFeedback);
            document.getElementById('close-btn').addEventListener('click', closeInterface);

            // 键盘快捷键
            document.addEventListener('keydown', (event) => {
                if (event.ctrlKey && event.key === 'Enter') {
                    event.preventDefault();
                    submitFeedback();
                } else if (event.altKey && event.key === 'c') {
                    event.preventDefault();
                    insertCodeFromClipboard();
                } else if (event.altKey && event.key === 's') {
                    event.preventDefault();
                    submitFeedback();
                }
            });
        });
    </script>
</body>
</html>
        '''

    def update_content(self, new_prompt: str, new_options: Optional[List[str]] = None):
        """更新页面内容（仅在持续模式下可用）"""
        if self.persistent:
            self.current_prompt = new_prompt
            self.current_options = new_options if new_options is not None else []
            self.has_content = bool(new_prompt)
            if new_prompt:
                print(f"📝 内容已更新: {new_prompt[:50]}...")
            else:
                print("📝 内容已清空，显示无有效内容页面")

    def run(self) -> Dict[str, str]:
        """启动Web服务器并等待用户反馈"""
        mode_text = "持续模式" if self.persistent else "单次模式"
        print(f"\n🌐 Web反馈界面已启动 ({mode_text})")
        print(f"📍 请在浏览器中打开: http://{self.host}:{self.port}")
        if self.host == "0.0.0.0":
            print(f"🔗 SSH端口转发命令: ssh -L {self.port}:localhost:{self.port} user@remote_server")

        if self.persistent:
            print("🔄 持续模式：页面将保持打开，可实时更新内容")
        else:
            print("⏳ 单次模式：等待用户反馈后自动关闭")
        print()

        try:
            self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)
        except KeyboardInterrupt:
            pass

        return self.feedback_result or {'cursor_usage_opt': ''}

def web_feedback_ui(prompt: str, predefined_options: Optional[List[str]] = None,
                   output_file: Optional[str] = None, host: str = "0.0.0.0",
                   port: int = 8080) -> Optional[Dict[str, str]]:
    """启动Web版反馈界面"""
    ui = WebFeedbackUI(prompt, predefined_options, host, port)
    result = ui.run()

    if output_file and result:
        # 确保目录存在
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
        # 保存结果到输出文件
        with open(output_file, "w", encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        return None

    return result

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="运行Web版反馈界面")
    parser.add_argument("--prompt", default="我已经实现了您请求的更改。", help="向用户显示的提示信息")
    parser.add_argument("--predefined-options", default="", help="预定义选项列表，用|||分隔")
    parser.add_argument("--output-file", help="将反馈结果保存为JSON文件的路径")
    parser.add_argument("--host", default="0.0.0.0", help="Web服务器监听地址")
    parser.add_argument("--port", type=int, default=8080, help="Web服务器监听端口")
    args = parser.parse_args()

    predefined_options = [opt for opt in args.predefined_options.split("|||") if opt] if args.predefined_options else None

    result = web_feedback_ui(args.prompt, predefined_options, args.output_file, args.host, args.port)
    if result:
        print(f"\n收到反馈:\n{result['cursor_usage_opt']}")
    import sys
    sys.exit(0)
