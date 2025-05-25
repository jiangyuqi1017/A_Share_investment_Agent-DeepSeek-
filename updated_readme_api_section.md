# API Configuration Guide

The system now supports **any OpenAI-compatible API**, giving you flexibility to choose the best provider for your needs.

## 🚀 Quick Setup

### Option 1: OpenAI (Recommended for beginners)
```bash
# 创建.env文件用于存储API密钥
cp .env.example .env

# 编辑.env文件，设置以下内容：
API_KEY=sk-your-openai-api-key-here
API_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-3.5-turbo
API_PROVIDER=openai
```

### Option 2: SiliconFlow (Most cost-effective, Chinese-friendly)
```bash
# 编辑.env文件，设置以下内容：
API_KEY=sk-your-siliconflow-api-key-here
API_BASE_URL=https://api.siliconflow.cn/v1
MODEL_NAME=deepseek-ai/DeepSeek-V2.5
API_PROVIDER=siliconflow
```

### Option 3: DeepSeek (Cost-effective, Chinese-friendly)
```bash
# 编辑.env文件，设置以下内容：
API_KEY=sk-your-deepseek-api-key-here
API_BASE_URL=https://api.deepseek.com
MODEL_NAME=deepseek-chat
API_PROVIDER=deepseek
```

### Option 4: Local Models (Free with Ollama)
```bash
# 首先安装Ollama: https://ollama.ai/
# 然后下载模型: ollama pull llama2

# 编辑.env文件，设置以下内容：
API_KEY=ollama
API_BASE_URL=http://localhost:11434/v1
MODEL_NAME=llama2
API_PROVIDER=ollama
```

### Option 5: Other Providers
The system supports any OpenAI-compatible API including:
- **Anthropic Claude** (via wrapper)
- **Together AI** (many open-source models)
- **Groq** (extremely fast inference)
- **OpenRouter** (access to multiple providers)
- **Azure OpenAI**
- **Custom endpoints**

## 📝 Getting API Keys

| Provider | Get API Key | Free Tier | Best For |
|----------|-------------|-----------|----------|
| [OpenAI](https://platform.openai.com/api-keys) | $5 credit | No | Reliability, English |
| [SiliconFlow](https://cloud.siliconflow.cn/account/ak) | ¥50 credit | Yes | Cost-effective, Chinese |
| [DeepSeek](https://platform.deepseek.com/api-keys) | ¥25 credit | Yes | Reliable, Chinese |
| [Ollama](https://ollama.ai/) | N/A | Yes | Privacy, No internet |
| [Together AI](https://api.together.xyz/settings/api-keys) | $5 credit | Yes | Open-source models |
| [Groq](https://console.groq.com/keys) | Free tier | Yes | Speed |
| [OpenRouter](https://openrouter.ai/keys) | $5 credit | Yes | Model variety |

## ⚙️ Environment Variables

Create a `.env` file in your project root with these variables:

```bash
# Required: Your API configuration
API_KEY=your-api-key-here
API_BASE_URL=https://api.provider.com/v1
MODEL_NAME=model-name
API_PROVIDER=provider-name

# Optional: Advanced settings
API_TIMEOUT=30
MAX_RETRIES=3
DEBUG_LOGGING=false
```

## 🔄 Backward Compatibility

If you're upgrading from the original DeepSeek-only version, your existing configuration will continue to work:

```bash
# Old format (still supported)
DEEP_SEEK_API_KEY=your-deepseek-api-key
DEEP_SEEK_MODEL=deepseek-chat
```

## 🧪 Testing Your Setup

Test your API configuration:

```bash
# Quick test
python -c "from src.tools.openrouter_config import get_chat_completion; print(get_chat_completion([{'role': 'user', 'content': 'Hello!'}]))"

# Full system test
python src/main.py --ticker 600519 --show-reasoning
```

## 💰 Cost Comparison

| Provider | Model | Cost (1M tokens) | Speed | Quality |
|----------|-------|------------------|-------|---------|
| OpenAI | gpt-3.5-turbo | $0.50 | ⚡⚡⚡ | ⭐⭐⭐ |
| OpenAI | gpt-4 | $30.00 | ⚡⚡ | ⭐⭐⭐⭐⭐ |
| SiliconFlow | DeepSeek-V2.5 | $0.07 | ⚡⚡⚡ | ⭐⭐⭐⭐ |
| DeepSeek | deepseek-chat | $0.14 | ⚡⚡⚡ | ⭐⭐⭐⭐ |
| Groq | mixtral-8x7b | $0.27 | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ |
| Ollama | llama2 | Free | ⚡⚡ | ⭐⭐⭐ |

**💡 Recommendation:** 
- **Learning/Testing:** Ollama (free)
- **Production:** SiliconFlow (most cost-effective) or OpenAI (reliable)
- **Speed critical:** Groq

## 🛠️ Advanced Configuration

### Custom Parameters
```python
from src.tools.openrouter_config import get_chat_completion

response = get_chat_completion(
    messages=[{"role": "user", "content": "Analyze AAPL"}],
    temperature=0.7,    # Creativity (0-1)
    max_tokens=1000,    # Response length
    top_p=0.9          # Nucleus sampling
)
```

### Provider Setup in Code
```python
from src.tools.openrouter_config import setup_provider

# Quick provider switch
setup_provider("openai", "sk-your-key", "gpt-4")
setup_provider("siliconflow", "sk-your-key", "deepseek-ai/DeepSeek-V2.5")
setup_provider("deepseek", "sk-your-key", "deepseek-chat")
setup_provider("ollama", "ollama", "llama2")
```

## 🔧 Troubleshooting

### Common Issues

**API Key Error:**
```bash
Error: API_KEY not found in environment variables
Solution: Check your .env file and ensure API_KEY is set
```

**Model Not Found:**
```bash
Error: Model not found
Solution: Verify MODEL_NAME is correct for your provider
```

**Connection Error:**
```bash
Error: Connection timeout
Solution: Check API_BASE_URL and internet connection
```

### Debug Mode
Enable detailed logging in your `.env`:
```bash
DEBUG_LOGGING=true
```

## 📚 Example Configurations

### Complete SiliconFlow Setup
```bash
# .env
API_KEY=sk-your-siliconflow-key-here
API_BASE_URL=https://api.siliconflow.cn/v1
MODEL_NAME=deepseek-ai/DeepSeek-V2.5
API_PROVIDER=siliconflow
```

### Complete OpenAI Setup
```bash
# .env
API_KEY=sk-proj-your-openai-key-here
API_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-3.5-turbo
API_PROVIDER=openai
```

### Complete DeepSeek Setup
```bash
# .env
API_KEY=sk-your-deepseek-key-here
API_BASE_URL=https://api.deepseek.com
MODEL_NAME=deepseek-chat
API_PROVIDER=deepseek
```

### Complete Local Setup
```bash
# First: Install Ollama and pull model
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama2

# .env
API_KEY=ollama
API_BASE_URL=http://localhost:11434/v1
MODEL_NAME=llama2
API_PROVIDER=ollama
```

Ready to start? Choose your provider, set up your `.env` file, and run your first analysis!