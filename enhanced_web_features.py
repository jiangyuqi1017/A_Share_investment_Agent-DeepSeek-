# Additional features for the web interface
# Add these functions to enhance the existing web_interface.py

import io
import base64
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

def create_comparison_chart(symbols_data):
    """Create comparison chart for multiple stocks"""
    fig = go.Figure()
    
    colors = ['blue', 'red', 'green', 'orange', 'purple']
    
    for i, (symbol, data) in enumerate(symbols_data.items()):
        if data is not None and not data.empty:
            # Normalize prices to percentage change from first day
            normalized_prices = (data['close'] / data['close'].iloc[0] - 1) * 100
            
            fig.add_trace(go.Scatter(
                x=data['date'],
                y=normalized_prices,
                mode='lines',
                name=symbol,
                line=dict(color=colors[i % len(colors)])
            ))
    
    fig.update_layout(
        title="股票价格对比 (相对涨跌幅 %)",
        xaxis_title="日期",
        yaxis_title="涨跌幅 (%)",
        template="plotly_white",
        height=400
    )
    
    return fig

def export_analysis_report(symbol, decision_result, financial_metrics, news_summary, sentiment_score):
    """Generate downloadable analysis report"""
    
    report_content = f"""
# AI投资分析报告

## 股票信息
- **股票代码**: {symbol}
- **分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 投资决策
"""
    
    try:
        if isinstance(decision_result, str):
            decision = json.loads(decision_result)
        else:
            decision = decision_result
            
        action = decision.get('action', 'hold')
        quantity = decision.get('quantity', 0)
        confidence = decision.get('confidence', 0)
        
        action_text = "买入" if action == "buy" else "卖出" if action == "sell" else "持有"
        
        report_content += f"""
- **推荐操作**: {action_text}
- **建议数量**: {quantity:,} 股
- **置信度**: {confidence*100:.1f}%

### 各模块信号
"""
        
        for signal in decision.get('agent_signals', []):
            agent_name = signal.get('agent', 'Unknown')
            agent_signal = signal.get('signal', 'neutral')
            agent_confidence = signal.get('confidence', 0)
            
            agent_display_names = {
                'Technical Analysis': '技术分析',
                'Fundamental Analysis': '基本面分析',
                'Sentiment Analysis': '情绪分析',
                'Valuation Analysis': '估值分析',
                'Risk Management': '风险管理'
            }
            
            display_name = agent_display_names.get(agent_name, agent_name)
            signal_text = "看涨" if agent_signal == "bullish" else "看跌" if agent_signal == "bearish" else "中性"
            confidence_str = f"{agent_confidence*100:.0f}%" if isinstance(agent_confidence, (int, float)) else str(agent_confidence)
            
            report_content += f"- **{display_name}**: {signal_text} ({confidence_str})\n"
        
        report_content += f"""

### 决策理由
{decision.get('reasoning', '无详细说明')}

## 财务分析
"""
        
        if financial_metrics and financial_metrics[0]:
            metrics = financial_metrics[0]
            
            report_content += f"""
### 盈利能力指标
- **净资产收益率**: {metrics.get('return_on_equity', 0)*100:.2f}%
- **净利率**: {metrics.get('net_margin', 0)*100:.2f}%
- **营业利润率**: {metrics.get('operating_margin', 0)*100:.2f}%

### 成长性指标
- **营收增长率**: {metrics.get('revenue_growth', 0)*100:.2f}%
- **净利润增长率**: {metrics.get('earnings_growth', 0)*100:.2f}%

### 财务健康指标
- **流动比率**: {metrics.get('current_ratio', 0):.2f}
- **资产负债率**: {metrics.get('debt_to_equity', 0)*100:.2f}%

### 估值指标
- **市盈率**: {metrics.get('pe_ratio', 0):.2f}
- **市净率**: {metrics.get('price_to_book', 0):.2f}
- **市销率**: {metrics.get('price_to_sales', 0):.2f}
"""

        report_content += f"""

## 情绪分析
- **情绪分数**: {sentiment_score:.2f} (范围: -1 到 +1)
- **情绪评价**: {"积极" if sentiment_score > 0.3 else "消极" if sentiment_score < -0.3 else "中性"}

## 新闻摘要
"""
        
        for i, news in enumerate(news_summary[:3], 1):
            report_content += f"""
### 新闻 {i}
- **标题**: {news.get('title', 'N/A')}
- **来源**: {news.get('source', 'N/A')}
- **时间**: {news.get('publish_time', 'N/A')}
- **内容**: {news.get('content', 'N/A')[:200]}...

"""

        report_content += """
---
**免责声明**: 本报告仅供参考，不构成投资建议。投资有风险，请谨慎决策。
"""
        
    except Exception as e:
        report_content += f"\n错误: 生成报告时出现问题 - {str(e)}"
    
    return report_content

def create_download_link(content, filename, link_text):
    """Create download link for content"""
    b64 = base64.b64encode(content.encode()).decode()
    href = f'<a href="data:text/plain;base64,{b64}" download="{filename}">{link_text}</a>'
    return href

def display_advanced_metrics(df):
    """Display advanced technical metrics"""
    if df is None or df.empty:
        return
    
    st.subheader("📈 高级技术指标")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Volatility
        returns = df['close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252) * 100
        st.metric("年化波动率", f"{volatility:.2f}%")
    
    with col2:
        # Price change
        price_change = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
        st.metric("期间涨跌幅", f"{price_change:.2f}%")
    
    with col3:
        # Max drawdown
        rolling_max = df['close'].expanding().max()
        drawdown = (df['close'] / rolling_max - 1) * 100
        max_drawdown = drawdown.min()
        st.metric("最大回撤", f"{max_drawdown:.2f}%")
    
    with col4:
        # Average volume
        avg_volume = df['volume'].mean() / 100  # Convert to lots
        st.metric("平均成交量", f"{avg_volume:.0f}手")

def create_risk_assessment_chart(financial_metrics):
    """Create risk assessment radar chart"""
    if not financial_metrics or not financial_metrics[0]:
        return None
    
    metrics = financial_metrics[0]
    
    # Risk factors (higher score = lower risk)
    risk_factors = {
        '盈利能力': min(metrics.get('return_on_equity', 0) * 5, 1),
        '财务稳定': min(1 - metrics.get('debt_to_equity', 1), 1),
        '流动性': min(metrics.get('current_ratio', 0) / 2, 1),
        '成长性': min(metrics.get('revenue_growth', 0) * 2, 1),
        '估值合理性': min(1 / max(metrics.get('pe_ratio', 30) / 20, 0.1), 1)
    }
    
    # Ensure all values are between 0 and 1
    risk_factors = {k: max(0, min(1, v)) for k, v in risk_factors.items()}
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=list(risk_factors.values()),
        theta=list(risk_factors.keys()),
        fill='toself',
        name='风险评估',
        line_color='rgb(0,100,200)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )),
        showlegend=True,
        title="风险评估雷达图",
        height=400
    )
    
    return fig

def display_stock_comparison():
    """Display stock comparison feature"""
    st.subheader("📊 股票对比分析")
    
    with st.expander("添加对比股票"):
        compare_symbols = st.text_input(
            "输入对比股票代码(用逗号分隔)",
            placeholder="例如: 600036,000002,000001"
        )
        
        if compare_symbols and st.button("生成对比图"):
            symbols = [s.strip() for s in compare_symbols.split(',')]
            symbols_data = {}
            
            for symbol in symbols:
                if symbol.isdigit() and len(symbol) == 6:
                    data = fetch_stock_data(symbol, 90)  # 3 months data
                    symbols_data[symbol] = data
            
            if symbols_data:
                fig = create_comparison_chart(symbols_data)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("未能获取有效的对比数据")

def add_sidebar_features():
    """Add advanced features to sidebar"""
    
    st.sidebar.subheader("📊 高级功能")
    
    # Export options
    if st.sidebar.checkbox("启用数据导出"):
        st.sidebar.info("分析完成后可下载报告")
    
    # Comparison mode
    if st.sidebar.checkbox("启用股票对比"):
        st.sidebar.info("将显示股票对比功能")
    
    # Alert settings
    st.sidebar.subheader("🔔 提醒设置")
    price_alert = st.sidebar.number_input("价格提醒阈值(%)", min_value=-50.0, max_value=50.0, value=0.0)
    
    if price_alert != 0:
        st.sidebar.info(f"当价格变动超过{price_alert}%时提醒")
    
    # Display preferences
    st.sidebar.subheader("🎨 显示选项")
    chart_theme = st.sidebar.selectbox("图表主题", ["plotly_white", "plotly_dark", "simple_white"])
    show_advanced_metrics = st.sidebar.checkbox("显示高级指标", value=True)
    
    return {
        'export_enabled': st.sidebar.checkbox("启用数据导出"),
        'comparison_enabled': st.sidebar.checkbox("启用股票对比"),
        'price_alert': price_alert,
        'chart_theme': chart_theme,
        'show_advanced_metrics': show_advanced_metrics
    }

# Integration example for the main interface
def enhanced_main_interface_example():
    """Example of how to integrate enhanced features"""
    
    # Add to main() function after the analyze_button logic
    
    # Advanced sidebar features
    sidebar_options = add_sidebar_features()
    
    # In the results display section, add:
    
    # Advanced metrics (if enabled)
    if sidebar_options['show_advanced_metrics']:
        display_advanced_metrics(df)
    
    # Risk assessment chart
    if financial_metrics:
        risk_fig = create_risk_assessment_chart(financial_metrics)
        if risk_fig:
            st.plotly_chart(risk_fig, use_container_width=True)
    
    # Stock comparison (if enabled)
    if sidebar_options['comparison_enabled']:
        display_stock_comparison()
    
    # Export functionality (if enabled)
    if sidebar_options['export_enabled']:
        st.subheader("📥 导出报告")
        
        report_content = export_analysis_report(
            symbol, decision_result, financial_metrics, news_list, sentiment_score
        )
        
        filename = f"投资分析报告_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📄 下载分析报告",
                data=report_content,
                file_name=filename,
                mime="text/markdown"
            )
        
        with col2:
            # CSV export option
            if not df.empty:
                csv_data = df.to_csv(index=False)
                csv_filename = f"股票数据_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                st.download_button(
                    label="📊 下载价格数据",
                    data=csv_data,
                    file_name=csv_filename,
                    mime="text/csv"
                )

# Real-time features (requires additional setup)
def add_realtime_features():
    """Add real-time monitoring features"""
    
    st.subheader("⏰ 实时监控")
    
    # Auto-refresh option
    auto_refresh = st.checkbox("启用自动刷新 (每5分钟)")
    
    if auto_refresh:
        # Add auto-refresh logic
        st.info("🔄 启用自动刷新模式")
        
        # Placeholder for real-time price updates
        placeholder = st.empty()
        
        # This would require a background task in production
        with placeholder.container():
            st.info("实时价格监控功能需要后台服务支持")

# Mobile optimization functions
def optimize_for_mobile():
    """Optimize interface for mobile devices"""
    
    # Detect mobile using JavaScript (limited in Streamlit)
    mobile_css = """
    <style>
    @media screen and (max-width: 768px) {
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        .metric-container {
            margin: 0.25rem 0;
            padding: 0.5rem;
        }
        
        .stButton > button {
            width: 100%;
        }
    }
    </style>
    """
    
    st.markdown(mobile_css, unsafe_allow_html=True)