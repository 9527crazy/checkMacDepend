#!/bin/bash
# Package Monitor Tauri 启动脚本
# 使用方法: ./run.sh

set -e

cd "$(dirname "$0")"

if ! command -v npm >/dev/null 2>&1; then
    echo "未找到 npm，请先安装 Node.js。"
    exit 1
fi

if ! command -v cargo >/dev/null 2>&1; then
    echo "未找到 cargo，请先安装 Rust: https://rustup.rs"
    exit 1
fi

if [ ! -d "node_modules" ]; then
    echo "正在安装前端依赖..."
    npm install
fi

echo "启动 Package Monitor..."
npm run tauri:dev
