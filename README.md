# 🗣️ Cursor Usage Opt MCP

简单而强大的 [MCP 服务器](https://modelcontextprotocol.io/)，为 [Cursor](https://www.cursor.com)、[Cline](https://cline.bot) 和 [Windsurf](https://windsurf.com) 等 AI 辅助开发工具提供交互式反馈功能。

## 💡 为什么使用这个工具？

这个 MCP 服务器允许 AI 模型在完成响应之前暂停并请求澄清。AI 不再需要猜测您的需求，而是打开一个交互式反馈窗口，您可以在其中提供更多详细信息或修正 — 所有这些都在一个请求中完成。

**核心优势：**

- **💰 节省 API 调用：** 在一个请求中进行多轮反馈循环
- **✅ 减少错误：** 在行动前获得澄清
- **⏱️ 更快的工作流：** 快速确认胜过调试错误猜测
- **🌍 全场景支持：** 本地 GUI 和远程 Web 双模式

## ✨ 功能特性

### 🔄 智能双模式

- **🖥️ GUI 模式：** 本地环境的原生桌面界面，Apple 风格设计
- **🌐 Web 模式：** SSH 远程服务器的浏览器界面，支持端口转发
- **🔄 自动检测：** 根据环境自动选择最佳模式
- **🔄 持续模式：** Web 界面支持持续接收，实时更新内容
- **🎯 智能关闭：** 无输入时自动结束持续模式，避免资源浪费

### 📝 丰富的交互功能

- **Markdown 支持：** 完整的 Markdown 渲染和语法高亮
- **代码插入：** 一键插入剪贴板代码，自动格式化为代码块
- **预定义选项：** 快速选择预设选项，支持多选
- **自由文本输入：** 详细的反馈文本编辑，支持大文本
- **智能关闭：** 多种关闭策略，适应不同使用场景
- **实时轮询：** 持续模式下每 2 秒检查内容更新

### ⌨️ 键盘快捷键

- **Ctrl+Enter：** 快速提交反馈
- **Alt+C：** 从剪贴板插入代码
- **Alt+S：** 提交请求

### 🎨 界面设计

- **🍎 Apple 风格：** 深色主题，SF Pro 字体系统，圆角设计
- **📱 响应式设计：** Web 版本适配各种屏幕尺寸
- **🔤 字体优化：** 大字号设计（22px 主体，20px 代码），优化中文显示
- **🌍 多语言支持：** 完整的中文输入法集成
- **🎯 状态反馈：** 清晰的状态提示和进度指示

## 📦 安装

### 前置要求

- **Python 3.11+：** 现代 Python 版本
- **uv：** 快速的 Python 包管理器
- **图形环境：** GUI 模式需要（可选）

### 快速安装

```bash
# 1. 安装 uv 包管理器
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/macOS
# 或者 pip install uv  # Windows

# 2. 克隆项目
git clone https://github.com/xiadengma/cursor-usage-opt-mcp.git
cd cursor-usage-opt-mcp

# 3. 安装依赖
uv sync
```

### 验证安装

```bash
# 运行测试确保一切正常
uv run python test.py
```

## ⚙️ 配置

### MCP 服务器配置

将以下配置添加到您的 AI 工具配置文件中：

**Claude Desktop** (`claude_desktop_config.json`)：

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

**Cursor** (`mcp.json`)：

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

> **注意：** 请将 `/path/to/cursor-usage-opt-mcp` 替换为您实际的项目路径。

### 远程服务器配置

对于 SSH 远程服务器使用，添加环境变量配置：

```json
{
  "mcpServers": {
    "cursor-usage-opt": {
      "command": "uv",
      "args": ["--directory", "/path/to/cursor-usage-opt-mcp", "run", "server.py"],
      "timeout": 600,
      "autoApprove": ["cursor_usage_opt"],
      "env": {
        "FEEDBACK_WEB_HOST": "0.0.0.0",
        "FEEDBACK_WEB_PORT": "8080"
      }
    }
  }
}
```

### SSH 端口转发

```bash
# 建立端口转发
ssh -L 8080:localhost:8080 user@remote_server

# 在本地浏览器访问
http://localhost:8080
```

### AI 助手规则配置

在您的 AI 助手中添加以下规则（推荐在 Cursor 设置 > 规则 > 用户规则中）：

```
# MCP Interactive Feedback 规则
1. 在执行重要任务前，使用 cursor_usage_opt 工具向用户确认需求和细节
2. 当需要澄清用户意图时，调用 cursor_usage_opt 获取更多信息
3. 完成阶段性任务后，使用 cursor_usage_opt 询问用户反馈和下一步计划
4. 收到用户反馈后，根据反馈内容调整后续行为
5. 只有在用户明确表示满意或结束时，才停止交互循环
```

## 🚀 使用方法

### 智能模式切换

服务器会根据环境自动选择最佳界面模式：

- **🖥️ 本地环境：** 启动 Apple 风格 GUI 界面
- **🌐 远程环境：** 启动 Web 浏览器界面
- **🔄 持续模式：** Web 界面支持实时内容更新

### 操作流程

1. **AI 发起请求：** AI 助手调用 `cursor_usage_opt` 工具
2. **界面自动打开：** 根据环境显示 GUI 或 Web 界面
3. **查看内容：** 阅读 AI 的问题（支持 Markdown 渲染）
4. **提供反馈：**
   - 选择预定义选项（支持多选）
   - 输入自定义文本反馈
   - 使用"插入代码"功能分享代码片段
   - **空输入提交：** 持续模式下无输入时自动结束
5. **提交反馈：** 点击提交或使用快捷键 Ctrl+Enter
6. **AI 继续处理：** 基于您的反馈继续执行任务

### 持续模式特性

- **实时更新：** 页面每 2 秒检查新内容，自动刷新显示
- **智能关闭：** 多种关闭策略适应不同场景
  - 初始无内容：立即关闭
  - 运行中无输入：用户确认后关闭
  - 手动关闭：提供关闭按钮
- **状态管理：** 清晰的"有内容"↔"无内容"状态切换

### 界面特色

- **🍎 Apple 设计语言：** 深色主题，圆角设计，系统蓝色
- **📝 优化字体：** SF Pro 字体系统，22px 主体/20px 代码大字号显示
- **⌨️ 快捷键支持：** Ctrl+Enter 提交，Alt+C 插入代码
- **📱 响应式布局：** Web 版本适配各种屏幕尺寸
- **🔄 智能关闭：** 多策略自动关闭，避免资源浪费

## 🧪 测试

运行综合测试工具验证安装：

```bash
uv run python test.py
```

**测试选项：**

```
┌─────────────────────────────────────────────┐
│  1. 🖥️  GUI模式测试 (推荐)                │
│  2. 🌐  Web模式测试                        │
│  3. 🔧  MCP服务器测试                      │
│  4. 🚀  运行所有测试                       │
│  0. 🚪  退出                              │
└─────────────────────────────────────────────┘
```

**测试内容：**

- **🖥️ GUI 模式：** Apple 风格界面、字体渲染、交互功能
- **🌐 Web 模式：** 浏览器界面、持续模式、自动更新、智能关闭
- **🔧 MCP 服务器：** 环境检测、工具调用、反馈处理
- **🚀 综合测试：** 完整功能验证和兼容性检查

## 🔧 故障排除

### 常见问题

| 问题               | 解决方案                                                    |
| ------------------ | ----------------------------------------------------------- |
| **GUI 无法启动**   | 检查图形环境和 PySide6 安装：`uv add pyside6`               |
| **Web 端口冲突**   | 修改环境变量：`FEEDBACK_WEB_PORT=8081`                      |
| **中文输入异常**   | 确保系统安装中文输入法（如 fcitx5）                         |
| **SSH 连接失败**   | 检查端口转发：`ssh -L 8080:localhost:8080 user@host`        |
| **依赖安装失败**   | 更新 uv：`curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **持续模式不更新** | 检查浏览器控制台，确认轮询请求正常                          |
| **页面无法关闭**   | 刷新页面或检查 JavaScript 控制台错误                        |

### 调试模式

```bash
# 查看详细日志
PYTHONPATH=. uv run python server.py

# 测试特定模式
uv run python feedback_ui.py  # GUI 模式
uv run python web_ui.py       # Web 模式

# 调试持续模式
# 在浏览器开发者工具中查看控制台输出
# 检查 /api/config 轮询请求和响应
```

### 持续模式调试

如果持续模式自动更新不工作：

1. **检查轮询请求**：浏览器开发者工具 → 网络标签 → 查看每 2 秒的 `/api/config` 请求
2. **检查控制台**：开发者工具 → 控制台 → 查看 JavaScript 错误或状态信息
3. **验证状态变化**：确认服务器端 `has_content` 状态正确切换
4. **手动刷新**：如果自动更新失败，手动刷新页面重新同步状态

## 🆕 最新改进

### v1.2 功能增强

- **🎯 智能关闭策略**：

  - 初始无内容时立即关闭持续模式
  - 运行中无输入提交时优雅结束
  - 手动关闭按钮支持

- **🔄 持续模式优化**：

  - 每 2 秒轮询检查内容更新
  - 自动状态切换和页面刷新
  - 清晰的状态提示和反馈

- **🎨 界面美化**：

  - 测试菜单表格化显示
  - 字体大小统一优化（22px 主体/20px 代码）
  - Apple 风格设计语言完善

- **🧪 测试完善**：
  - 规整的测试界面布局
  - 完整的持续模式测试流程
  - 详细的调试和故障排除指南

## 📋 项目信息

### 技术栈

- **后端：** Python 3.11+, FastMCP, Flask
- **GUI：** PySide6 (Qt6)
- **Web：** HTML5, CSS3, JavaScript
- **包管理：** uv, pyproject.toml
- **渲染：** Markdown, Pygments

### 项目结构

```
cursor-usage-opt-mcp/
├── server.py          # MCP 服务器主程序
├── feedback_ui.py     # GUI 界面实现
├── web_ui.py          # Web 界面实现
├── test.py            # 综合测试工具
├── pyproject.toml     # 项目配置和依赖
└── README.md          # 项目文档
```

## 🙏 致谢

本项目基于以下优秀工作：

- **Fábio Ferreira** 和 **Pau Oliva** 的原始 MCP 实现
- **Tommy Tong** 的 [interactive-mcp](https://github.com/ttommyth/interactive-mcp) 项目创意
- **Apple** 的设计语言和字体系统
- **MCP 协议** 的标准化工作

## 📄 许可证

本项目采用开源许可证，详见 [LICENSE](LICENSE) 文件。
