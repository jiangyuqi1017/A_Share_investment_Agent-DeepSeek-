#!/usr/bin/env python3
"""
AI Investment System - Web Interface
A comprehensive dashboard for stock analysis and investment decisions

Usage:
    streamlit run web_interface.py

Requirements:
    pip install streamlit plotly pandas numpy yfinance akshare
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import json
import sys
import os
from datetime import datetime, timedelta
import time
import warnings
import hashlib
from pathlib import Path
# 优化的翻译函数，支持并行处理
import concurrent.futures
import threading

warnings.filterwarnings('ignore')

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.main import run_hedge_fund
    from src.tools.api import get_price_history, get_financial_metrics, get_market_data
    from src.tools.news_crawler import get_stock_news, get_news_sentiment
    from src.tools.openrouter_config import logger
except ImportError as e:
    st.error(f"导入错误: {e}")
    st.error("请确保您在项目根目录运行此程序，并且已安装所有依赖")
    st.stop()

# Configure Streamlit page
st.set_page_config(
    page_title="AI投资决策系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 2px solid #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .signal-bullish {
        color: #00ff00;
        font-weight: bold;
    }
    .signal-bearish {
        color: #ff0000;
        font-weight: bold;
    }
    .signal-neutral {
        color: #ffa500;
        font-weight: bold;
    }
    .decision-buy {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
    }
    .decision-sell {
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
        padding: 1rem;
        margin: 1rem 0;
    }
    .decision-hold {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 在web_interface.py的导入部分添加
try:
    from src.tools.openrouter_config import get_chat_completion
    API_TRANSLATION_AVAILABLE = True
except ImportError:
    API_TRANSLATION_AVAILABLE = False
    print("警告：无法导入翻译API，将使用简单映射")

class TranslationCache:
    """翻译缓存管理器"""
    
    def __init__(self, cache_file="translation_cache.json"):
        self.cache_file = Path(cache_file)
        self.cache = self._load_cache()
    
    def _load_cache(self):
        """加载缓存"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载翻译缓存失败: {e}")
        return {}
    
    def _save_cache(self):
        """保存缓存"""
        try:
            # 确保目录存在
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存翻译缓存失败: {e}")
    
    def get_cache_key(self, text):
        """生成缓存键"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def get(self, text):
        """获取缓存的翻译"""
        cache_key = self.get_cache_key(text)
        return self.cache.get(cache_key)
    
    def set(self, text, translation):
        """设置缓存"""
        cache_key = self.get_cache_key(text)
        self.cache[cache_key] = {
            'translation': translation,
            'timestamp': time.time(),
            'original': text[:100]  # 存储原文前100字符用于调试
        }
        self._save_cache()

# 创建全局缓存实例
translation_cache = TranslationCache()

class TranslationManager:
    """翻译管理器，支持并行翻译和智能缓存"""
    
    def __init__(self):
        self.cache = TranslationCache()
        self.lock = threading.Lock()
    
    def translate_multiple(self, texts, max_workers=3):
        """并行翻译多个文本"""
        if not texts:
            return []
        
        results = [None] * len(texts)
        
        # 首先检查缓存
        uncached_indices = []
        for i, text in enumerate(texts):
            cached = self.cache.get(text)
            if cached:
                results[i] = cached['translation']
            else:
                uncached_indices.append(i)
        
        # 并行翻译未缓存的文本
        if uncached_indices:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_index = {
                    executor.submit(translate_with_api, texts[i]): i 
                    for i in uncached_indices
                }
                
                for future in concurrent.futures.as_completed(future_to_index):
                    index = future_to_index[future]
                    try:
                        translation = future.result(timeout=30)  # 30秒超时
                        results[index] = translation
                    except Exception as e:
                        print(f"并行翻译失败 (索引 {index}): {e}")
                        results[index] = translate_with_simple_mapping(texts[index])
        
        return results
    
    def translate_decision_batch(self, decision_data):
        """批量翻译决策相关内容"""
        texts_to_translate = []
        
        # 收集需要翻译的文本
        reasoning = decision_data.get('reasoning', '')
        if reasoning:
            texts_to_translate.append(reasoning)
        
        # 翻译agent信号中的描述（如果有）
        agent_signals = decision_data.get('agent_signals', [])
        for signal in agent_signals:
            if 'description' in signal:
                texts_to_translate.append(signal['description'])
        
        # 执行并行翻译
        if texts_to_translate:
            translations = self.translate_multiple(texts_to_translate)
            
            # 将翻译结果映射回原数据
            translation_index = 0
            if reasoning:
                decision_data['reasoning_zh'] = translations[translation_index]
                translation_index += 1
            
            for signal in agent_signals:
                if 'description' in signal:
                    signal['description_zh'] = translations[translation_index]
                    translation_index += 1
        
        return decision_data

# 创建全局翻译管理器
translation_manager = TranslationManager()


def translate_with_api(text, max_retries=2):
    """使用API进行智能翻译"""
    
    if not text or not text.strip():
        return text
    
    # 检查缓存
    cached_translation = translation_cache.get(text)
    if cached_translation:
        return cached_translation['translation']
    
    if not API_TRANSLATION_AVAILABLE:
        return translate_with_simple_mapping(text)
    
    # 构建翻译提示
    system_message = {
        "role": "system",
        "content": """你是一个专业的金融投资翻译专家，擅长将英文的股票分析内容翻译成自然流畅的中文。

        翻译要求：
        1. 保持金融术语的专业性和准确性
        2. 翻译要自然流畅，符合中文表达习惯
        3. 保留原文的逻辑结构和语气
        4. 对于专业术语，使用标准的中文金融术语

        常见术语对照：
        - bullish = 看涨/看好
        - bearish = 看跌/看空  
        - neutral = 中性
        - technical analysis = 技术分析
        - fundamental analysis = 基本面分析
        - sentiment analysis = 情绪分析
        - valuation analysis = 估值分析
        - risk management = 风险管理
        - confidence = 置信度
        - fair value = 公允价值
        - portfolio = 投资组合

        请直接返回翻译结果，不要添加解释或前缀。"""
    }
    
    user_message = {
        "role": "user", 
        "content": f"请将以下投资分析内容翻译成中文：\n\n{text}"
    }
    
    for attempt in range(max_retries):
        try:
            # 调用API进行翻译
            response = get_chat_completion(
                [system_message, user_message],
                temperature=0.3,  # 较低的温度确保翻译一致性
                max_tokens=500    # 限制响应长度
            )
            
            if response and response.strip():
                # 清理可能的格式问题
                translation = response.strip()
                
                # 基本质量检查
                if len(translation) > 10 and not translation.startswith("I "):
                    # 缓存翻译结果
                    translation_cache.set(text, translation)
                    return translation
                else:
                    print(f"翻译质量检查失败，尝试 {attempt + 1}/{max_retries}")
                    
        except Exception as e:
            print(f"API翻译失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            
        # 等待后重试
        if attempt < max_retries - 1:
            time.sleep(1)
    
    # API翻译失败，使用简单映射作为备选
    print("API翻译失败，使用简单映射")
    return translate_with_simple_mapping(text)

def translate_with_simple_mapping(text):
    """简单映射翻译（备选方案）"""
    translation_map = {
        # 基本术语
        "bullish": "看涨",
        "bearish": "看跌", 
        "neutral": "中性",
        "technical signal": "技术信号",
        "fundamental analysis": "基本面分析",
        "sentiment": "情绪",
        "valuation analysis": "估值分析",
        "risk management": "风险管理",
        "buy": "买入",
        "sell": "卖出", 
        "hold": "持有",
        "confidence": "置信度",
        "signal": "信号",
        
        # 常见表达
        "Despite a": "尽管",
        "making it difficult to assess": "使得难以评估",
        "fair value": "公允价值",
        "recommends": "建议",
        "reducing position": "减少仓位",
        "since there is no current position": "由于当前没有仓位",
        "the appropriate action is to": "合适的行动是",
        "due to conflicting signals": "由于信号冲突",
        "Confidence is": "置信度",
        "moderate due to": "由于...而适中",
        "conflicting signals": "信号冲突",
        "is invalid": "无效",
        "invalid": "无效",
        
        # 技术分析术语
        "technical analysis": "技术分析",
        "price momentum": "价格动量",
        "moving average": "移动平均线",
        "volatility": "波动性",
        "trend": "趋势",
        "support": "支撑位",
        "resistance": "阻力位",
        
        # 基本面术语
        "earnings": "盈利",
        "revenue": "营收",
        "profit margin": "利润率",
        "debt ratio": "负债比率",
        "cash flow": "现金流",
        "growth rate": "增长率",
        
        # 情绪分析
        "positive sentiment": "积极情绪",
        "negative sentiment": "消极情绪",
        "news analysis": "新闻分析",
        "market sentiment": "市场情绪",
        
        # 风险管理
        "high risk": "高风险",
        "low risk": "低风险",
        "risk tolerance": "风险承受能力",
        "portfolio": "投资组合",
        "diversification": "分散投资"
    }
    
    result = text
    for english, chinese in translation_map.items():
        result = result.replace(english, chinese)
    
    return result

def translate_reasoning_to_chinese(reasoning):
    """将决策理由翻译为中文 - 使用API智能翻译"""
    if not reasoning or reasoning == "无详细说明":
        return "系统未提供详细的决策理由。建议结合各项指标综合考虑。"
    
    # 检查是否已经是中文
    chinese_char_count = len([c for c in reasoning if ord(c) > 127])
    if chinese_char_count > len(reasoning) * 0.3:
        # 如果中文字符超过30%，认为已经是中文
        return reasoning
    
    try:
        # 使用API翻译
        translated = translate_with_api(reasoning)
        
        # 如果翻译结果太短或明显失败，提供默认解释
        if len(translated) < 20 or translated == reasoning:
            return f"""
                基于综合分析的投资建议：

                原文：{reasoning}

                **分析要点：**
                - 技术面：关注价格趋势和技术指标
                - 基本面：评估公司财务状况和业务前景  
                - 情绪面：考虑市场情绪和投资者预期
                - 估值面：判断当前价格是否合理
                - 风险面：评估投资风险和仓位管理

                建议投资者结合自身风险承受能力和投资目标，谨慎决策。
            """.strip()
        
        return translated
        
    except Exception as e:
        print(f"翻译过程中出错: {e}")
        # 出错时使用简单映射
        return translate_with_simple_mapping(reasoning)

def batch_translate_agent_names(agent_signals):
    """批量翻译agent名称（优化版本）"""
    
    # 标准映射（快速路径）
    standard_mapping = {
        'Technical Analysis': '技术分析',
        'Fundamental Analysis': '基本面分析',
        'Sentiment Analysis': '情绪分析',
        'Valuation Analysis': '估值分析',
        'Risk Management': '风险管理',
        'Portfolio Management': '投资组合管理'
    }
    
    translated_signals = []
    
    for signal in agent_signals:
        agent_name = signal.get('agent', 'Unknown')
        
        # 首先尝试标准映射
        if agent_name in standard_mapping:
            translated_name = standard_mapping[agent_name]
        else:
            # 使用智能匹配
            translated_name = smart_agent_name_mapping(agent_name)
        
        translated_signals.append({
            **signal,
            'translated_name': translated_name
        })
    
    return translated_signals

def smart_agent_name_mapping(agent_name):
    """智能agent名称映射"""
    if not agent_name or agent_name == 'Unknown':
        return '未知模块'
    
    # 关键词匹配
    name_lower = agent_name.lower()
    
    keyword_mapping = {
        'technical': '技术分析',
        'fundamental': '基本面分析', 
        'sentiment': '情绪分析',
        'valuation': '估值分析',
        'risk': '风险管理',
        'portfolio': '投资组合管理',
        '技术': '技术分析',
        '基本面': '基本面分析',
        '情绪': '情绪分析',
        '估值': '估值分析',
        '风险': '风险管理'
    }
    
    for keyword, chinese_name in keyword_mapping.items():
        if keyword in name_lower:
            return chinese_name
    
    # 如果都匹配不到，尝试API翻译（仅对于合理长度的文本）
    if len(agent_name) > 3 and len(agent_name) < 50:
        try:
            translated = translate_with_api(f"In stock analysis context, translate this agent name: {agent_name}")
            if translated and translated != agent_name and len(translated) < 20:
                return translated
        except:
            pass
    
    # 最后保持原名称
    return agent_name

def get_translation_stats():
    """获取翻译统计信息"""
    try:
        cache_size = len(translation_cache.cache)
        cache_file_size = translation_cache.cache_file.stat().st_size if translation_cache.cache_file.exists() else 0
        
        return {
            'cache_entries': cache_size,
            'cache_file_size_kb': round(cache_file_size / 1024, 2),
            'api_available': API_TRANSLATION_AVAILABLE
        }
    except Exception as e:
        return {'error': str(e)}

def clear_translation_cache():
    """清除翻译缓存"""
    try:
        translation_cache.cache = {}
        translation_cache._save_cache()
        return True
    except Exception as e:
        print(f"清除缓存失败: {e}")
        return False

# 示例使用函数
def test_translation_system():
    """测试翻译系统"""
    test_texts = [
        "Despite a bullish technical signal and sentiment, the fundamental analysis is bearish and the valuation analysis is invalid.",
        "The risk management signal recommends reducing position, but since there is no current position, the appropriate action is to hold.",
        "Confidence is moderate due to conflicting signals."
    ]
    
    print("🧪 测试翻译系统...")
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n测试 {i}:")
        print(f"原文: {text}")
        
        # 测试API翻译
        translated = translate_reasoning_to_chinese(text)
        print(f"译文: {translated}")
        
        # 测试简单映射
        simple_translated = translate_with_simple_mapping(text)
        print(f"简单映射: {simple_translated}")
    
    # 显示统计信息
    stats = get_translation_stats()
    print(f"\n📊 翻译统计: {stats}")

# 在web界面中使用时的配置选项
def add_translation_settings_to_sidebar():
    """在侧边栏添加翻译设置"""
    st.sidebar.subheader("🌐 翻译设置")
    
    # 翻译方式选择
    translation_method = st.sidebar.selectbox(
        "翻译方式",
        options=["API智能翻译", "简单映射", "禁用翻译"],
        index=0 if API_TRANSLATION_AVAILABLE else 1
    )
    
    # 显示翻译统计
    if st.sidebar.button("查看翻译统计"):
        stats = get_translation_stats()
        st.sidebar.json(stats)
    
    # 清除缓存选项
    if st.sidebar.button("清除翻译缓存"):
        if clear_translation_cache():
            st.sidebar.success("缓存已清除")
        else:
            st.sidebar.error("清除缓存失败")
    
    return translation_method

def get_signal_color(signal):
    """Get color class for signal display"""
    if signal.lower() == 'bullish':
        return 'signal-bullish'
    elif signal.lower() == 'bearish':
        return 'signal-bearish'
    else:
        return 'signal-neutral'

def format_signal_display(signal, confidence):
    """Format signal for display"""
    color_class = get_signal_color(signal)
    if signal.lower() == 'bullish':
        emoji = "🟢"
        text = "看涨"
    elif signal.lower() == 'bearish':
        emoji = "🔴"
        text = "看跌"
    else:
        emoji = "🟡"
        text = "中性"
    
    return f"{emoji} <span class='{color_class}'>{text}</span> ({confidence})"

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_stock_data(symbol, days=365):
    """Fetch stock data with caching"""
    try:
        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=days)
        
        df = get_price_history(
            symbol, 
            start_date.strftime('%Y-%m-%d'), 
            end_date.strftime('%Y-%m-%d')
        )
        
        if df is None or df.empty:
            return None
            
        return df
    except Exception as e:
        st.error(f"获取股票数据失败: {str(e)}")
        return None

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def fetch_financial_data(symbol):
    """Fetch financial data with caching"""
    try:
        financial_metrics = get_financial_metrics(symbol)
        market_data = get_market_data(symbol)
        return financial_metrics, market_data
    except Exception as e:
        st.error(f"获取财务数据失败: {str(e)}")
        return None, None

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def fetch_news_data(symbol, num_news=10):
    """Fetch news data with caching"""
    try:
        news_list = get_stock_news(symbol, max_news=num_news)
        
        # Filter recent news (last 7 days)
        cutoff_date = datetime.now() - timedelta(days=7)
        recent_news = [
            news for news in news_list
            if datetime.strptime(news['publish_time'], '%Y-%m-%d %H:%M:%S') > cutoff_date
        ]
        
        sentiment_score = get_news_sentiment(recent_news, num_of_news=min(len(recent_news), num_news))
        
        return recent_news, sentiment_score
    except Exception as e:
        st.error(f"获取新闻数据失败: {str(e)}")
        return [], 0.0

def create_candlestick_chart(df, symbol):
    """Create candlestick chart with volume"""
    if df is None or df.empty:
        return None
    
    # Create subplots with secondary y-axis
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=('价格走势', '成交量'),
        row_width=[0.7, 0.3]
    )
    
    # Add candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name="K线",
            increasing_line_color='red',
            decreasing_line_color='green'
        ),
        row=1, col=1
    )
    
    # Add moving averages if available
    if 'momentum_1m' in df.columns:
        # Calculate simple moving averages for display
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['ma5'],
                mode='lines',
                name='MA5',
                line=dict(color='blue', width=1)
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['ma20'],
                mode='lines',
                name='MA20',
                line=dict(color='orange', width=1)
            ),
            row=1, col=1
        )
    
    # Add volume chart
    fig.add_trace(
        go.Bar(
            x=df['date'],
            y=df['volume'],
            name="成交量",
            marker_color='lightblue'
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        title=f"{symbol} - 股价走势图",
        xaxis_rangeslider_visible=False,
        height=600,
        showlegend=True,
        template="plotly_white"
    )
    
    fig.update_xaxes(title_text="日期", row=2, col=1)
    fig.update_yaxes(title_text="价格 (元)", row=1, col=1)
    fig.update_yaxes(title_text="成交量", row=2, col=1)
    
    return fig

def display_basic_info(symbol, market_data, financial_metrics, latest_price):
    """Display basic stock information"""
    st.subheader("📊 基本信息")
    
    if market_data and financial_metrics:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="当前价格",
                value=f"¥{latest_price:.2f}" if latest_price else "N/A",
                delta=None
            )
            st.metric(
                label="总市值",
                value=f"¥{market_data.get('market_cap', 0)/100000000:.2f}亿" if market_data.get('market_cap') else "N/A"
            )
        
        with col2:
            pe_ratio = financial_metrics[0].get('pe_ratio', 0) if financial_metrics else 0
            pb_ratio = financial_metrics[0].get('price_to_book', 0) if financial_metrics else 0
            st.metric(label="市盈率 (PE)", value=f"{pe_ratio:.2f}" if pe_ratio else "N/A")
            st.metric(label="市净率 (PB)", value=f"{pb_ratio:.2f}" if pb_ratio else "N/A")
        
        with col3:
            roe = financial_metrics[0].get('return_on_equity', 0) if financial_metrics else 0
            net_margin = financial_metrics[0].get('net_margin', 0) if financial_metrics else 0
            st.metric(label="净资产收益率", value=f"{roe*100:.2f}%" if roe else "N/A")
            st.metric(label="净利率", value=f"{net_margin*100:.2f}%" if net_margin else "N/A")
        
        with col4:
            revenue_growth = financial_metrics[0].get('revenue_growth', 0) if financial_metrics else 0
            earnings_growth = financial_metrics[0].get('earnings_growth', 0) if financial_metrics else 0
            st.metric(label="营收增长率", value=f"{revenue_growth*100:.2f}%" if revenue_growth else "N/A")
            st.metric(label="净利润增长率", value=f"{earnings_growth*100:.2f}%" if earnings_growth else "N/A")

def display_financial_health(financial_metrics):
    """Display financial health analysis"""
    st.subheader("💰 财务健康")
    
    if not financial_metrics or not financial_metrics[0]:
        st.warning("财务数据不可用")
        return
    
    metrics = financial_metrics[0]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**盈利能力**")
        
        # ROE assessment
        roe = metrics.get('return_on_equity', 0)
        roe_status = "优秀" if roe > 0.15 else "良好" if roe > 0.10 else "一般" if roe > 0.05 else "较差"
        st.markdown(f"• 净资产收益率: {roe*100:.2f}% ({roe_status})")
        
        # Net margin assessment
        net_margin = metrics.get('net_margin', 0)
        margin_status = "优秀" if net_margin > 0.20 else "良好" if net_margin > 0.10 else "一般" if net_margin > 0.05 else "较差"
        st.markdown(f"• 净利率: {net_margin*100:.2f}% ({margin_status})")
        
        # Operating margin
        op_margin = metrics.get('operating_margin', 0)
        st.markdown(f"• 营业利润率: {op_margin*100:.2f}%")
    
    with col2:
        st.markdown("**财务状况**")
        
        # Current ratio
        current_ratio = metrics.get('current_ratio', 0)
        liquidity_status = "优秀" if current_ratio > 2.0 else "良好" if current_ratio > 1.5 else "一般" if current_ratio > 1.0 else "较差"
        st.markdown(f"• 流动比率: {current_ratio:.2f} ({liquidity_status})")
        
        # Debt to equity
        debt_ratio = metrics.get('debt_to_equity', 0)
        debt_status = "优秀" if debt_ratio < 0.3 else "良好" if debt_ratio < 0.5 else "一般" if debt_ratio < 0.7 else "较差"
        st.markdown(f"• 资产负债率: {debt_ratio*100:.2f}% ({debt_status})")
        
        # Growth metrics
        revenue_growth = metrics.get('revenue_growth', 0)
        st.markdown(f"• 营收增长率: {revenue_growth*100:.2f}%")

def display_news_summary(news_list, sentiment_score):
    """Display news summary and sentiment"""
    st.subheader("📰 新闻摘要与情绪分析")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**最新新闻**")
        
        if news_list:
            for i, news in enumerate(news_list[:5]):  # Show top 5 news
                with st.expander(f"{news['title'][:50]}..."):
                    st.markdown(f"**来源:** {news['source']}")
                    st.markdown(f"**时间:** {news['publish_time']}")
                    st.markdown(f"**内容:** {news['content'][:200]}...")
                    if news.get('url'):
                        st.markdown(f"[查看原文]({news['url']})")
        else:
            st.info("暂无最新新闻")
    
    with col2:
        st.markdown("**情绪分析**")
        
        # Sentiment gauge
        sentiment_text = "积极" if sentiment_score > 0.3 else "消极" if sentiment_score < -0.3 else "中性"
        sentiment_color = "green" if sentiment_score > 0.3 else "red" if sentiment_score < -0.3 else "orange"
        
        st.metric(
            label="整体情绪",
            value=sentiment_text,
            delta=f"分数: {sentiment_score:.2f}"
        )
        
        # Sentiment bar
        fig_sentiment = go.Figure(go.Indicator(
            mode="gauge+number",
            value=sentiment_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "情绪指标"},
            gauge={
                'axis': {'range': [-1, 1]},
                'bar': {'color': sentiment_color},
                'steps': [
                    {'range': [-1, -0.3], 'color': "lightcoral"},
                    {'range': [-0.3, 0.3], 'color': "lightyellow"},
                    {'range': [0.3, 1], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 0
                }
            }
        ))
        
        fig_sentiment.update_layout(height=250)
        st.plotly_chart(fig_sentiment, use_container_width=True)

def display_investment_decision(decision_result):
    '''
    """Display investment decision with reasoning"""
    st.subheader("🎯 投资决策")
    
    try:
        if isinstance(decision_result, str):
            decision = json.loads(decision_result)
        else:
            decision = decision_result
        
        action = decision.get('action', 'hold')
        quantity = decision.get('quantity', 0)
        confidence = decision.get('confidence', 0)
        agent_signals = decision.get('agent_signals', [])
        reasoning = decision.get('reasoning', '无详细说明')
        
        # Main decision display
        decision_class = f"decision-{action}"
        action_text = "买入" if action == "buy" else "卖出" if action == "sell" else "持有"
        action_emoji = "🟢" if action == "buy" else "🔴" if action == "sell" else "🟡"
        
        st.markdown(f"""
        <div class="{decision_class}">
            <h3>{action_emoji} 推荐操作: {action_text}</h3>
            <p><strong>数量:</strong> {quantity:,} 股</p>
            <p><strong>置信度:</strong> {confidence*100:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Agent signals breakdown
        st.markdown("**各分析模块信号**")
        
        signal_cols = st.columns(len(agent_signals) if agent_signals else 1)
        
        for i, signal in enumerate(agent_signals):
            with signal_cols[i % len(signal_cols)]:
                agent_name = signal.get('agent', 'Unknown')
                agent_signal = signal.get('signal', 'neutral')
                agent_confidence = signal.get('confidence', 0)
                
                # Translate agent names
                agent_display_names = {
                    'Technical Analysis': '技术分析',
                    'Fundamental Analysis': '基本面分析',
                    'Sentiment Analysis': '情绪分析',
                    'Valuation Analysis': '估值分析',
                    'Risk Management': '风险管理'
                }
                
                display_name = agent_display_names.get(agent_name, agent_name)
                confidence_str = f"{agent_confidence*100:.0f}%" if isinstance(agent_confidence, (int, float)) else str(agent_confidence)
                
                signal_html = format_signal_display(agent_signal, confidence_str)
                
                st.markdown(f"""
                <div class="metric-container">
                    <strong>{display_name}</strong><br>
                    {signal_html}
                </div>
                """, unsafe_allow_html=True)
        
        # Detailed reasoning
        st.markdown("**决策理由**")
        st.info(reasoning)
        
        # Risk warning
        st.warning("⚠️ 投资有风险，决策仅供参考。请根据自身情况谨慎投资。")
        
    except Exception as e:
        st.error(f"解析投资决策失败: {str(e)}")
        st.text(f"原始数据: {decision_result}")
    '''
    return display_investment_decision_with_api_translation(decision_result)

def display_decision_content(action, quantity, confidence, agent_signals, reasoning):
    """Display the actual decision content with API translation"""
    # Main decision display
    decision_class = f"decision-{action}"
    action_text = "买入" if action == "buy" else "卖出" if action == "sell" else "持有"
    action_emoji = "🟢" if action == "buy" else "🔴" if action == "sell" else "🟡"
    
    # 确保confidence是数字
    if isinstance(confidence, str):
        try:
            confidence = float(confidence.replace('%', '')) / 100 if '%' in confidence else float(confidence)
        except:
            confidence = 0.5
    
    st.markdown(f"""
    <div class="{decision_class}">
        <h3>{action_emoji} 推荐操作: {action_text}</h3>
        <p><strong>数量:</strong> {quantity:,} 股</p>
        <p><strong>置信度:</strong> {confidence*100:.1f}%</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Agent signals breakdown with API translation
    if agent_signals:
        st.markdown("**各分析模块信号**")
        
        # 使用批量翻译优化性能
        translated_signals = batch_translate_agent_names(agent_signals)
        
        # 动态调整列数
        num_signals = len(translated_signals)
        if num_signals <= 3:
            signal_cols = st.columns(num_signals)
        else:
            signal_cols = st.columns(3)
        
        for i, signal_data in enumerate(translated_signals):
            with signal_cols[i % len(signal_cols)]:
                agent_name = signal_data.get('agent', 'Unknown')
                agent_signal = signal_data.get('signal', 'neutral')
                agent_confidence = signal_data.get('confidence', 0)
                translated_name = signal_data.get('translated_name', agent_name)
                
                # 处理置信度格式
                if isinstance(agent_confidence, str):
                    confidence_str = agent_confidence
                else:
                    confidence_str = f"{agent_confidence*100:.0f}%" if isinstance(agent_confidence, (int, float)) else "N/A"
                
                signal_html = format_signal_display(agent_signal, confidence_str)
                
                st.markdown(f"""
                <div class="metric-container">
                    <strong>{translated_name}</strong><br>
                    {signal_html}
                </div>
                """, unsafe_allow_html=True)
    
    # Detailed reasoning with API translation
    st.markdown("**决策理由**")
    
    # 显示翻译进度
    with st.spinner("正在翻译决策理由..."):
        translated_reasoning = translate_reasoning_to_chinese(reasoning)
    
    # 显示翻译结果
    st.info(translated_reasoning)
    
    # 可选：显示原文（调试模式）
    if st.session_state.get('show_original_text', False):
        with st.expander("📄 查看原文", expanded=False):
            st.text(reasoning)
    
    # Risk warning
    st.warning("⚠️ 投资有风险，决策仅供参考。请根据自身情况谨慎投资。")

def display_investment_decision_with_api_translation(decision_result):
    """Display investment decision with API translation support"""
    st.subheader("🎯 投资决策")
    
    # 翻译设置控制
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        pass  # 空列用于布局
    with col2:
        show_original = st.checkbox("显示原文", key="show_original_text")
    with col3:
        translation_mode = st.selectbox(
            "翻译模式",
            options=["API翻译", "简单映射"],
            key="translation_mode"
        )
    
    # 根据选择的翻译模式设置全局变量
    if translation_mode == "简单映射":
        # 临时禁用API翻译
        global API_TRANSLATION_AVAILABLE
        temp_api_status = API_TRANSLATION_AVAILABLE
        API_TRANSLATION_AVAILABLE = False
    
    # 调试信息（可选）
    with st.expander("🔧 调试信息", expanded=False):
        st.write("decision_result 类型:", type(decision_result))
        st.write("decision_result 长度:", len(str(decision_result)) if decision_result else 0)
        
        # 翻译系统状态
        translation_stats = get_translation_stats()
        st.write("翻译系统状态:", translation_stats)
        
        # 如果是字符串，尝试解析并显示agent信息
        if isinstance(decision_result, str) and decision_result.strip():
            try:
                test_parse = json.loads(decision_result.strip().replace('```json', '').replace('```', ''))
                if 'agent_signals' in test_parse:
                    st.write("原始agent信号:")
                    for signal in test_parse['agent_signals']:
                        st.write(f"- Agent: {signal.get('agent', 'Unknown')}")
                        st.write(f"  Signal: {signal.get('signal', 'unknown')}")
                        st.write(f"  Confidence: {signal.get('confidence', 'unknown')}")
            except:
                st.write("无法解析为JSON格式")
    
    # 检查是否为空值
    if not decision_result:
        st.error("❌ 未收到投资决策结果")
        display_fallback_decision()
        return
    
    # 转换为字符串（如果不是）
    if not isinstance(decision_result, str):
        decision_result = str(decision_result)
    
    # 清理可能的格式问题
    decision_result = decision_result.strip()
    
    # 检查是否包含JSON标记并清理
    if decision_result.startswith('```json'):
        decision_result = decision_result.replace('```json', '').replace('```', '').strip()
    
    try:
        # 尝试解析JSON
        decision = json.loads(decision_result)
        
        # 验证必要字段
        if not isinstance(decision, dict):
            raise ValueError("决策结果不是有效的字典格式")
            
        action = decision.get('action', 'hold')
        quantity = decision.get('quantity', 0)
        confidence = decision.get('confidence', 0)
        agent_signals = decision.get('agent_signals', [])
        reasoning = decision.get('reasoning', '无详细说明')
        
        # 显示决策结果（使用API翻译）
        display_decision_content(action, quantity, confidence, agent_signals, reasoning)
        
    except json.JSONDecodeError as e:
        st.error(f"❌ JSON解析失败: {str(e)}")
        st.warning("尝试从文本中提取决策信息...")
        
        # 尝试从文本中提取信息
        extracted_decision = extract_decision_from_text(decision_result)
        if extracted_decision:
            st.info("✅ 成功从文本中提取决策信息")
            display_decision_content(**extracted_decision)
        else:
            st.error("无法从文本中提取有效决策信息")
            display_fallback_decision()
            
            # 显示原始内容供调试
            with st.expander("📋 原始返回内容", expanded=False):
                st.text(decision_result)
    
    except Exception as e:
        st.error(f"❌ 处理投资决策时出错: {str(e)}")
        display_fallback_decision()
        
        # 显示原始内容供调试
        with st.expander("📋 原始返回内容", expanded=False):
            st.text(decision_result)
    
    finally:
        # 恢复API翻译状态
        if translation_mode == "简单映射":
            API_TRANSLATION_AVAILABLE = temp_api_status

def add_translation_controls_to_main():
    """在主界面添加翻译控制"""
    st.sidebar.subheader("🌐 翻译设置")
    
    # API翻译状态
    api_status = "✅ 可用" if API_TRANSLATION_AVAILABLE else "❌ 不可用"
    st.sidebar.info(f"API翻译: {api_status}")
    
    # 翻译统计
    if st.sidebar.button("📊 查看翻译统计"):
        stats = get_translation_stats()
        st.sidebar.json(stats)
    
    # 测试翻译
    if st.sidebar.button("🧪 测试翻译系统"):
        test_translation_system()
        st.sidebar.success("测试完成，请查看控制台输出")
    
    # 缓存管理
    if st.sidebar.button("🗑️ 清除翻译缓存"):
        if clear_translation_cache():
            st.sidebar.success("翻译缓存已清除")
        else:
            st.sidebar.error("清除缓存失败")
    
    # 翻译设置
    st.sidebar.markdown("**翻译选项**")
    enable_api_translation = st.sidebar.checkbox(
        "启用API翻译", 
        value=True,
        help="使用AI API进行智能翻译，提供更自然的中文表达"
    )
    
    cache_translations = st.sidebar.checkbox(
        "缓存翻译结果", 
        value=True,
        help="缓存翻译结果以提高性能和节省API调用"
    )
    
    return {
        'enable_api_translation': enable_api_translation,
        'cache_translations': cache_translations
    }

def main():
    """Main application"""
    
    # Title
    st.markdown('<h1 class="main-header">🤖 AI投资决策系统</h1>', unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ 配置参数")
        
        # Stock selection
        symbol = st.text_input(
            "股票代码", 
            value="600519", 
            help="请输入6位A股代码，如：600519（贵州茅台）"
        )
        
        # Analysis parameters
        st.subheader("分析参数")
        num_news = st.slider("新闻分析数量", min_value=5, max_value=50, value=10)
        show_reasoning = st.checkbox("显示详细分析过程", value=True)
        
        # Time range
        st.subheader("时间范围")
        days_range = st.selectbox(
            "历史数据范围",
            options=[30, 90, 180, 365],
            index=3,
            format_func=lambda x: f"{x}天"
        )
        
        # Analysis button
        analyze_button = st.button("🔍 开始分析", type="primary", use_container_width=True)
        
        # API status
        st.subheader("系统状态")
        api_provider = os.getenv('API_PROVIDER', 'unknown')
        model_name = os.getenv('MODEL_NAME', 'unknown')
        st.info(f"API提供商: {api_provider}")
        st.info(f"模型: {model_name}")

        translation_settings = add_translation_controls_to_main()

    
    # Main content area
    if analyze_button and symbol:
        # Validate stock code
        if not symbol.isdigit() or len(symbol) != 6:
            st.error("请输入有效的6位股票代码")
            return
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Fetch stock data
            status_text.text("正在获取股票数据...")
            progress_bar.progress(20)
            
            df = fetch_stock_data(symbol, days_range)
            if df is None or df.empty:
                st.error("无法获取股票数据，请检查股票代码")
                return
            
            latest_price = df['close'].iloc[-1] if not df.empty else None
            
            # Step 2: Fetch financial data
            status_text.text("正在获取财务数据...")
            progress_bar.progress(40)
            
            financial_metrics, market_data = fetch_financial_data(symbol)
            
            # Step 3: Fetch news data
            status_text.text("正在分析新闻情绪...")
            progress_bar.progress(60)
            
            news_list, sentiment_score = fetch_news_data(symbol, num_news)
            
            # Step 4: Run AI analysis
            status_text.text("正在运行AI分析...")
            progress_bar.progress(80)
            
            # Prepare date range for analysis
            end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days_range)).strftime('%Y-%m-%d')
            
            # Run the hedge fund analysis
            portfolio = {"cash": 100000, "stock": 0}
            decision_result = run_hedge_fund(
                ticker=symbol,
                start_date=start_date,
                end_date=end_date,
                portfolio=portfolio,
                show_reasoning=show_reasoning,
                num_of_news=num_news
            )
            
            progress_bar.progress(100)
            status_text.text("分析完成！")
            
            # Clear progress indicators
            time.sleep(1)
            progress_bar.empty()
            status_text.empty()
            
            # Display results
            
            # Row 1: Basic info and chart
            col1, col2 = st.columns([1, 2])
            
            with col1:
                display_basic_info(symbol, market_data, financial_metrics, latest_price)
            
            with col2:
                # Create and display chart
                fig = create_candlestick_chart(df, symbol)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("无法创建价格图表")
            
            # Row 2: Financial health
            display_financial_health(financial_metrics)
            
            # Row 3: News and sentiment
            display_news_summary(news_list, sentiment_score)
            
            # Row 4: Investment decision
            display_investment_decision(decision_result)
            
        except Exception as e:
            st.error(f"分析过程中出现错误: {str(e)}")
            if show_reasoning:
                st.exception(e)
        
        finally:
            progress_bar.empty()
            status_text.empty()
    
    elif not symbol:
        # Welcome screen
        st.info("👈 请在左侧输入股票代码开始分析")
        
        # Feature showcase
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            ### 📈 技术分析
            - K线图和成交量分析
            - 多种技术指标
            - 趋势识别和信号生成
            """)
        
        with col2:
            st.markdown("""
            ### 💰 基本面分析
            - 财务健康评估
            - 盈利能力分析
            - 成长性指标
            """)
        
        with col3:
            st.markdown("""
            ### 📰 智能决策
            - AI新闻情绪分析
            - 多维度综合评估
            - 风险控制建议
            """)

if __name__ == "__main__":
    main()