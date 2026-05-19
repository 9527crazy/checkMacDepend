#!/bin/bash
# Package Monitor 启动脚本
# 使用方法: ./run.sh

cd "$(dirname "$0")"

# 如果 venv 不存在则创建
if [ ! -d "venv" ]; then
    echo "正在创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt --quiet
else
    source venv/bin/activate
fi

# 启动应用
echo "启动 Package Monitor..."
python3 main.py
