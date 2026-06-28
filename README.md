# Paster — 模拟键盘逐字输入

绕过不允许复制粘贴的文本框 / 在线编译器。

用纯 ctypes SendInput API 实现逐字符键盘模拟，从剪贴板读取内容后逐字输入到目标窗口。支持文本模式和代码模式（自动 strip 行首缩进），不会被检测为粘贴行为。

## 功能

- **文本模式** — 原样输出所有字符（中英文、数字、符号）
- **代码模式** — 自动去除行首空格，适合粘贴到在线编译器（让 IDE 自动缩进）
- 读剪贴板：自动读取剪贴板，输出内容交给程序自己输入，且不会改变输入法状态
- 快捷键 **Ctrl+Shift+V** 立即开始，不等倒计时
- **Ctrl+Shift+P** 暂停/继续
- 可调字符延迟 / 回车额外延迟 / 等待倒计时
- 窗口置顶，深色主题中文 UI

## 安装和使用

### 方法一：直接运行 Python 脚本

```bash
git clone https://github.com/SillyJay/paster-keyboard-simulator.git
cd paster-keyboard-simulator
pip install pyperclip keyboard
python Paster.py
```

### 方法二：打包为独立 exe（不需要 Python 环境）

以管理员身份运行 `build_exe.bat`，完成后 `dist\Paster.exe` 可直接发给其他 Windows 用户双击运行。

## 使用说明

1. 复制你要输入的文本到剪贴板
2. 打开 Paster，选择模式（文本/代码）
3. 调整延迟参数（可选）
4. 点击「开始粘贴」或按 Ctrl+Shift+V
5. 将光标聚焦到目标输入框，等待倒计时结束后自动逐字输入
6. 可随时暂停或停止

## 技术实现

- 纯 ctypes `SendInput` API 发送按键（无需 `pynput`）
- 文字：`KEYEVENTF_UNICODE` 通道
- 回车/Tab/空格：`VK_ENTER` / `VK_TAB` / `VK_SPACE` 虚拟键
- Tkinter 深色 UI + Canvas 圆角按钮
- 独立线程输入，不阻塞 UI

## 依赖

- `pyperclip` — 读取系统剪贴板
- `keyboard` — 注册全局快捷键
- Python 3.9+ 标准库：`tkinter`, `ctypes`, `threading`

## License

MIT
