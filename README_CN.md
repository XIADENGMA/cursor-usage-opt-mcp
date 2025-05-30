# 🗣️ Cursor Usage Opt MCP

简单的 [MCP Server](https://modelcontextprotocol.io/)，为 [Cursor](https://www.cursor.com)、[Cline](https://cline.bot) 和 [Windsurf](https://windsurf.com) 等 AI 辅助开发工具提供人机协作工作流。该服务器允许您直接向 AI 助手提供反馈，在 AI 和您之间架起桥梁。

**注意：** 该服务器设计为与 MCP 客户端（如 Claude Desktop、VS Code）本地运行，因为它需要直接访问用户的操作系统来显示通知。

## 🖼️ 示例

![交互式反馈示例](https://raw.githubusercontent.com/poliva/interactive-feedback-mcp/refs/heads/main/.github/example.png)

## 💡 为什么使用这个工具？

在 Cursor 等环境中，您发送给 LLM 的每个提示都被视为独立请求，每个都会计入您的月度限额（例如 500 个高级请求）。当您需要对模糊指令进行迭代或纠正误解的输出时，这变得低效，因为每次后续澄清都会触发一个全新的请求。

这个 MCP 服务器引入了一个解决方案：它允许模型在完成响应之前暂停并请求澄清。模型不会完成请求，而是触发一个工具调用（`cursor_usage_opt`）来打开交互式反馈窗口。然后您可以提供更多细节或要求更改——模型在同一个请求中继续会话。

本质上，这只是巧妙地使用工具调用来延迟请求的完成。由于工具调用不算作单独的高级交互，您可以在不消耗额外请求的情况下循环多个反馈周期。

从根本上说，这有助于您的 AI 助手在不浪费另一个请求的情况下*请求澄清而不是猜测*。这意味着更少的错误答案、更好的性能和更少的 API 使用浪费。

- **💰 减少高级 API 调用**：避免基于猜测生成代码而浪费昂贵的 API 调用。
- **✅ 更少错误**：行动前的澄清意味着更少的错误代码和浪费的时间。
- **⏱️ 更快周期**：快速确认胜过调试错误猜测。
- **🎮 更好协作**：将单向指令转变为对话，让您保持控制。

## ✨ 功能特性

### 📋 交互式反馈界面

- **多语言支持**：完全支持中文和其他语言，增强输入法集成
- **深色模式 UI**：专业深色主题，优化字体以提高可读性
- **预定义选项**：从预定义选择中快速选择，加快决策制定
- **自由文本输入**：详细反馈，支持丰富的文本编辑功能

### 🔧 代码集成工具

- **📌 插入代码按钮**：一键插入剪贴板内容为格式化代码块
  - 自动将剪贴板内容包装在 markdown 代码块中（```）
  - 智能格式化，保持适当的换行和缩进
  - 键盘快捷键支持（Alt+C）
  - 智能光标定位，实现无缝工作流

### ⌨️ 键盘快捷键

- **Ctrl+Enter**：快速提交反馈
- **Alt+C**：从剪贴板插入代码
- **Alt+S**：提交请求（再次发送请求）

### 🎯 智能工作流

- **上下文保持**：在反馈周期中保持对话上下文
- **自动焦点**：自动焦点管理，优化用户体验
- **会话记忆**：记住窗口位置和大小偏好

## 🛠️ 工具

该服务器通过模型上下文协议（MCP）暴露以下工具：

- `cursor_usage_opt`：向用户提问并返回他们的答案。可以显示预定义选项，并提供增强的代码分享和协作界面。

## 📦 安装

1.  **先决条件：**
    - Python 3.11 或更新版本。
    - [uv](https://github.com/astral-sh/uv)（Python 包管理器）。安装方法：
      - Windows：`pip install uv`
      - Linux：`curl -LsSf https://astral.sh/uv/install.sh | sh`
      - macOS：`brew install uv`
2.  **获取代码：**
    - 克隆此仓库：
      `git clone https://github.com/xiadengma/cursor-usage-opt-mcp.git`
    - 或下载源代码。

## ⚙️ 配置

1. 将以下配置添加到您的 `claude_desktop_config.json`（Claude Desktop）或 `mcp.json`（Cursor）：
   **记住将 `/path/to/cursor-usage-opt-mcp` 路径更改为您在系统上克隆仓库的实际路径。**

```json
{
  "mcpServers": {
    "cursor-usage-opt": {
      "command": "uv",
      "args": ["--directory", "/path/to/cursor-usage-opt-mcp", "run", "server.py"],
      "timeout": 600,
      "autoApprove": ["cursor_usage_opt"]
    }
  }
}
```

2. 将以下内容添加到您的 AI 助手的自定义规则中（在 Cursor 设置 > 规则 > 用户规则）：

> 如果需求或指令不清楚，请在继续之前使用 cursor_usage_opt 工具向用户提出澄清问题，不要做假设。尽可能通过 cursor_usage_opt MCP 工具向用户提供预定义选项，以便快速决策。

> 每当您即将完成用户请求时，在结束过程之前调用 cursor_usage_opt 工具请求用户反馈。如果反馈为空，您可以结束请求，不要循环调用该工具。

这将确保您的 AI 助手始终使用此 MCP 服务器在提示不清楚时请求用户反馈，并在将任务标记为完成之前使用。

## 🚀 使用技巧

### 📝 代码分享工作流

1. 将代码片段复制到剪贴板
2. 通过 AI 助手打开反馈界面
3. 点击"插入代码"按钮或按 Alt+C
4. 代码会自动格式化并插入为：

```
您的剪贴板内容
```

5. 添加额外的上下文或指令
6. 使用 Ctrl+Enter 提交或点击"再次发送请求"

### 🎯 最佳实践

- 使用预定义选项进行快速是/否决策
- 利用"插入代码"功能分享示例或错误消息
- 利用键盘快捷键进行更快的交互
- 界面会在会话间记住您的偏好

## 🙏 致谢

由 Fábio Ferreira ([@fabiomlferreira](https://x.com/fabiomlferreira)) 开发。

由 Pau Oliva ([@pof](https://x.com/pof)) 增强，灵感来自 Tommy Tong 的 [interactive-mcp](https://github.com/ttommyth/interactive-mcp)。

进一步增强了中文语言支持和代码集成功能。
