# 构建说明 — ESP-IDF (Windows)

此工程基于 ESP-IDF（Espressif IoT Development Framework）。下面给出在 Windows 上从零开始安装 ESP-IDF、配置环境、构建与刷写固件的快速步骤。

注意：以下命令基于 PowerShell（Windows）。如果遇到权限问题，请以管理员身份运行 PowerShell。

## 1) 推荐：使用 ESP-IDF Tools Installer（图形安装器）
- 官方安装器会自动安装 Python、工具链、OpenOCD 等。下载并运行官方 Windows Installer：
- 安装完成后打开 “ESP-IDF PowerShell” 或按照安装器说明运行 `export.ps1` 来导出环境变量。

官方下载页（示例）: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/ （请访问官方文档获取最新链接）

## 2) 手动安装（可选）
1. 克隆 ESP-IDF（示例安装到用户目录）：

```powershell
git clone --recursive https://github.com/espressif/esp-idf.git $env:USERPROFILE\esp\esp-idf
```

2. 设定 PowerShell 策略（仅需一次）：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

3. 运行安装脚本（这会安装 Python 包和工具链）：

```powershell
& "$env:USERPROFILE\esp\esp-idf\install.ps1"
```

4. 激活环境（每次新开启终端时执行，或在系统启动脚本中执行）：

```powershell
& "$env:USERPROFILE\esp\esp-idf\export.ps1"
# 或者使用环境变量已设置的路径：& "$env:IDF_PATH\export.ps1"
```

5. 验证安装：

```powershell
idf.py --version
python --version
```

## 3) 在项目里快速构建与刷写
进入本工程根目录（包含 `CMakeLists.txt` 的目录），然后：

```powershell
# 设置目标芯片（依据你的硬件，例如 esp32/esp32s3 等）
idf.py set-target esp32

# 配置（menuconfig 可选）
idf.py menuconfig

# 构建
idf.py build

# 刷写并打开串口监视（把 COM3 换成你的设备端口）
idf.py -p COM3 flash monitor
```

如何查找设备端口（PowerShell）：

```powershell
Get-WmiObject Win32_SerialPort | Select-Object DeviceID,Description
# 或者使用 Get-PnpDevice | Where-Object { $_.FriendlyName -Match "USB" }
```

常见 USB-UART 芯片：Silicon Labs CP210x、WCH CH340、FTDI。若 Windows 没识别，请安装相应驱动或在设备管理器中查看。

## 4) 常见问题与排查
- 权限/执行策略：若无法运行脚本，确认已执行 Set-ExecutionPolicy。  
- 串口占用：确保没有其它程序（如串口终端）占用 COM 口。  
- Python 依赖问题：运行 `& "$env:IDF_PATH\tools\idf_tools.py"` 或参考 install 输出修复。  
- 驱动问题：为 CP210x/CH340/FTDI 安装官方驱动。  
- 若 `idf.py` 未找到，确认 `export.ps1` 已运行并 IDF_PATH 被设置。

## 5) 本仓库注意事项
- 本工程的组件和源码在 `main/` 目录下，主要文件：`main.c`、`wifi.c`、`i2s_audio.c`、`websocket.c` 等。  
- 如果想要我直接帮你在当前机器上构建，请告诉我你已安装好 ESP-IDF 工具链或是否需要我引导安装中的某一步。

## 6) 推荐学习资源
- 官方文档（入门、API 参考、示例）: https://docs.espressif.com  
- 官方示例（esp-idf/examples）  
- 中文教程、视频与社区（B站/知乎/掘金）

---
快速开始小结：推荐先用官方 Tools Installer 安装，然后在 PowerShell 运行 `& "$env:IDF_PATH\export.ps1"`，接着在项目目录运行 `idf.py build` 与 `idf.py -p <COM> flash monitor`。

如果你愿意，我可以：
- 指导你一步步在你的 Windows 机器上安装（我会给出需要复制的 PowerShell 命令）；
- 或者继续在仓库里添加更多说明（例如常见依赖、目标芯片说明）。

欢迎告诉我你希望下一步我直接做什么。
