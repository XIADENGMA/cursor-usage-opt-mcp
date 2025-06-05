#!/usr/bin/env python3
"""
Cursor Usage Opt MCP 综合测试工具
包含GUI、Web、MCP服务器的完整测试功能
"""

import sys
import os
import json
import threading
import time
import tempfile
from typing import Optional

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_environment():
    """检测测试环境"""
    print("🔍 检测测试环境...")

    try:
        from server import has_gui_environment
        has_gui = has_gui_environment()
        print(f"✅ GUI环境: {'可用' if has_gui else '不可用'}")

        # 检查依赖
        try:
            import PySide6
            print("✅ PySide6: 已安装")
        except ImportError:
            print("❌ PySide6: 未安装")

        try:
            import flask
            print("✅ Flask: 已安装")
        except ImportError:
            print("❌ Flask: 未安装")

        try:
            import requests
            print("✅ Requests: 已安装")
        except ImportError:
            print("❌ Requests: 未安装")

        return has_gui

    except Exception as e:
        print(f"❌ 环境检测失败: {e}")
        return False

def test_gui_mode():
    """测试GUI模式"""
    print("\n🖥️ 测试GUI模式...")

    try:
        from feedback_ui import feedback_ui

        prompt = """
# 🍎 Apple风格GUI测试

欢迎使用全新的 **Apple风格** 反馈界面！

## ✨ 测试项目
- **🎨 界面美观度**：Apple设计风格
- **📝 字体渲染**：SF Pro字体系统
- **🔵 交互效果**：按钮悬停和点击
- **⌨️ 快捷键**：Ctrl+Enter 提交，Alt+C 插入代码

## 💻 代码示例
```python
def apple_style_test():
    return "🍎 Beautiful Apple UI"
```

请测试界面功能并提供反馈！
"""

        options = [
            "🎨 界面非常美观",
            "📱 很有Apple风格",
            "🚀 交互体验流畅",
            "💡 还有改进空间"
        ]

        print("💡 GUI窗口即将打开，请在界面中完成测试...")
        result = feedback_ui(prompt, options)
        print(f"✅ GUI测试完成，用户反馈: {result}")
        return True

    except Exception as e:
        print(f"❌ GUI测试失败: {e}")
        return False

def test_web_mode():
    """测试Web模式"""
    print("\n🌐 测试Web模式...")

    try:
        from web_ui import WebFeedbackUI
        import requests

        prompt = """
# 🌐 Web界面测试

这是Web模式的反馈界面测试。

## 测试功能
- **响应式设计**：适配不同屏幕
- **API接口**：前后端通信
- **实时渲染**：Markdown支持
- **交互体验**：与GUI版本一致
- **持续模式**：页面保持打开，实时更新内容

请在浏览器中测试各项功能！
"""

        options = ["Web界面正常", "功能完整", "需要优化", "测试持续模式"]

        print("选择测试模式:")
        print("1. 单次模式（提交后关闭）")
        print("2. 持续模式（保持打开，可实时更新）")
        print("3. 持续模式无内容测试（测试自动关闭）")
        choice = input("请选择 (1/2/3): ").strip()

        persistent = choice in ["2", "3"]
        no_content_test = choice == "3"

        if no_content_test:
            mode_text = "持续模式无内容测试"
            # 无内容测试：启动时就没有内容
            web_ui = WebFeedbackUI("", [], host="127.0.0.1", port=8080, persistent=True)
        else:
            mode_text = "持续模式" if persistent else "单次模式"
            # 正常测试：有初始内容
            web_ui = WebFeedbackUI(prompt, options, host="127.0.0.1", port=8080, persistent=persistent)

        print(f"🔧 启动{mode_text}测试...")

        def run_server():
            return web_ui.run()

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        # 等待服务器启动
        time.sleep(2)

        # 测试API接口
        try:
            response = requests.get("http://127.0.0.1:8080/api/config", timeout=5)
            if response.status_code == 200:
                config = response.json()
                print("✅ Web API测试成功")
                print(f"📋 持续模式: {config.get('persistent', False)}")
            else:
                print(f"❌ Web API测试失败: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Web API连接失败: {e}")

        print(f"🌐 Web服务器已启动: http://127.0.0.1:8080")
        print(f"💡 请在浏览器中打开上述地址进行{mode_text}测试")

        if no_content_test:
            print("🔄 持续模式无内容测试流程:")
            print("   1. 页面应显示'无有效内容'")
            print("   2. 页面应在3秒后自动关闭（非持续模式行为）")
            print("   3. 或显示关闭按钮供手动关闭")
            print("💡 此测试验证：没有内容时持续模式的正确行为")

            # 无内容测试不需要等待用户反馈，只需要验证页面行为
            print("\n⏳ 请在浏览器中观察页面行为...")
            print("   - 如果是非持续模式逻辑：页面会自动关闭")
            print("   - 如果是持续模式逻辑：页面会显示关闭按钮")

            input("按Enter键结束无内容测试...")
            return True

        elif persistent:
            print("🔄 持续模式测试流程:")
            print("   1. 在浏览器中提交第一次反馈")
            print("   2. 页面应显示'无有效内容'并等待")
            print("   3. 测试程序将推送新内容")
            print("   4. 页面应自动更新显示新内容")
            print("   5. 提交第二次反馈完成测试")
        else:
            print("⏳ 单次模式：提交反馈后页面会自动关闭")

        # 等待用户第一次反馈
        print("\n⏳ 请在浏览器中提交第一次反馈...")

        # 轮询等待反馈结果
        feedback_received = False
        for i in range(60):  # 等待最多60秒
            if web_ui.feedback_result:
                feedback_received = True
                print(f"✅ 收到用户反馈: {web_ui.feedback_result['cursor_usage_opt']}")
                break
            time.sleep(1)

        if not feedback_received:
            print("⚠️ 未收到用户反馈，跳过后续测试")
            return False

        # 如果是持续模式，测试内容更新功能
        if persistent:
            print("\n🔄 测试持续模式内容更新...")

            # 推送新内容
            new_prompt = """
# 🆕 内容已更新！

这是通过持续模式推送的新内容。

## 验证项目
- ✅ 页面是否自动显示新内容
- ✅ 提交按钮是否重新启用
- ✅ 是否收到更新提示

## 测试完成
请提交此反馈以完成持续模式测试。
"""

            new_options = ["新内容显示正常", "按钮重新启用", "持续模式完美", "测试完成"]

            web_ui.update_content(new_prompt, new_options)
            print("📝 新内容已推送到页面")
            print("💡 请在浏览器中查看更新效果并提交第二次反馈")

            # 等待第二次反馈
            web_ui.feedback_result = None  # 重置反馈结果
            second_feedback_received = False

            for i in range(60):  # 等待最多60秒
                if web_ui.feedback_result:
                    second_feedback_received = True
                    print(f"✅ 收到第二次反馈: {web_ui.feedback_result['cursor_usage_opt']}")
                    break
                time.sleep(1)

            if second_feedback_received:
                print("🎉 持续模式测试完成！")
            else:
                print("⚠️ 未收到第二次反馈")

            # 清空内容结束测试
            web_ui.update_content("", [])
            print("🔚 测试结束，已清空内容")

        print(f"✅ {mode_text}测试完成")
        return True

    except Exception as e:
        print(f"❌ Web测试失败: {e}")
        return False



def test_mcp_server():
    """测试MCP服务器功能"""
    print("\n🔧 测试MCP服务器...")

    try:
        from server import launch_feedback_ui

        print("💡 测试MCP工具调用...")

        message = "这是MCP服务器功能测试，请确认收到此消息。"
        options = ["收到消息", "功能正常", "测试完成"]

        print("🚀 MCP工具即将启动，请完成交互...")
        result = launch_feedback_ui(message, options)
        print(f"✅ MCP测试完成，结果: {result}")

        # 测试文件输出
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_file = f.name

        test_result = {"cursor_usage_opt": "文件输出测试"}
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(test_result, f, ensure_ascii=False, indent=2)

        with open(output_file, 'r', encoding='utf-8') as f:
            loaded_result = json.load(f)

        if loaded_result == test_result:
            print("✅ 文件输出测试成功")
        else:
            print("❌ 文件输出测试失败")

        os.unlink(output_file)
        return True

    except Exception as e:
        print(f"❌ MCP测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 Cursor Usage Opt MCP 综合测试")
    print("=" * 50)

    # 环境检测
    has_gui = test_environment()

    print("\n📋 可用测试:")
    print("┌─────────────────────────────────────────────┐")
    if has_gui:
        print("│  1. 🖥️  GUI模式测试 (推荐)                │")
    else:
        print("│  1. 🖥️  GUI模式测试 (需要图形界面)        │")
    print("│  2. 🌐  Web模式测试                        │")
    print("│  3. 🔧  MCP服务器测试                      │")
    print("│  4. 🚀  运行所有测试                       │")
    print("│  0. 🚪  退出                              │")
    print("└─────────────────────────────────────────────┘")

    while True:
        try:
            choice = input("\n请选择测试 (0-4): ").strip()

            if choice == "0":
                print("👋 退出测试")
                break
            elif choice == "1":
                if has_gui:
                    test_gui_mode()
                else:
                    print("❌ 当前环境不支持GUI，请在图形界面环境中运行")
            elif choice == "2":
                test_web_mode()
            elif choice == "3":
                test_mcp_server()
            elif choice == "4":
                print("\n🚀 运行所有测试...")
                success_count = 0
                total_tests = 3

                if has_gui and test_gui_mode():
                    success_count += 1
                elif not has_gui:
                    print("⏭️ 跳过GUI测试（无图形界面）")
                    total_tests -= 1

                if test_web_mode():
                    success_count += 1

                if test_mcp_server():
                    success_count += 1

                print(f"\n📊 测试完成: {success_count}/{total_tests} 通过")
                if success_count == total_tests:
                    print("🎉 所有测试通过！")
                else:
                    print("⚠️ 部分测试失败，请检查错误信息")
                break
            else:
                print("❌ 无效选择，请输入 0-4")

        except KeyboardInterrupt:
            print("\n👋 测试被中断")
            break
        except Exception as e:
            print(f"❌ 测试出错: {e}")

if __name__ == "__main__":
    main()
