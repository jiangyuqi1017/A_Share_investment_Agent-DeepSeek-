# API Provider Configuration Guide

## 🚀 Quick Setup

The system now supports any OpenAI-compatible API. Here's how to configure different providers:

### 1. **OpenAI** (Recommended for beginners)
```bash
# .env file
API_KEY=sk-your-openai-api-key-here
API_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-3.5-turbo
API_PROVIDER=openai
```

**Models available:**
- `gpt-3.5-turbo` (Fastest, cheapest)
- `gpt-4` (Better quality)
- `gpt-4-turbo` (Latest GPT-4)
- `gpt-4o` (Multimodal)

**Get API Key:** [OpenAI Platform](https://platform.openai.com/api-keys)

### 2. **DeepSeek** (Chinese AI, very cost-effective)
```bash
# .env file
API_KEY=sk-your-deepseek-api-key-here
API_BASE_URL=https://api.deepseek.com
MODEL_NAME=deepseek-chat
API_PROVIDER=deepseek
```

**Models available:**
- `deepseek-chat` (General purpose)
- `deepseek-coder` (Code-specialized)

**Get API Key:** [DeepSeek Platform](https://platform.deepseek.com/api-keys)

### 3. **SiliconFlow** (Chinese AI platform, very competitive pricing)
```bash
# .env file
API_KEY=sk-your-siliconflow-api-key-here
API_BASE_URL=https://api.siliconflow.cn/v1
MODEL_NAME=deepseek-ai/DeepSeek-V2.5
API_PROVIDER=siliconflow
```

**Models available:**
- `deepseek-ai/DeepSeek-V2.5` (Advanced reasoning)
- `Qwen/Qwen2.5-7B-Instruct` (Alibaba's model)
- `Qwen/Qwen2.5-72B-Instruct` (Large Qwen model)
- `meta-llama/Meta-Llama-3.1-70B-Instruct` (Meta's latest)
- `01-ai/Yi-1.5-34B-Chat-16K` (Zero One AI)

**Get API Key:** [SiliconFlow Cloud](https://cloud.siliconflow.cn/account/ak)

### 4. **Anthropic Claude** (via OpenAI-compatible wrapper)
```bash
# .env file
API_KEY=sk-ant-your-anthropic-key-here
API_BASE_URL=https://api.anthropic.com/v1  # If using compatible wrapper
MODEL_NAME=claude-3-sonnet-20240229
API_PROVIDER=anthropic
```

**Note:** You may need to use a wrapper service or wait for Anthropic's OpenAI-compatible endpoint.

### 5. **Local Models** (Ollama - Free!)
```bash
# First install Ollama: https://ollama.ai/
# Then: ollama pull llama2

# .env file
API_KEY=ollama
API_BASE_URL=http://localhost:11434/v1
MODEL_NAME=llama2
API_PROVIDER=ollama
```

**Popular models:**
- `llama2` (7B/13B/70B)
- `codellama` (Code specialist)
- `mistral` (Fast and good)
- `yi` (Chinese-friendly)

### 6. **Together AI** (Many open-source models)
```bash
# .env file
API_KEY=your-together-api-key
API_BASE_URL=https://api.together.xyz/v1
MODEL_NAME=meta-llama/Llama-2-7b-chat-hf
API_PROVIDER=together
```

**Get API Key:** [Together AI](https://api.together.xyz/settings/api-keys)

### 7. **Groq** (Extremely fast inference)
```bash
# .env file
API_KEY=gsk_your-groq-api-key
API_BASE_URL=https://api.groq.com/openai/v1
MODEL_NAME=mixtral-8x7b-32768
API_PROVIDER=groq
```

**Get API Key:** [Groq Console](https://console.groq.com/keys)

### 8. **OpenRouter** (Access to many models)
```bash
# .env file
API_KEY=sk-or-your-openrouter-key
API_BASE_URL=https://openrouter.ai/api/v1
MODEL_NAME=anthropic/claude-3-sonnet
API_PROVIDER=openrouter
```

**Get API Key:** [OpenRouter](https://openrouter.ai/keys)

## 🔧 Programmatic Configuration

You can also configure providers directly in Python:

```python
from src.tools.openrouter_config import setup_provider

# Quick setup for OpenAI
setup_provider("openai", "sk-your-key", "gpt-4")

# Quick setup for local Ollama
setup_provider("ollama", "ollama", "llama2")

# Quick setup for DeepSeek
setup_provider("deepseek", "sk-your-deepseek-key", "deepseek-chat")

# Quick setup for SiliconFlow
setup_provider("siliconflow", "sk-your-siliconflow-key", "deepseek-ai/DeepSeek-V2.5")
```

## 💡 Advanced Configuration

### Custom Parameters

You can pass additional parameters to the API:

```python
from src.tools.openrouter_config import get_chat_completion

# With custom parameters
response = get_chat_completion(
    messages=[{"role": "user", "content": "Analyze this stock"}],
    model="gpt-4",
    temperature=0.7,        # Creativity level
    max_tokens=1000,        # Response length limit
    top_p=0.9,             # Nucleus sampling
    frequency_penalty=0.1   # Avoid repetition
)
```

### Environment Variables for Advanced Settings

```bash
# .env file
API_TIMEOUT=30
MAX_RETRIES=3
RATE_LIMIT=60
DEBUG_LOGGING=true
CUSTOM_HEADERS={"User-Agent": "AI-Investment-System/1.0"}
```

## 🔍 Testing Your Configuration

After setting up your `.env` file, test the configuration:

```python
# test_api.py
from src.tools.openrouter_config import get_chat_completion

def test_api():
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello! Please respond with 'API working correctly.'"}
    ]
    
    response = get_chat_completion(messages)
    print(f"Response: {response}")
    
    if response and "API working correctly" in response:
        print("✅ API configuration is working!")
    else:
        print("❌ API configuration issue")

if __name__ == "__main__":
    test_api()
```

Run the test:
```bash
python test_api.py
```

## 🚨 Troubleshooting

### Common Issues

1. **API Key Invalid**
   ```
   Error: Invalid API key
   Solution: Double-check your API key in .env file
   ```

2. **Model Not Found**
   ```
   Error: Model not found
   Solution: Check if model name is correct for your provider
   ```

3. **Connection Timeout**
   ```
   Error: Connection timeout
   Solution: Check API_BASE_URL and network connection
   ```

4. **Rate Limit Exceeded**
   ```
   Error: Rate limit exceeded
   Solution: Wait or upgrade your API plan
   ```

### Debug Mode

Enable detailed logging:
```bash
# Add to .env
DEBUG_LOGGING=true
```

This will show:
- All API requests and responses
- Retry attempts
- Error details
- Performance metrics

## 💰 Cost Comparison

| Provider | Model | Cost (per 1M tokens) | Speed | Quality |
|----------|-------|---------------------|-------|---------|
| OpenAI | gpt-3.5-turbo | $0.50 | Fast | Good |
| OpenAI | gpt-4 | $30.00 | Medium | Excellent |
| DeepSeek | deepseek-chat | $0.14 | Fast | Very Good |
| SiliconFlow | DeepSeek-V2.5 | $0.07 | Fast | Very Good |
| SiliconFlow | Qwen2.5-72B | $0.50 | Medium | Excellent |
| Groq | mixtral-8x7b | $0.27 | Very Fast | Good |
| Together | llama-2-7b | $0.20 | Fast | Good |
| Ollama | llama2 | Free | Medium | Good |

**Recommendation:** Start with SiliconFlow for maximum cost-effectiveness, DeepSeek for reliability, or OpenAI GPT-3.5 for proven stability.

## 🔄 Migration from Old Version

If you're upgrading from the DeepSeek-only version:

1. **Keep existing config** (will work automatically):
   ```bash
   DEEP_SEEK_API_KEY=sk-your-deepseek-key
   DEEP_SEEK_MODEL=deepseek-chat
   ```

2. **Or migrate to new format**:
   ```bash
   API_KEY=sk-your-deepseek-key
   API_BASE_URL=https://api.deepseek.com
   MODEL_NAME=deepseek-chat
   API_PROVIDER=deepseek
   ```

## 🎯 Recommendations by Use Case

### **For Learning/Testing**
- **Ollama** (Free, runs locally)
- Models: `llama2`, `mistral`

### **For Production (English)**
- **OpenAI GPT-3.5-turbo** (Reliable, fast)
- **Groq Mixtral** (Very fast, good quality)

### **For Production (Chinese)**
- **SiliconFlow** (Most cost-effective, excellent Chinese support)
- **DeepSeek** (Good Chinese understanding, reliable)
- **OpenAI GPT-4** (Excellent but expensive)

### **For Experimentation**
- **OpenRouter** (Access to many models)
- **Together AI** (Many open-source options)

### **For Speed**
- **Groq** (Fastest inference)
- **Together AI** (Fast open-source models)

### **For Cost**
- **SiliconFlow** (Cheapest quality option at $0.07/1M tokens)
- **DeepSeek** (Good balance of cost and quality)
- **Ollama** (Free, but requires local setup)

## 📝 Example Complete Setup

Here's a complete example for setting up with SiliconFlow (most cost-effective):

1. **Get API Key:** Go to [SiliconFlow Cloud](https://cloud.siliconflow.cn/account/ak)

2. **Create .env file:**
   ```bash
   API_KEY=sk-your-actual-siliconflow-key-here
   API_BASE_URL=https://api.siliconflow.cn/v1
   MODEL_NAME=deepseek-ai/DeepSeek-V2.5
   API_PROVIDER=siliconflow
   ```

3. **Test the system:**
   ```bash
   python src/main.py --ticker 600519 --show-reasoning
   ```

4. **Expected output:**
   ```
   ✓ 已加载环境变量: /path/to/.env
   ✓ API配置:
     提供商: siliconflow
     基础URL: https://api.siliconflow.cn/v1
     模型: deepseek-ai/DeepSeek-V2.5
   ✓ OpenAI兼容客户端初始化成功
   
   正在获取 600519 的历史行情数据...
   # ... analysis continues
   ```

The system is now flexible enough to work with any OpenAI-compatible API while maintaining backward compatibility with the original DeepSeek configuration!