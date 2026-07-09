# 启动命令

## Linux

在 WSL 中，使用 conda 环境 `mingjing` 启动：

```powershell
wsl
conda activate mingjing
```

首次运行前需要安装后端依赖（在 WSL + conda 环境 `mingjing` 中）：

```powershell
cd /mnt/d/personal/project/260504_aidoll/260504_aidoll_t_web/server
pip install -r requirements.txt
```

运行启动前后端：

```powershell
npm run dev
cd server && python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## 板子烧录 / 监听

以下命令在 `firmware/` 目录下执行，且需先激活 ESP-IDF 环境：

```powershell
cd firmware
& "$env:IDF_PATH\export.ps1"
# 编译、烧录固件并打开串口监视：
idf.py -p COM5 flash monitor
# 单监听（仅串口监视，不烧录）
idf.py -p COM5 monitor
```

退出串口监视：`Ctrl + ]`。
