# 启动命令

## 前端

```powershell
pnpm dev
```

Vite 开发服务器，默认端口 `5173`。

## 后端

在 WSL 中，使用 conda 环境 `mingjing` 启动：

```bash
wsl
conda activate mingjing
cd /mnt/d/personal/project/260504_aidoll/260504_aidoll_t_web/server
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

FastAPI + uvicorn，默认端口 `8000`，带热重载。

首次运行前需要安装后端依赖（在 WSL + conda 环境 `mingjing` 中）：

```bash
cd /mnt/d/personal/project/260504_aidoll/260504_aidoll_t_web/server
pip install -r requirements.txt
```

## 板子烧录 / 监听

以下命令在 `firmware/` 目录下执行，且需先激活 ESP-IDF 环境：

```powershell
cd firmware
& "$env:IDF_PATH\export.ps1"
```

### 烧录 + 监听

编译、烧录固件并打开串口监视：

```powershell
idf.py -p COM5 flash monitor
# 单监听（仅串口监视，不烧录）
idf.py -p COM3 monitor
```

退出串口监视：`Ctrl + ]`。
