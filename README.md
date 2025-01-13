# AI 投资系统

这是一个基于人工智能的投资系统概念验证项目。项目目标是探索如何使用 AI 来辅助投资决策。本项目仅用于**教育目的**，不适用于实际交易或投资。

## 系统组成

系统由以下几个协同工作的 agent 组成：

- **Market Data Analyst**：负责收集和预处理市场数据
- **Valuation Agent**：计算股票内在价值并生成交易信号  
- **Sentiment Agent**：分析市场情绪并生成交易信号
- **Fundamentals Agent**：分析基本面数据并生成交易信号
- **Technical Analyst**：分析技术指标并生成交易信号
- **Risk Manager**：计算风险指标并设置仓位限制
- **Portfolio Manager**：制定最终交易决策并生成订单

![Screenshot 2024-12-27 at 5 49 56 PM](https://github.com/user-attachments/assets/c281b8c3-d8e6-431e-a05e-d309d306e967)

注意：系统仅模拟交易决策，不进行实际交易。

## 免责声明

本项目仅用于**教育和研究目的**。

- 不适用于实际交易或投资
- 不提供任何保证
- 过往业绩不代表未来表现
- 创建者不承担任何财务损失责任
- 投资决策请咨询专业理财顾问

使用本软件即表示您同意仅将其用于学习目的。

## 目录

- [安装](#安装)
- [使用](#使用)
  - [运行对冲基金](#运行对冲基金)
  - [运行回测](#运行回测)
- [项目结构](#项目结构)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## 安装

1. 克隆仓库：

```bash
git clone https://github.com/zivmryang/A_Share_investment_Agent-DeepSeek-.git
cd A_Share_investent_Agent
```

2. 安装 Poetry（如果尚未安装）：

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

3. 安装依赖：

```bash
poetry install
```

4. 设置环境变量：

```bash
# 创建.env文件用于存储API密钥
cp .env.example .env

# 从 https://platform.deepseek.com/ 获取DeepSeek API密钥
export DEEP_SEEK_API_KEY='your-deepseek-api-key-here'
export DEEP_SEEK_MODEL='deepseek-chat'
```

## DeepSeek API 申请指南

1. 访问 [DeepSeek 平台](https://platform.deepseek.com/)
2. 注册或登录您的账户
3. 进入 API Keys 页面
4. 点击 "Create new API key" 按钮
5. 复制生成的 API key
6. 将 API key 填入 .env 文件中的 DEEP_SEEK_API_KEY 变量

## 使用说明

### 运行对冲基金

系统支持多种运行方式，可以根据需要组合使用不同的参数：

1. **基本运行**

```bash
poetry run python src/main.py --ticker 301155
```

这将使用默认参数运行系统，包括：

- 默认分析 5 条新闻（num_of_news=5）
- 不显示详细分析过程（show_reasoning=False）
- 使用默认的初始资金（initial_capital=100,000）

2. **显示分析推理过程**

```bash
poetry run python src/main.py --ticker 301155 --show-reasoning
```

这将显示每个智能体（Market Data Agent、Technical Analyst、Fundamentals Agent、Sentiment Agent、Risk Manager、Portfolio Manager）的分析过程和推理结果。

这允许你设置：

- initial_capital: 初始现金金额（可选，默认为 100,000）

3. **自定义新闻分析数量和具体日期的投资建议**

```bash
poetry run python src/main.py --ticker 301157 --show-reasoning --end-date 2024-12-11 --num-of-news 20
```

这将：

- 分析指定日期范围内最近的 20 条新闻进行情绪分析
- start-date 和 end-date 格式为 YYYY-MM-DD

4. **回测功能**

```bash
poetry run python src/backtester.py --ticker 301157 --start-date 2024-12-11 --end-date 2025-01-07 --num-of-news 20
```

回测功能支持以下参数：

- ticker: 股票代码
- start-date: 回测开始日期（YYYY-MM-DD）
- end-date: 回测结束日期（YYYY-MM-DD）
- initial-capital: 初始资金（可选，默认为 100,000）
- num-of-news: 情绪分析使用的新闻数量（可选，默认为 5，最大为 100）

### 参数说明

- `--ticker`: 股票代码（必需）
- `--show-reasoning`: 显示分析推理过程（可选，默认为 false）
- `--initial-capital`: 初始现金金额（可选，默认为 100,000）
- `--num-of-news`: 情绪分析使用的新闻数量（可选，默认为 5，最大为 100）
- `--start-date`: 开始日期，格式 YYYY-MM-DD（可选）
- `--end-date`: 结束日期，格式 YYYY-MM-DD（可选）

### 输出说明

系统会输出以下信息：

1. 基本面分析结果
2. 估值分析结果
3. 技术分析结果
4. 情绪分析结果
5. 风险管理评估
6. 最终交易决策

如果使用了`--show-reasoning`参数，还会显示每个智能体的详细分析过程。

**Example Output:**

```
正在获取 301157 的历史行情数据...
开始日期：2024-12-11
结束日期：2024-12-11
成功获取历史行情数据，共 242 条记录

警告：以下指标存在NaN值：
- momentum_1m: 20条
- momentum_3m: 60条
- momentum_6m: 120条
...（这些警告是正常的，是由于某些技术指标需要更长的历史数据才能计算）

正在获取 301157 的财务指标数据...
获取实时行情...
成功获取实时行情数据

获取新浪财务指标...
成功获取新浪财务指标数据，共 3 条记录
最新数据日期：2024-09-30 00:00:00

获取利润表数据...
成功获取利润表数据

构建指标数据...
成功构建指标数据

Final Result:
{
  "action": "buy",
  "quantity": 12500,
  "confidence": 0.42,
  "agent_signals": [
    {
      "agent": "Technical Analysis",
      "signal": "bullish",
      "confidence": 0.6
    },
    {
      "agent": "Fundamental Analysis",
      "signal": "neutral",
      "confidence": 0.5
    },
    {
      "agent": "Sentiment Analysis",
      "signal": "neutral",
      "confidence": 0.8
    },
    {
      "agent": "Valuation Analysis",
      "signal": "bearish",
      "confidence": 0.99
    },
    {
      "agent": "Risk Management",
      "signal": "buy",
      "confidence": 1.0
    }
  ],
  "reasoning": "Risk Management allows a buy action with a maximum quantity of 12500..."
}
```

### 日志文件说明

系统会在 `logs/` 目录下生成以下类型的日志文件：

1. **回测日志**

   - 文件名格式：`backtest_{股票代码}_{当前日期}_{回测开始日期}_{回测结束日期}.log`
   - 示例：`backtest_301157_20250107_20241201_20241230.log`
   - 包含：每个交易日的分析结果、交易决策和投资组合状态

2. **API 调用日志**
   - 文件名格式：`api_calls_{当前日期}.log`
   - 示例：`api_calls_20250107.log`
   - 包含：所有 API 调用的详细信息和响应

所有日期格式均为 YYYY-MM-DD。如果使用了 `--show-reasoning` 参数，详细的分析过程也会记录在日志文件中。

## 项目结构

```
ai-hedge-fund/
├── src/                         # 源代码目录
│   ├── agents/                  # agent定义和工作流
│   │   ├── fundamentals.py      # 基本面分析Agent
│   │   ├── market_data.py       # 市场数据分析Agent
│   │   ├── portfolio_manager.py # 投资组合管理Agent
│   │   ├── risk_manager.py      # 风险管理Agent
│   │   ├── sentiment.py         # 情绪分析Agent
│   │   ├── state.py            # Agent状态管理
│   │   ├── technicals.py       # 技术分析Agent
│   │   └── valuation.py        # 估值分析Agent
│   ├── data/                   # 数据存储目录
│   │   ├── sentiment_cache.json # 情绪分析缓存
│   │   └── stock_news/         # 股票新闻数据
│   ├── tools/                  # 工具和功能模块
│   │   ├── api.py              # API接口和数据获取
│   │   ├── data_analyzer.py    # 数据分析工具
│   │   ├── news_crawler.py     # 新闻爬取工具
│   │   ├── openrouter_config.py # OpenRouter配置
│   │   └── test_*.py           # 测试文件
│   ├── utils/                  # 通用工具函数
│   ├── backtester.py          # 回测系统
│   └── main.py                # 主程序入口
├── logs/                      # 日志文件目录
│   ├── api_calls_*.log        # API调用日志
│   └── backtest_*.log         # 回测结果日志
├── .env                       # 环境变量配置
├── .env.example              # 环境变量示例
├── poetry.lock               # Poetry依赖锁定文件
├── pyproject.toml            # Poetry项目配置
└── README.md                 # 项目文档
```

## 贡献指南

欢迎贡献代码！请按照以下步骤进行：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证信息

本项目采用 MIT 开源许可证，具体条款请参阅项目根目录下的 LICENSE 文件。

主要条款包括：
- 允许自由使用、复制、修改、合并、出版发行、散布、再授权及销售软件及其副本
- 允许修改源代码，但必须在所有副本中包含版权声明和许可声明
- 软件按"原样"提供，不提供任何形式的担保

## 致谢与参考项目

本项目基于以下开源项目进行修改和扩展，特此致谢：

1. [ai-hedge-fund](https://github.com/virattt/ai-hedge-fund.git)
   - 提供了基础的AI投资系统框架
   - 实现了核心的agent协作机制
   - 包含完整的回测系统实现

2. [24mlight/A_Share_investment_Agent](https://github.com/24mlight/A_Share_investment_Agent.git)
   - 提供了A股市场适配方案
   - 实现了akshare数据接口集成
   - 包含中文文档和本地化支持

我们衷心感谢原作者的出色工作和启发，这些项目为我们针对A股市场的适配和改进提供了坚实的基础。

## 项目详细说明

### 系统架构设计

本项目采用模块化的多Agent架构，每个Agent都有明确的职责分工。系统架构图如下：

```
市场数据分析 → [技术/基本面/情绪/估值分析] → 风险管理 → 投资组合管理 → 交易决策
```

#### 各Agent功能说明

1. **市场数据分析Agent**

   - 系统入口，负责数据采集和预处理
   - 通过akshare API获取A股市场数据
   - 数据来源包括：
     - 东方财富
     - 新浪财经
     - 同花顺

2. **技术分析Agent**

   - 分析以下技术指标：
     - 价格趋势
     - 成交量
     - 动量指标
   - 生成技术分析交易信号
   - 关注短期市场走势

3. **基本面分析Agent**

   - 分析公司财务指标：
     - 盈利能力
     - 成长性
     - 财务健康状况
   - 评估公司长期发展潜力
   - 生成基本面交易信号

4. **情绪分析Agent**

   - 分析市场新闻和舆论
   - 评估市场情绪
   - 生成情绪交易信号
   - 支持多数据源：
     - 新浪财经
     - 东方财富
     - 雪球

5. **估值分析Agent**

   - 进行公司估值分析
   - 评估股票内在价值
   - 主要估值方法：
     - DCF模型
     - 相对估值法
     - 市场比较法

6. **风险管理Agent**

   - 整合各Agent信号
   - 评估潜在风险
   - 设置风险控制参数：
     - 最大持仓限制
     - 止损止盈水平
     - 交易规模限制

7. **投资组合管理Agent**
   - 最终决策者
   - 综合考虑：
     - 各Agent信号
     - 风险因素
     - 投资组合状态
   - 生成交易决策：
     - 买入
     - 卖出
     - 持有

### 数据处理流程

#### 数据类型说明

1. **市场数据**

   ```python
   {
       "market_cap": float,        # 总市值
       "volume": float,            # 成交量
       "average_volume": float,    # 平均成交量
       "fifty_two_week_high": float,  # 52周最高价
       "fifty_two_week_low": float    # 52周最低价
   }
   ```

2. **财务指标数据**

   ```python
   {
       # 市场数据
       "market_cap": float,          # 总市值
       "float_market_cap": float,    # 流通市值

       # 盈利数据
       "revenue": float,             # 营业总收入
       "net_income": float,          # 净利润
       "return_on_equity": float,    # 净资产收益率
       "net_margin": float,          # 销售净利率
       "operating_margin": float,    # 营业利润率

       # 增长指标
       "revenue_growth": float,      # 主营业务收入增长率
       "earnings_growth": float,     # 净利润增长率
       "book_value_growth": float,   # 净资产增长率

       # 财务健康指标
       "current_ratio": float,       # 流动比率
       "debt_to_equity": float,      # 资产负债率
       "free_cash_flow_per_share": float,  # 每股经营性现金流
       "earnings_per_share": float,  # 每股收益

       # 估值比率
       "pe_ratio": float,           # 市盈率（动态）
       "price_to_book": float,      # 市净率
       "price_to_sales": float      # 市销率
   }
   ```

3. **财务报表数据**

   ```python
   {
       "net_income": float,          # 净利润
       "operating_revenue": float,    # 营业总收入
       "operating_profit": float,     # 营业利润
       "working_capital": float,      # 营运资金
       "depreciation_and_amortization": float,  # 折旧和摊销
       "capital_expenditure": float,  # 资本支出
       "free_cash_flow": float       # 自由现金流
   }
   ```

4. **交易信号数据**

   ```python
   {
       "action": str,               # 交易动作：买入/卖出/持有
       "quantity": int,             # 交易数量
       "confidence": float,         # 置信度 (0-1)
       "agent_signals": [           # 各Agent信号
           {
               "agent": str,        # Agent名称
               "signal": str,       # 信号类型：看涨/看跌/中性
               "confidence": float  # 置信度 (0-1)
           }
       ],
       "reasoning": str            # 决策理由
   }
   ```

#### 数据处理流程

1. **数据采集**

   - 通过akshare API获取以下数据：
     - 实时行情数据
     - 历史行情数据
     - 财务指标数据
     - 财务报表数据
   - 通过新浪财经API获取新闻数据
   - 数据标准化处理

2. **数据分析**

   - 技术分析：
     - 计算技术指标
     - 分析价格模式
     - 生成交易信号
   - 基本面分析：
     - 分析财务报表
     - 评估公司基本面
     - 生成交易信号
   - 情绪分析：
     - 分析市场新闻
     - 评估市场情绪
     - 生成交易信号
   - 估值分析：
     - 计算估值指标
     - 进行DCF估值
     - 生成交易信号

3. **风险管理**

   - 评估市场风险
   - 计算头寸规模
   - 设置止损止盈
   - 控制投资组合风险

4. **投资决策**

   - 综合各Agent信号
   - 评估市场状况
   - 考虑投资组合状态
   - 生成最终交易决策

5. **数据存储**

   - 情绪分析结果缓存
   - 新闻数据存储
   - 日志文件记录
   - API调用记录

6. **系统监控**

   - API调用监控
   - Agent分析追踪
   - 决策过程记录
   - 回测结果评估

### Agent协作机制

#### 信息共享

- 所有Agent共享同一个状态对象
- 通过消息传递机制进行通信
- 每个Agent都可以访问必要的历史数据

#### 决策权重

投资组合管理Agent在做决策时考虑不同信号的权重：

- 估值分析：35%
- 基本面分析：30% 
- 技术分析：25%
- 情绪分析：10%

#### 风险控制

- 强制性风险限制
- 最大持仓限制
- 交易规模限制
- 止损和止盈设置

#### 系统特点

1. **模块化设计**
   - 每个Agent都是独立的模块
   - 易于维护和升级
   - 可以单独测试和优化

2. **可扩展性**
   - 可以轻松添加新的分析师
   - 支持添加新的数据源
   - 可以扩展决策策略

3. **风险管理**
   - 多层次的风险控制
   - 实时风险评估
   - 自动止损机制

4. **智能决策**
   - 基于多维度分析
   - 考虑多个市场因素
   - 动态调整策略

#### 未来展望

1. **数据源扩展**
   - 添加更多A股数据源
   - 接入更多财经数据平台
   - 增加社交媒体情绪数据
   - 扩展到港股、美股市场

2. **功能增强**
   - 添加更多技术指标
   - 实现自动化回测
   - 支持多股票组合管理

3. **性能优化**
   - 提高数据处理效率
   - 优化决策算法
   - 增加并行处理能力
### 情感分析功能

情感分析代理（Sentiment Agent）是系统中的关键组件之一，负责分析市场新闻和舆论对股票的潜在影响。

#### 功能特点

1. **新闻数据采集**
   - 自动抓取最新的股票相关新闻
   - 支持多个新闻源
   - 实时更新新闻数据

2. **情感分析处理**
   - 使用先进的AI模型分析新闻情感
   - 情感分数范围：-1（极其消极）到1（极其积极）
   - 考虑新闻的重要性和时效性

3. **交易信号生成**
   - 基于情感分析结果生成交易信号
   - 包含信号类型（看涨/看跌）
   - 提供置信度评估
   - 附带详细的分析理由

#### 情感分数说明

| 分数范围 | 情感等级 | 典型场景 |
|----------|----------|----------|
| 1.0 | 极其积极 | 重大利好消息、超预期业绩、行业政策支持 |
| 0.5 到 0.9 | 积极 | 业绩增长、新项目落地、获得订单 |
| 0.1 到 0.4 | 轻微积极 | 小额合同签订、日常经营正常 |
| 0.0 | 中性 | 日常公告、人事变动、无重大影响的新闻 |
| -0.1 到 -0.4 | 轻微消极 | 小额诉讼、非核心业务亏损 |
| -0.5 到 -0.9 | 消极 | 业绩下滑、重要客户流失、行业政策收紧 |
| -1.0 | 极其消极 | 重大违规、核心业务严重亏损、被监管处罚 |

#### 结果展示
![情感分析结果示例](https://github.com/user-attachments/assets/c281b8c3-d8e6-431e-a05e-d309d306e967)

### 项目信息

#### 基本信息
- **描述**: 无描述信息
- **网站**: 无
- **主题**: 无

#### 资源
- **文档**: README.md
- **许可证**: MIT 许可证

#### 项目活跃度
- **星标**: 320
- **关注者**: 6
- **分支**: 95

#### 发布信息
- **版本发布**: 无
- **软件包发布**: 无

#### 语言分布
| 语言 | 占比 |
|------|------|
| Python | 82.0% |
| PowerShell | 12.5% |
| Roff | 2.6% |
| C | 2.3% |
| Batchfile | 0.6% |
