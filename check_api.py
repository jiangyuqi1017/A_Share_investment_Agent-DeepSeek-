#!/usr/bin/env python3
"""
API配置快速检查脚本
运行这个脚本来诊断API配置问题
"""

import os
import sys
from pathlib import Path

# 添加src路径
sys.path.append(str(Path(__file__).parent / "src"))

def check_api_config():
    """检查API配置"""
    print("🔍 检查API配置...")
    
    # 检查环境变量
    required_vars = {
        'API_KEY': os.getenv('API_KEY'),
        'API_BASE_URL': os.getenv('API_BASE_URL'),
        'MODEL_NAME': os.getenv('MODEL_NAME'),
        'API_PROVIDER': os.getenv('API_PROVIDER')
    }
    
    print("\n📋 环境变量检查:")
    for var_name, var_value in required_vars.items():
        if var_value:
            if var_name == 'API_KEY':
                # 隐藏API密钥
                display_value = f"{var_value[:8]}...{var_value[-4:]}" if len(var_value) > 12 else "***"
            else:
                display_value = var_value
            print(f"✅ {var_name}: {display_value}")
        else:
            print(f"❌ {var_name}: 未设置")
    
    # 检查.env文件
    env_file = Path('.env')
    if env_file.exists():
        print(f"\n✅ 找到.env文件: {env_file.absolute()}")
    else:
        print(f"\n❌ 未找到.env文件: {env_file.absolute()}")
        return False
    
    # 测试API连接
    print("\n🧪 测试API连接...")
    try:
        from src.tools.openrouter_config import get_chat_completion
        
        test_messages = [
            {"role": "user", "content": "Hello, please respond with 'API test successful'"}
        ]
        
        response = get_chat_completion(test_messages)
        
        if response:
            print("✅ API连接成功")
            print(f"📝 响应: {response[:100]}...")
            return True
        else:
            print("❌ API连接失败：无响应")
            return False
            
    except Exception as e:
        print(f"❌ API连接失败: {str(e)}")
        return False

def suggest_fixes():
    """提供修复建议"""
    print("\n💡 修复建议:")
    print("""
1. 确保.env文件存在且包含正确的API配置
2. 检查API密钥是否有效（未过期、有足够余额）
3. 验证API_BASE_URL是否正确
4. 确认MODEL_NAME在API提供商中可用
5. 检查网络连接和防火墙设置
6. 重启程序或清除缓存

推荐配置示例 (.env文件):
API_KEY=sk-your-actual-api-key-here
API_BASE_URL=https://api.siliconflow.cn/v1
MODEL_NAME=deepseek-ai/DeepSeek-V2.5
API_PROVIDER=siliconflow
""")

if __name__ == "__main__":
    print("🤖 AI投资系统 - API配置诊断")
    print("=" * 50)
    
    success = check_api_config()
    
    if not success:
        suggest_fixes()
    else:
        print("\n🎉 API配置正常！可以正常使用Web界面。")
    
    print("\n" + "=" * 50)