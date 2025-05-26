"""
AI Stock Screener - Batch Processing Architecture
Reconstructed from single-stock analysis system for screening hundreds of stocks
"""

import asyncio
import concurrent.futures
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import time
from pathlib import Path
import json

# Core data structures
@dataclass
class StockAnalysis:
    symbol: str
    name: str
    composite_score: float
    agent_signals: Dict[str, Dict]
    key_reasons: List[str]
    risk_factors: List[str]
    current_price: float
    target_price: Optional[float] = None
    upside_potential: Optional[str] = None
    
@dataclass
class ScreeningConfig:
    stock_universe: str = "CSI300"  # CSI300, CSI500, ALL_A_SHARES
    min_market_cap: float = 1_000_000_000  # 10亿
    min_daily_volume: float = 10_000_000   # 1000万
    max_pe_ratio: float = 100
    min_liquidity_days: int = 250
    exclude_st_stocks: bool = True
    max_stocks_full_analysis: int = 50
    target_top_picks: int = 10

class StockUniverse:
    """Manage stock universe and basic filtering"""
    
    def __init__(self, config: ScreeningConfig):
        self.config = config
        
    def get_stock_list(self) -> List[str]:
        """Get initial stock universe"""
        try:
            if self.config.stock_universe == "CSI300":
                # Fetch CSI300 constituents
                import akshare as ak
                df = ak.index_stock_cons("000300")
                return df['品种代码'].tolist()
            elif self.config.stock_universe == "CSI500":
                df = ak.index_stock_cons("000905")
                return df['品种代码'].tolist()
            else:
                # All A-shares (be careful with API limits!)
                df = ak.stock_zh_a_spot_em()
                return df['代码'].tolist()
        except Exception as e:
            logging.error(f"Error fetching stock universe: {e}")
            return []

class QuickFilter:
    """First stage filtering to eliminate obvious non-candidates"""
    
    def __init__(self, config: ScreeningConfig):
        self.config = config
        
    def filter_stocks(self, symbols: List[str]) -> List[str]:
        """Apply basic financial and liquidity filters"""
        filtered = []
        
        try:
            import akshare as ak
            
            # Get market overview data
            market_data = ak.stock_zh_a_spot_em()
            
            for symbol in symbols:
                stock_info = market_data[market_data['代码'] == symbol]
                if stock_info.empty:
                    continue
                    
                stock = stock_info.iloc[0]
                
                # Apply filters
                market_cap = float(stock.get('总市值', 0))
                volume = float(stock.get('成交额', 0))
                pe_ratio = float(stock.get('市盈率-动态', 999))
                
                # Check if stock meets criteria
                if (market_cap >= self.config.min_market_cap and
                    volume >= self.config.min_daily_volume and
                    0 < pe_ratio <= self.config.max_pe_ratio and
                    (not self.config.exclude_st_stocks or 'ST' not in stock.get('名称', ''))):
                    filtered.append(symbol)
                    
        except Exception as e:
            logging.error(f"Error in quick filtering: {e}")
            return symbols[:100]  # Fallback to first 100
            
        logging.info(f"Quick filter: {len(symbols)} -> {len(filtered)} stocks")
        return filtered[:200]  # Limit for technical screening

class TechnicalScreener:
    """Second stage technical analysis screening"""
    
    def __init__(self):
        self.weight_factors = {
            'momentum_score': 0.3,
            'trend_score': 0.3,
            'volatility_score': 0.2,
            'volume_score': 0.2
        }
        
    def screen_stocks(self, symbols: List[str]) -> List[Tuple[str, float]]:
        """Apply technical analysis and score stocks"""
        results = []
        
        # Use parallel processing for technical analysis
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = {
                executor.submit(self._analyze_single_stock, symbol): symbol 
                for symbol in symbols
            }
            
            for future in concurrent.futures.as_completed(futures):
                symbol = futures[future]
                try:
                    tech_score = future.result(timeout=30)
                    if tech_score is not None:
                        results.append((symbol, tech_score))
                except Exception as e:
                    logging.warning(f"Technical analysis failed for {symbol}: {e}")
                    
        # Sort by technical score and return top candidates
        results.sort(key=lambda x: x[1], reverse=True)
        top_count = min(50, len(results))
        
        logging.info(f"Technical screening: {len(symbols)} -> {top_count} stocks")
        return results[:top_count]
    
    def _analyze_single_stock(self, symbol: str) -> Optional[float]:
        """Analyze single stock technical indicators"""
        try:
            from src.tools.api import get_price_history
            
            # Get price data
            end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            
            df = get_price_history(symbol, start_date, end_date)
            if df is None or len(df) < 20:
                return None
                
            # Calculate technical indicators
            scores = {}
            
            # Momentum score
            returns = df['close'].pct_change()
            momentum_20d = returns.rolling(20).sum()
            scores['momentum_score'] = min(max(momentum_20d.iloc[-1] * 5 + 0.5, 0), 1)
            
            # Trend score (MA analysis)
            ma5 = df['close'].rolling(5).mean()
            ma20 = df['close'].rolling(20).mean()
            trend_strength = (ma5.iloc[-1] / ma20.iloc[-1] - 1) * 10 + 0.5
            scores['trend_score'] = min(max(trend_strength, 0), 1)
            
            # Volume score
            vol_ratio = df['volume'].iloc[-5:].mean() / df['volume'].iloc[-20:].mean()
            scores['volume_score'] = min(max((vol_ratio - 0.5) * 2, 0), 1)
            
            # Volatility score (lower is better)
            volatility = returns.std() * np.sqrt(252)
            scores['volatility_score'] = max(0, 1 - volatility * 2)
            
            # Composite technical score
            composite = sum(
                scores[factor] * weight 
                for factor, weight in self.weight_factors.items()
            )
            
            return composite
            
        except Exception as e:
            logging.warning(f"Technical analysis error for {symbol}: {e}")
            return None

class BatchAnalyzer:
    """Main batch analysis engine using existing agents"""
    
    def __init__(self, config: ScreeningConfig):
        self.config = config
        
    async def analyze_stocks(self, stock_candidates: List[Tuple[str, float]]) -> List[StockAnalysis]:
        """Run full multi-agent analysis on top candidates"""
        
        # Import existing agents
        from src.main import run_hedge_fund
        
        results = []
        total_stocks = len(stock_candidates)
        
        # Use semaphore to limit concurrent API calls
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent analyses
        
        async def analyze_single(symbol_score: Tuple[str, float]) -> Optional[StockAnalysis]:
            symbol, tech_score = symbol_score
            async with semaphore:
                try:
                    # Add delay to respect API limits
                    await asyncio.sleep(2)
                    
                    # Run full analysis using existing system
                    end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
                    
                    portfolio = {"cash": 100000, "stock": 0}
                    decision_result = await asyncio.get_event_loop().run_in_executor(
                        None,
                        run_hedge_fund,
                        symbol,
                        start_date, 
                        end_date,
                        portfolio,
                        False,  # show_reasoning
                        5       # num_of_news
                    )
                    
                    if decision_result:
                        return self._parse_decision_result(symbol, decision_result, tech_score)
                        
                except Exception as e:
                    logging.error(f"Analysis failed for {symbol}: {e}")
                    return None
        
        # Run analyses concurrently
        tasks = [analyze_single(candidate) for candidate in stock_candidates]
        analysis_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        for result in analysis_results:
            if isinstance(result, StockAnalysis):
                results.append(result)
                
        return results
    
    def _parse_decision_result(self, symbol: str, decision_result: str, tech_score: float) -> StockAnalysis:
        """Parse decision result and create StockAnalysis object"""
        try:
            if isinstance(decision_result, str):
                decision_result = decision_result.replace('```json', '').replace('```', '').strip()
                decision = json.loads(decision_result)
            else:
                decision = decision_result
                
            # Calculate composite score
            agent_signals = {}
            weights = {'technical': 0.25, 'fundamental': 0.30, 'sentiment': 0.10, 'valuation': 0.35}
            composite_score = 0
            
            for signal in decision.get('agent_signals', []):
                agent_type = signal.get('agent', '').lower()
                if 'technical' in agent_type:
                    agent_type = 'technical'
                elif 'fundamental' in agent_type:
                    agent_type = 'fundamental'
                elif 'sentiment' in agent_type:
                    agent_type = 'sentiment'
                elif 'valuation' in agent_type:
                    agent_type = 'valuation'
                else:
                    continue
                    
                confidence = float(signal.get('confidence', 0))
                if isinstance(confidence, str):
                    confidence = float(confidence.replace('%', '')) / 100
                    
                agent_signals[agent_type] = {
                    'signal': signal.get('signal', 'neutral'),
                    'confidence': confidence
                }
                
                if agent_type in weights:
                    composite_score += confidence * weights[agent_type] * 100
            
            # Generate reasons based on signals
            key_reasons = self._generate_key_reasons(agent_signals, decision)
            risk_factors = self._generate_risk_factors(agent_signals)
            
            return StockAnalysis(
                symbol=symbol,
                name=self._get_stock_name(symbol),
                composite_score=composite_score,
                agent_signals=agent_signals,
                key_reasons=key_reasons,
                risk_factors=risk_factors,
                current_price=0.0  # TODO: Get current price
            )
            
        except Exception as e:
            logging.error(f"Error parsing decision for {symbol}: {e}")
            return None
    
    def _generate_key_reasons(self, signals: Dict, decision: Dict) -> List[str]:
        """Generate key investment reasons based on signals"""
        reasons = []
        
        # Technical reasons
        if signals.get('technical', {}).get('signal') == 'bullish':
            reasons.append("技术面显示积极信号，价格动量和趋势指标向好")
            
        # Fundamental reasons  
        if signals.get('fundamental', {}).get('signal') == 'bullish':
            reasons.append("基本面强劲，盈利能力和财务健康状况良好")
            
        # Valuation reasons
        if signals.get('valuation', {}).get('signal') == 'bullish':
            reasons.append("估值分析显示股票被低估，具有上涨潜力")
            
        # Sentiment reasons
        if signals.get('sentiment', {}).get('signal') == 'bullish':
            reasons.append("市场情绪积极，新闻和舆论支持")
            
        return reasons or ["综合分析显示投资价值"]
    
    def _generate_risk_factors(self, signals: Dict) -> List[str]:
        """Generate risk factors based on signals"""
        risks = []
        
        if signals.get('technical', {}).get('signal') == 'bearish':
            risks.append("技术面存在风险信号")
            
        if signals.get('fundamental', {}).get('signal') == 'bearish':
            risks.append("基本面指标显示潜在风险")
            
        if signals.get('valuation', {}).get('signal') == 'bearish':
            risks.append("估值偏高，存在调整风险")
            
        return risks or ["市场系统性风险"]
    
    def _get_stock_name(self, symbol: str) -> str:
        """Get stock name from symbol"""
        try:
            import akshare as ak
            df = ak.stock_zh_a_spot_em()
            stock_info = df[df['代码'] == symbol]
            if not stock_info.empty:
                return stock_info.iloc[0]['名称']
        except:
            pass
        return f"Stock_{symbol}"

class RankingEngine:
    """Rank and select top stocks"""
    
    def rank_stocks(self, analyses: List[StockAnalysis], target_count: int = 10) -> List[StockAnalysis]:
        """Rank stocks by composite score and return top picks"""
        
        # Sort by composite score
        analyses.sort(key=lambda x: x.composite_score, reverse=True)
        
        # Additional ranking factors for tie-breaking
        for analysis in analyses:
            # Boost score for bullish valuation signals
            if analysis.agent_signals.get('valuation', {}).get('signal') == 'bullish':
                analysis.composite_score += 2
                
            # Boost for strong fundamentals
            if analysis.agent_signals.get('fundamental', {}).get('signal') == 'bullish':
                analysis.composite_score += 1
        
        # Re-sort after adjustments
        analyses.sort(key=lambda x: x.composite_score, reverse=True)
        
        return analyses[:target_count]

class StockScreener:
    """Main screening orchestrator"""
    
    def __init__(self, config: ScreeningConfig = None):
        self.config = config or ScreeningConfig()
        self.universe = StockUniverse(self.config)
        self.quick_filter = QuickFilter(self.config)
        self.technical_screener = TechnicalScreener()
        self.batch_analyzer = BatchAnalyzer(self.config)
        self.ranking_engine = RankingEngine()
        
    async def run_screening(self) -> List[StockAnalysis]:
        """Run complete stock screening process"""
        
        start_time = time.time()
        logging.info("Starting stock screening process...")
        
        # Stage 1: Get stock universe
        print("🔍 获取股票池...")
        all_stocks = self.universe.get_stock_list()
        print(f"股票池总数: {len(all_stocks)}")
        
        # Stage 2: Quick filter
        print("⚡ 快速筛选中...")
        filtered_stocks = self.quick_filter.filter_stocks(all_stocks)
        print(f"快速筛选后: {len(filtered_stocks)} 只")
        
        # Stage 3: Technical screening
        print("📊 技术面筛选中...")
        tech_candidates = self.technical_screener.screen_stocks(filtered_stocks)
        print(f"技术面筛选后: {len(tech_candidates)} 只")
        
        # Stage 4: Full analysis
        print("🤖 AI全面分析中...")
        analysis_results = await self.batch_analyzer.analyze_stocks(tech_candidates)
        print(f"全面分析完成: {len(analysis_results)} 只")
        
        # Stage 5: Ranking
        print("🏆 综合排名中...")
        top_picks = self.ranking_engine.rank_stocks(analysis_results, self.config.target_top_picks)
        
        total_time = time.time() - start_time
        print(f"✅ 筛选完成! 耗时: {total_time:.1f}秒")
        print(f"🎯 精选推荐: {len(top_picks)} 只")
        
        return top_picks

# Usage example and CLI interface
async def main():
    """Main entry point for stock screening"""
    
    # Configuration
    config = ScreeningConfig(
        stock_universe="CSI300",
        min_market_cap=5_000_000_000,  # 50亿市值
        target_top_picks=10
    )
    
    # Run screening
    screener = StockScreener(config)
    top_stocks = await screener.run_screening()
    
    # Display results
    print("\n" + "="*80)
    print("🏆 TOP 10 STOCK RECOMMENDATIONS")
    print("="*80)
    
    for i, stock in enumerate(top_stocks, 1):
        print(f"\n📈 #{i} {stock.symbol} - {stock.name}")
        print(f"综合评分: {stock.composite_score:.1f}/100")
        print(f"当前价格: ¥{stock.current_price:.2f}")
        
        print("\n🔍 各模块信号:")
        for agent, signal_data in stock.agent_signals.items():
            signal = signal_data['signal']
            confidence = signal_data['confidence']
            emoji = "🟢" if signal == 'bullish' else "🔴" if signal == 'bearish' else "🟡"
            print(f"  {emoji} {agent}: {signal} ({confidence:.1%})")
        
        print(f"\n💡 关键原因:")
        for reason in stock.key_reasons:
            print(f"  • {reason}")
            
        if stock.risk_factors:
            print(f"\n⚠️ 风险因素:")
            for risk in stock.risk_factors:
                print(f"  • {risk}")
        
        print("-" * 60)

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    asyncio.run(main())
