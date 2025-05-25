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