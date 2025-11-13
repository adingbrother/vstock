from typing import Dict, List, Optional
import numpy as np
from loguru import logger
from quant_web.core.const import FACTOR_WEIGHTS


class FactorModel:
    """多因子评分模型"""
    
    def __init__(self):
        # stats could be computed from history; in skeleton we provide dummy stats
        self.stats = {k: {"mean": 0.0, "std": 1.0} for k in FACTOR_WEIGHTS}
    
    def _calc_returns_factor(self, stock: str, results: List[Dict]) -> float:
        """计算收益因子
        
        Args:
            stock: 股票代码
            results: 策略回测结果列表
            
        Returns:
            收益因子得分
        """
        try:
            # 计算平均收益率
            returns = []
            for result in results:
                if stock in result.get('stocks', {}):
                    stock_data = result['stocks'][stock]
                    # 计算收益率
                    if 'total_return' in stock_data:
                        returns.append(stock_data['total_return'])
                    elif 'close_prices' in stock_data and len(stock_data['close_prices']) > 1:
                        # 从价格计算收益率
                        prices = stock_data['close_prices']
                        return_rate = (prices[-1] - prices[0]) / prices[0]
                        returns.append(return_rate)
            
            return np.mean(returns) if returns else 0
        except Exception as e:
            logger.error(f"计算收益因子失败 {stock}: {str(e)}")
            return 0
    
    def _calc_stability_factor(self, stock: str, results: List[Dict]) -> float:
        """计算稳定因子（波动率的负值）"""
        try:
            # 计算平均波动率（波动率越小越稳定）
            volatilities = []
            for result in results:
                if stock in result.get('stocks', {}):
                    stock_data = result['stocks'][stock]
                    # 计算波动率
                    if 'volatility' in stock_data:
                        volatilities.append(stock_data['volatility'])
                    elif 'daily_returns' in stock_data and len(stock_data['daily_returns']) > 1:
                        vol = np.std(stock_data['daily_returns'])
                        volatilities.append(vol)
                    elif 'close_prices' in stock_data and len(stock_data['close_prices']) > 1:
                        # 从价格计算收益率然后计算波动率
                        prices = stock_data['close_prices']
                        returns = np.diff(prices) / prices[:-1]
                        vol = np.std(returns)
                        volatilities.append(vol)
            
            return -np.mean(volatilities) if volatilities else 0
        except Exception as e:
            logger.error(f"计算稳定因子失败 {stock}: {str(e)}")
            return 0
    
    def _calc_activity_factor(self, stock: str, results: List[Dict]) -> float:
        """计算活跃因子（成交量和涨跌幅的综合）"""
        try:
            activities = []
            for result in results:
                if stock in result.get('stocks', {}):
                    stock_data = result['stocks'][stock]
                    activity_score = 0
                    
                    if 'volume' in stock_data and len(stock_data['volume']) > 1:
                        # 成交量变化率
                        volumes = stock_data['volume']
                        vol_change = np.mean(np.diff(volumes) / volumes[:-1])
                        activity_score += vol_change
                    
                    if 'price_changes' in stock_data:
                        # 涨跌幅绝对值的平均值
                        avg_change = np.mean(np.abs(stock_data['price_changes']))
                        activity_score += avg_change
                    elif 'daily_returns' in stock_data:
                        # 日收益率绝对值的平均值
                        avg_abs_return = np.mean(np.abs(stock_data['daily_returns']))
                        activity_score += avg_abs_return
                    
                    activities.append(activity_score)
            
            return np.mean(activities) if activities else 0
        except Exception as e:
            logger.error(f"计算活跃因子失败 {stock}: {str(e)}")
            return 0
    
    def _calc_quality_factor(self, stock: str, results: List[Dict]) -> float:
        """计算质量因子（胜率、夏普率等综合）"""
        try:
            qualities = []
            for result in results:
                if stock in result.get('stocks', {}):
                    stock_data = result['stocks'][stock]
                    quality_score = 0
                    
                    if 'win_rate' in stock_data:
                        quality_score += stock_data['win_rate'] - 0.5  # 归一化到-0.5到0.5
                    
                    if 'sharpe_ratio' in stock_data:
                        # 夏普率通常在0-3之间，归一化到-1到1
                        normalized_sharpe = min(1, max(-1, stock_data['sharpe_ratio'] / 1.5))
                        quality_score += normalized_sharpe / 2
                    
                    if 'max_drawdown' in stock_data:
                        # 最大回撤越小越好，归一化
                        normalized_dd = min(1, max(-1, -stock_data['max_drawdown'] / 0.5))
                        quality_score += normalized_dd / 2
                    
                    qualities.append(quality_score)
            
            return np.mean(qualities) if qualities else 0
        except Exception as e:
            logger.error(f"计算质量因子失败 {stock}: {str(e)}")
            return 0
    
    def _calc(self, factor_name: str, stock: str, results: List[Dict]) -> float:
        """计算特定因子的值"""
        if factor_name == '收益因子':
            return self._calc_returns_factor(stock, results)
        elif factor_name == '稳定因子':
            return self._calc_stability_factor(stock, results)
        elif factor_name == '活跃因子':
            return self._calc_activity_factor(stock, results)
        elif factor_name == '质量因子':
            return self._calc_quality_factor(stock, results)
        else:
            logger.error(f"未知因子: {factor_name}")
            return 0
    
    def score(self, stock: str, results: list) -> float:
        """计算股票的综合评分（0-100）"""
        try:
            raw = {f: self._calc(f, stock, results) for f in FACTOR_WEIGHTS}
            z_score = {k: (v - self.stats[k]['mean']) / (self.stats[k]['std'] or 1.0) for k, v in raw.items()}
            weighted = sum(z_score[f] * FACTOR_WEIGHTS[f] for f in FACTOR_WEIGHTS)
            return max(0.0, min(100.0, 50 + 10 * weighted))
        except Exception as e:
            logger.error(f"计算综合评分失败 {stock}: {str(e)}")
            return 0
    
    def update_stats(self, stock_pool: List[str], results: List[Dict]) -> None:
        """更新因子统计信息"""
        try:
            all_scores = {factor: [] for factor in FACTOR_WEIGHTS}
            
            # 计算所有股票的各个因子值
            for stock in stock_pool:
                for factor in FACTOR_WEIGHTS:
                    score = self._calc(factor, stock, results)
                    all_scores[factor].append(score)
            
            # 更新均值和标准差
            for factor, scores in all_scores.items():
                if scores:
                    self.stats[factor]['mean'] = np.mean(scores)
                    self.stats[factor]['std'] = np.std(scores) if len(scores) > 1 else 1
            
            logger.info(f"更新因子统计信息完成")
        except Exception as e:
            logger.error(f"更新因子统计信息失败: {str(e)}")
    
    def get_factor_scores(self, stock: str, results: List[Dict]) -> Dict[str, float]:
        """获取股票的各因子得分"""
        factor_scores = {}
        for factor in FACTOR_WEIGHTS:
            # 获取标准化后的因子得分
            raw_score = self._calc(factor, stock, results)
            mean = self.stats[factor]['mean']
            std = self.stats[factor]['std']
            if std != 0:
                z_score = (raw_score - mean) / std
            else:
                z_score = 0
            factor_scores[factor] = z_score
        return factor_scores
