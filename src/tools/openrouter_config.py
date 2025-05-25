import os
import time
import logging
from dotenv import load_dotenv
from dataclasses import dataclass
import backoff
from openai import OpenAI

# 初始化日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.handlers.clear()  # 清除所有现有处理器

# 创建日志目录
log_dir = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), 'logs')
os.makedirs(log_dir, exist_ok=True)

# 设置文件处理器
log_file = os.path.join(log_dir, f'api_calls_{time.strftime("%Y%m%d")}.log')
logger.debug(f"Creating log file at: {log_file}")

try:
    file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='a')
    file_handler.setLevel(logging.DEBUG)
    logger.debug("Successfully created file handler")
except Exception as e:
    logger.error(f"Error creating file handler: {str(e)}")

# 设置控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# 设置日志格式
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 添加处理器
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# 立即测试日志记录
logger.debug("Logger initialization completed")
logger.info("API logging system started")

# 状态图标
SUCCESS_ICON = "✓"
ERROR_ICON = "✗"
WAIT_ICON = "⟳"


@dataclass
class ChatMessage:
    content: str


@dataclass
class ChatChoice:
    message: ChatMessage


@dataclass
class ChatCompletion:
    choices: list[ChatChoice]


# 获取项目根目录
project_root = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(project_root, '.env')

# 加载环境变量
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)
    logger.info(f"{SUCCESS_ICON} 已加载环境变量: {env_path}")
else:
    logger.warning(f"{ERROR_ICON} 未找到环境变量文件: {env_path}")

# 获取API配置 - 支持多种API提供商
api_key = os.getenv("API_KEY")
api_base_url = os.getenv("API_BASE_URL", "https://api.openai.com/v1")  # 默认OpenAI
model_name = os.getenv("MODEL_NAME", "gpt-3.5-turbo")  # 默认模型
api_provider = os.getenv("API_PROVIDER", "openai")  # API提供商标识

# 向后兼容 - 如果还在使用旧的DeepSeek环境变量
if not api_key and os.getenv("DEEP_SEEK_API_KEY"):
    api_key = os.getenv("DEEP_SEEK_API_KEY")
    api_base_url = "https://api.deepseek.com"
    model_name = os.getenv("DEEP_SEEK_MODEL", "deepseek-chat")
    api_provider = "deepseek"
    logger.info("Using legacy DeepSeek configuration")

# 验证必需的环境变量
if not api_key:
    logger.error("未找到 API_KEY 环境变量")
    raise ValueError("API_KEY not found in environment variables. Please set API_KEY in your .env file")

if not model_name:
    logger.error("未找到 MODEL_NAME 环境变量")
    raise ValueError("MODEL_NAME not found in environment variables. Please set MODEL_NAME in your .env file")

logger.info(f"{SUCCESS_ICON} API配置:")
logger.info(f"  提供商: {api_provider}")
logger.info(f"  基础URL: {api_base_url}")
logger.info(f"  模型: {model_name}")

# 初始化 OpenAI 客户端（支持任何OpenAI兼容的API）
try:
    client = OpenAI(
        api_key=api_key,
        base_url=api_base_url
    )
    logger.info(f"{SUCCESS_ICON} OpenAI兼容客户端初始化成功")
except Exception as e:
    logger.error(f"{ERROR_ICON} 客户端初始化失败: {str(e)}")
    raise


# 根据不同API提供商配置重试策略
def get_retry_config():
    """根据API提供商返回相应的重试配置"""
    if api_provider.lower() == "deepseek":
        return {
            "max_tries": 5,
            "max_time": 300,
            "giveup": lambda e: "AFC is enabled" not in str(e)
        }
    elif api_provider.lower() == "openai":
        return {
            "max_tries": 3,
            "max_time": 120,
            "giveup": lambda e: "rate_limit_exceeded" not in str(e).lower()
        }
    elif api_provider.lower() == "anthropic":
        return {
            "max_tries": 3,
            "max_time": 120,
            "giveup": lambda e: "rate_limit" not in str(e).lower()
        }
    else:
        # 通用配置
        return {
            "max_tries": 3,
            "max_time": 120,
            "giveup": lambda e: False  # 总是重试
        }


@backoff.on_exception(
    backoff.expo,
    (Exception),
    **get_retry_config()
)
def generate_content_with_retry(model, messages, config=None):
    """带重试机制的内容生成函数"""
    try:
        logger.info(f"{WAIT_ICON} 正在调用 {api_provider} API...")
        logger.info(f"模型: {model}")
        logger.info(f"请求内容: {messages}")
        logger.info(f"请求配置: {config}")

        # 构建请求参数
        request_params = {
            "model": model,
            "messages": messages
        }
        
        # 添加额外配置
        if config:
            request_params.update(config)

        response = client.chat.completions.create(**request_params)

        logger.info(f"{SUCCESS_ICON} API 调用成功")
        logger.info(f"响应内容: {response.choices[0].message.content[:500]}..." if len(
            response.choices[0].message.content) > 500 else f"响应内容: {response.choices[0].message.content}")
        return response
    except Exception as e:
        error_msg = str(e).lower()
        
        # 根据不同提供商的错误信息判断是否需要重试
        should_retry = False
        if api_provider.lower() == "deepseek" and "afc is enabled" in error_msg:
            should_retry = True
            wait_time = 5
        elif "rate_limit" in error_msg or "429" in error_msg:
            should_retry = True
            wait_time = 10
        elif "timeout" in error_msg or "connection" in error_msg:
            should_retry = True
            wait_time = 3
        
        if should_retry:
            logger.warning(f"{ERROR_ICON} API限制或网络错误，等待重试... 错误: {str(e)}")
            time.sleep(wait_time)
            raise e
        else:
            logger.error(f"{ERROR_ICON} API 调用失败: {str(e)}")
            raise e


def get_chat_completion(messages, model=None, max_retries=3, initial_retry_delay=1, **kwargs):
    """获取聊天完成结果，支持任何OpenAI兼容API
    
    Args:
        messages: 消息列表
        model: 模型名称（可选，默认使用环境变量中的模型）
        max_retries: 最大重试次数
        initial_retry_delay: 初始重试延迟
        **kwargs: 传递给API的额外参数（如temperature, max_tokens等）
    
    Returns:
        str: API响应的文本内容
    """
    try:
        if model is None:
            model = model_name

        logger.info(f"{WAIT_ICON} 使用模型: {model}")
        logger.debug(f"消息内容: {messages}")

        for attempt in range(max_retries):
            try:
                # 转换消息格式
                formatted_messages = []
                for message in messages:
                    role = message["role"]
                    content = message["content"]
                    formatted_messages.append({
                        "role": role,
                        "content": content
                    })

                # 准备API调用配置
                api_config = {}
                if kwargs:
                    api_config.update(kwargs)

                # 调用 API
                response = generate_content_with_retry(
                    model=model,
                    messages=formatted_messages,
                    config=api_config
                )

                if response is None:
                    logger.warning(
                        f"{ERROR_ICON} 尝试 {attempt + 1}/{max_retries}: API 返回空值")
                    if attempt < max_retries - 1:
                        retry_delay = initial_retry_delay * (2 ** attempt)
                        logger.info(f"{WAIT_ICON} 等待 {retry_delay} 秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    return None

                # 转换响应格式
                chat_message = ChatMessage(content=response.choices[0].message.content)
                chat_choice = ChatChoice(message=chat_message)
                completion = ChatCompletion(choices=[chat_choice])

                logger.debug(f"API 原始响应: {response.choices[0].message.content}")
                logger.info(f"{SUCCESS_ICON} 成功获取响应")
                return completion.choices[0].message.content

            except Exception as e:
                logger.error(
                    f"{ERROR_ICON} 尝试 {attempt + 1}/{max_retries} 失败: {str(e)}")
                if attempt < max_retries - 1:
                    retry_delay = initial_retry_delay * (2 ** attempt)
                    logger.info(f"{WAIT_ICON} 等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"{ERROR_ICON} 最终错误: {str(e)}")
                    return None

    except Exception as e:
        logger.error(f"{ERROR_ICON} get_chat_completion 发生错误: {str(e)}")
        return None


# 为不同API提供商提供便捷函数
def get_openai_completion(messages, model="gpt-3.5-turbo", **kwargs):
    """OpenAI API调用"""
    return get_chat_completion(messages, model=model, **kwargs)


def get_anthropic_completion(messages, model="claude-3-sonnet-20240229", **kwargs):
    """Anthropic Claude API调用（通过OpenAI格式）"""
    return get_chat_completion(messages, model=model, **kwargs)


def get_deepseek_completion(messages, model="deepseek-chat", **kwargs):
    """DeepSeek API调用"""
    return get_chat_completion(messages, model=model, **kwargs)


def get_local_completion(messages, model="llama2", **kwargs):
    """本地模型调用（如Ollama）"""
    return get_chat_completion(messages, model=model, **kwargs)


def get_siliconflow_completion(messages, model="deepseek-ai/DeepSeek-V2.5", **kwargs):
    """SiliconFlow API调用"""
    return get_chat_completion(messages, model=model, **kwargs)


# 提供商配置模板
PROVIDER_CONFIGS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"],
        "default_model": "gpt-3.5-turbo"
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "models": ["deepseek-chat", "deepseek-coder"],
        "default_model": "deepseek-chat"
    },
    "siliconflow": {
        "base_url": "https://api.siliconflow.cn/v1",
        "models": [
            "deepseek-ai/DeepSeek-V3",
            "deepseek-ai/DeepSeek-R1",
            "Qwen/Qwen3-32B",
            "Qwen/Qwen3-30B-A3B", 
            "Qwen/Qwen3-14B", 
            "Qwen/Qwen3-8B", 
            "Qwen/Qwen3-235B-A22B"
        ],
        "default_model": "deepseek-ai/DeepSeek-V3"
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1",  # 如果有OpenAI兼容端点
        "models": ["claude-3-sonnet-20240229", "claude-3-opus-20240229"],
        "default_model": "claude-3-sonnet-20240229"
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "models": ["llama2", "codellama", "mistral"],
        "default_model": "llama2"
    },
    "together": {
        "base_url": "https://api.together.xyz/v1",
        "models": ["meta-llama/Llama-2-7b-chat-hf", "meta-llama/Llama-2-13b-chat-hf"],
        "default_model": "meta-llama/Llama-2-7b-chat-hf"
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "models": ["mixtral-8x7b-32768", "llama2-70b-4096"],
        "default_model": "mixtral-8x7b-32768"
    }
}


def setup_provider(provider_name, api_key, model=None):
    """快速设置API提供商"""
    if provider_name not in PROVIDER_CONFIGS:
        raise ValueError(f"不支持的提供商: {provider_name}. 支持的提供商: {list(PROVIDER_CONFIGS.keys())}")
    
    config = PROVIDER_CONFIGS[provider_name]
    
    # 更新环境变量
    os.environ["API_KEY"] = api_key
    os.environ["API_BASE_URL"] = config["base_url"]
    os.environ["API_PROVIDER"] = provider_name
    os.environ["MODEL_NAME"] = model or config["default_model"]
    
    logger.info(f"{SUCCESS_ICON} 已设置API提供商: {provider_name}")
    logger.info(f"  模型: {os.environ['MODEL_NAME']}")
    logger.info(f"  基础URL: {config['base_url']}")
    
    # 重新初始化客户端
    global client, api_provider, api_base_url, model_name
    api_provider = provider_name
    api_base_url = config["base_url"]
    model_name = os.environ["MODEL_NAME"]
    
    client = OpenAI(
        api_key=api_key,
        base_url=api_base_url
    )
    
    return client