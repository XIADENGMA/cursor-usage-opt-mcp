# Interactive Feedback MCP
# Developed by Fábio Ferreira (https://x.com/fabiomlferreira)
# Inspired by/related to dotcursorrules.com (https://dotcursorrules.com/)
# Enhanced by Pau Oliva (https://x.com/pof) with ideas from https://github.com/ttommyth/interactive-mcp
# Enhanced with Web UI support for SSH remote usage
import os
import sys
import json
import tempfile
import subprocess

from typing import Annotated, Dict

from fastmcp import FastMCP
from pydantic import Field

# The log_level is necessary for Cline to work: https://github.com/jlowin/fastmcp/issues/81
mcp = FastMCP("Interactive Feedback MCP", log_level="ERROR")

def has_gui_environment() -> bool:
    """检测是否有GUI环境可用"""
    # 检查DISPLAY环境变量 (X11)
    if os.environ.get('DISPLAY'):
        return True

    # 检查WAYLAND_DISPLAY环境变量 (Wayland)
    if os.environ.get('WAYLAND_DISPLAY'):
        return True

    # 检查是否在SSH会话中
    if os.environ.get('SSH_CLIENT') or os.environ.get('SSH_TTY'):
        return False

    # 在Windows上，通常有GUI环境
    if sys.platform == 'win32':
        return True

    # 在macOS上，通常有GUI环境
    if sys.platform == 'darwin':
        return True

    return False

def get_web_ui_config() -> dict:
    """获取Web UI配置"""
    # 从环境变量读取配置，提供默认值
    host = os.environ.get('FEEDBACK_WEB_HOST', '0.0.0.0')
    port = int(os.environ.get('FEEDBACK_WEB_PORT', '8080'))
    return {'host': host, 'port': port}

def launch_feedback_ui(summary: str, predefinedOptions: list[str] | None = None) -> dict[str, str]:
    # Create a temporary file for the feedback result
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        output_file = tmp.name

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # 检测是否有GUI环境
        if has_gui_environment():
            # 使用GUI模式
            feedback_ui_path = os.path.join(script_dir, "feedback_ui.py")

            # Run feedback_ui.py as a separate process
            # NOTE: There appears to be a bug in uv, so we need
            # to pass a bunch of special flags to make this work
            args = [
                sys.executable,
                "-u",
                feedback_ui_path,
                "--prompt", summary,
                "--output-file", output_file,
                "--predefined-options", "|||".join(predefinedOptions) if predefinedOptions else ""
            ]
            result = subprocess.run(
                args,
                check=False,
                shell=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                close_fds=True
            )
            if result.returncode != 0:
                raise Exception(f"Failed to launch GUI feedback UI: {result.returncode}")
        else:
            # 使用Web模式
            web_ui_path = os.path.join(script_dir, "web_ui.py")
            web_config = get_web_ui_config()

            args = [
                sys.executable,
                "-u",
                web_ui_path,
                "--prompt", summary,
                "--output-file", output_file,
                "--predefined-options", "|||".join(predefinedOptions) if predefinedOptions else "",
                "--host", web_config['host'],
                "--port", str(web_config['port'])
            ]
            result = subprocess.run(
                args,
                check=False,
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                close_fds=True,
                text=True
            )
            if result.returncode != 0:
                print(f"Web UI stdout: {result.stdout}")
                print(f"Web UI stderr: {result.stderr}")
                raise Exception(f"Failed to launch Web feedback UI: {result.returncode}")

        # Read the result from the temporary file
        with open(output_file, 'r', encoding='utf-8') as f:
            result = json.load(f)
        os.unlink(output_file)
        return result
    except Exception as e:
        if os.path.exists(output_file):
            os.unlink(output_file)
        raise e

@mcp.tool()
def cursor_usage_opt(
    message: str = Field(description="The specific question for the user"),
    predefined_options: list = Field(default=None, description="Predefined options for the user to choose from (optional)"),
) -> Dict[str, str]:
    """Request interactive feedback from the user"""
    predefined_options_list = predefined_options if isinstance(predefined_options, list) else None
    return launch_feedback_ui(message, predefined_options_list)

if __name__ == "__main__":
    mcp.run(transport="stdio")
