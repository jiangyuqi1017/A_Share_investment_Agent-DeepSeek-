#!/bin/bash

# AI Investment System - Web Interface Launch Script
# This script sets up and launches the web interface

echo "🤖 AI投资决策系统 - Web界面启动脚本"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "src/main.py" ]; then
    print_error "请在项目根目录运行此脚本"
    print_info "期望找到 src/main.py 文件"
    exit 1
fi

print_status "找到项目结构"

# Check Python version
python_version=$(python3 --version 2>/dev/null || python --version 2>/dev/null)
if [ $? -eq 0 ]; then
    print_status "Python版本: $python_version"
else
    print_error "未找到Python安装"
    exit 1
fi

# Check if web_interface.py exists
if [ ! -f "web_interface.py" ]; then
    print_warning "未找到 web_interface.py 文件"
    print_info "请从artifacts复制Web界面代码并保存为 web_interface.py"
    
    read -p "是否现在创建模板文件? (y/N): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cat > web_interface.py << 'EOF'
#!/usr/bin/env python3
"""
请从AI助手的artifacts中复制完整的Web界面代码到此文件

Web界面代码位于 "AI Investment System Web Interface" artifact
"""

print("⚠️ 请复制完整的Web界面代码到此文件")
print("📋 代码位于助手回复中的 'AI Investment System Web Interface' artifact")

EOF
        print_status "已创建 web_interface.py 模板文件"
        print_info "请编辑此文件并粘贴完整的Web界面代码"
        exit 1
    else
        exit 1
    fi
fi

print_status "找到Web界面文件"

# Check .env file
if [ ! -f ".env" ]; then
    print_warning "未找到 .env 配置文件"
    print_info "请确保已配置API密钥"
    
    read -p "是否创建示例 .env 文件? (y/N): " -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cat > .env << 'EOF'
# AI Investment System API Configuration
# 请填入您的实际API配置

# SiliconFlow (推荐 - 最便宜)
API_KEY=sk-your-siliconflow-api-key-here
API_BASE_URL=https://api.siliconflow.cn/v1
MODEL_NAME=deepseek-ai/DeepSeek-V2.5
API_PROVIDER=siliconflow

# 或者使用其他提供商:
# OpenAI
# API_KEY=sk-your-openai-api-key
# API_BASE_URL=https://api.openai.com/v1
# MODEL_NAME=gpt-3.5-turbo
# API_PROVIDER=openai

EOF
        print_status "已创建示例 .env 文件"
        print_warning "请编辑 .env 文件并填入您的真实API密钥"
        print_info "然后重新运行此脚本"
        exit 1
    else
        exit 1
    fi
fi

print_status "找到配置文件"

# Check if required packages are installed
print_info "检查依赖包..."

# Check for streamlit
if python3 -c "import streamlit" 2>/dev/null || python -c "import streamlit" 2>/dev/null; then
    print_status "Streamlit 已安装"
else
    print_warning "Streamlit 未安装"
    print_info "正在安装 Streamlit..."
    
    if command -v pip3 &> /dev/null; then
        pip3 install streamlit plotly
    else
        pip install streamlit plotly
    fi
    
    if [ $? -eq 0 ]; then
        print_status "Streamlit 安装成功"
    else
        print_error "Streamlit 安装失败"
        exit 1
    fi
fi

# Check for plotly
if python3 -c "import plotly" 2>/dev/null || python -c "import plotly" 2>/dev/null; then
    print_status "Plotly 已安装"
else
    print_warning "Plotly 未安装"
    print_info "正在安装 Plotly..."
    
    if command -v pip3 &> /dev/null; then
        pip3 install plotly
    else
        pip install plotly
    fi
    
    if [ $? -eq 0 ]; then
        print_status "Plotly 安装成功"
    else
        print_error "Plotly 安装失败"
        exit 1
    fi
fi

# Check other required packages
required_packages=("pandas" "numpy" "akshare" "openai" "langchain_core" "langgraph")

for package in "${required_packages[@]}"; do
    if python3 -c "import $package" 2>/dev/null || python -c "import $package" 2>/dev/null; then
        print_status "$package 已安装"
    else
        print_warning "$package 未安装"
        print_info "请运行: pip install $package"
    fi
done

# Test API configuration
print_info "测试API配置..."

if [ -f "test_api_config.py" ]; then
    python3 test_api_config.py --show-config 2>/dev/null || python test_api_config.py --show-config 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_status "API配置测试通过"
    else
        print_warning "API配置可能有问题"
        print_info "建议运行: python test_api_config.py"
    fi
else
    print_warning "未找到API测试脚本"
fi

# Launch the web interface
print_info "启动Web界面..."
echo ""
echo "🌐 Web界面即将在浏览器中打开"
echo "📍 访问地址: http://localhost:8501"
echo ""
print_info "按 Ctrl+C 停止服务"
echo ""

# Try different Python commands
if command -v python &> /dev/null; then
    python -m streamlit run web_interface.py
elif command -v python &> /dev/null; then
    python -m streamlit run web_interface.py
else
    print_error "无法找到Python命令"
    exit 1
fi