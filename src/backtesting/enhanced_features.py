# src/backtesting/enhanced_features.py
"""
CARACTERÍSTICAS AVANZADAS DEL BACKTESTER CRYPTONITA

Funciones adicionales para análisis profundo y visualizaciones
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import json

class BacktestAnalyzer:
    """Analizador avanzado de resultados de backtesting"""
    
    def __init__(self, backtester):
        self.backtester = backtester
        self.stats = backtester.final_statistics
        self.trades_df = pd.DataFrame(backtester.trade_history)
        self.portfolio_df = pd.DataFrame(backtester.portfolio_history)
        
    def analyze_trade_patterns(self):
        """Analiza patrones en los trades"""
        if self.trades_df.empty:
            return {}
        
        # Análisis por ticker
        ticker_analysis = {}
        for ticker in self.trades_df['ticker'].unique():
            ticker_trades = self.trades_df[self.trades_df['ticker'] == ticker]
            buy_trades = ticker_trades[ticker_trades['action'] == 'BUY']
            sell_trades = ticker_trades[ticker_trades['action'] == 'SELL']
            
            if len(sell_trades) > 0:
                total_pnl = sell_trades['pnl'].sum()
                win_rate = (sell_trades['pnl'] > 0).mean() * 100
                avg_hold_days = sell_trades['hold_days'].mean()
                
                ticker_analysis[ticker] = {
                    'total_trades': len(buy_trades),
                    'total_pnl': total_pnl,
                    'win_rate': win_rate,
                    'avg_hold_days': avg_hold_days,
                    'best_trade': sell_trades['pnl'].max(),
                    'worst_trade': sell_trades['pnl'].min()
                }
        
        return ticker_analysis
    
    def calculate_rolling_metrics(self, window_days=30):
        """Calcula métricas móviles"""
        if self.portfolio_df.empty:
            return {}
        
        df = self.portfolio_df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Calcular retornos diarios
        df['daily_return'] = df['portfolio_value'].pct_change()
        
        # Métricas móviles
        df['rolling_volatility'] = df['daily_return'].rolling(window_days).std() * np.sqrt(252)
        df['rolling_sharpe'] = (df['daily_return'].rolling(window_days).mean() * 252) / df['rolling_volatility']
        df['rolling_max'] = df['portfolio_value'].rolling(window_days).max()
        df['rolling_drawdown'] = (df['portfolio_value'] - df['rolling_max']) / df['rolling_max']
        
        return df
    
    def monthly_performance_analysis(self):
        """Análisis de rendimiento mensual"""
        if self.portfolio_df.empty:
            return {}
        
        df = self.portfolio_df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Agrupar por mes
        monthly = df.resample('M').last()
        monthly['monthly_return'] = monthly['portfolio_value'].pct_change() * 100
        
        monthly_stats = {
            'best_month': {
                'return': monthly['monthly_return'].max(),
                'date': monthly['monthly_return'].idxmax().strftime('%Y-%m')
            },
            'worst_month': {
                'return': monthly['monthly_return'].min(),
                'date': monthly['monthly_return'].idxmin().strftime('%Y-%m')
            },
            'positive_months': (monthly['monthly_return'] > 0).sum(),
            'negative_months': (monthly['monthly_return'] < 0).sum(),
            'avg_monthly_return': monthly['monthly_return'].mean(),
            'monthly_volatility': monthly['monthly_return'].std()
        }
        
        return monthly_stats, monthly
    
    def risk_analysis(self):
        """Análisis de riesgo detallado"""
        if self.portfolio_df.empty:
            return {}
        
        df = self.portfolio_df.copy()
        df['daily_return'] = df['portfolio_value'].pct_change()
        daily_returns = df['daily_return'].dropna()
        
        # VaR (Value at Risk)
        var_95 = np.percentile(daily_returns, 5)
        var_99 = np.percentile(daily_returns, 1)
        
        # Expected Shortfall (CVaR)
        cvar_95 = daily_returns[daily_returns <= var_95].mean()
        cvar_99 = daily_returns[daily_returns <= var_99].mean()
        
        # Calmar Ratio
        calmar_ratio = (self.stats['total_return_pct'] / self.stats['days_simulated'] * 365) / abs(self.stats['max_drawdown_pct']) if self.stats['max_drawdown_pct'] != 0 else float('inf')
        
        # Sortino Ratio
        negative_returns = daily_returns[daily_returns < 0]
        downside_deviation = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0
        sortino_ratio = (daily_returns.mean() * 252) / downside_deviation if downside_deviation > 0 else float('inf')
        
        return {
            'var_95': var_95 * 100,
            'var_99': var_99 * 100,
            'cvar_95': cvar_95 * 100,
            'cvar_99': cvar_99 * 100,
            'calmar_ratio': calmar_ratio,
            'sortino_ratio': sortino_ratio,
            'skewness': daily_returns.skew(),
            'kurtosis': daily_returns.kurtosis()
        }
    
    def generate_comprehensive_report(self):
        """Genera reporte comprehensivo"""
        
        # Análisis básico
        trade_patterns = self.analyze_trade_patterns()
        monthly_stats, monthly_df = self.monthly_performance_analysis()
        risk_metrics = self.risk_analysis()
        rolling_metrics = self.calculate_rolling_metrics()
        
        # Compilar reporte
        comprehensive_report = {
            'summary': {
                'period': f"{self.backtester.start_date.strftime('%Y-%m-%d')} to {self.backtester.end_date.strftime('%Y-%m-%d')}",
                'initial_capital': self.stats['initial_capital'],
                'final_value': self.stats['final_value'],
                'total_return_pct': self.stats['total_return_pct'],
                'cagr': self._calculate_cagr(),
                'max_drawdown': self.stats['max_drawdown_pct'],
                'sharpe_ratio': self.stats['sharpe_ratio'],
                'total_trades': self.stats['total_trades'],
                'win_rate': self.stats['winning_rate_pct']
            },
            'trade_analysis': trade_patterns,
            'monthly_performance': monthly_stats,
            'risk_metrics': risk_metrics,
            'benchmark_comparison': self._benchmark_comparison()
        }
        
        return comprehensive_report
    
    def _calculate_cagr(self):
        """Calcula Compound Annual Growth Rate"""
        years = self.stats['days_simulated'] / 365.25
        if years > 0:
            cagr = ((self.stats['final_value'] / self.stats['initial_capital']) ** (1/years) - 1) * 100
            return cagr
        return 0
    
    def _benchmark_comparison(self):
        """Compara con benchmarks comunes"""
        benchmarks = {}
        
        # BTC Buy & Hold
        try:
            btc_start = self.backtester.get_price_at_date("BTC-USD", self.backtester.start_date)
            btc_end = self.backtester.get_price_at_date("BTC-USD", self.backtester.end_date)
            if btc_start and btc_end:
                btc_return = ((btc_end / btc_start) - 1) * 100
                benchmarks['BTC_buy_hold'] = {
                    'return': btc_return,
                    'alpha_vs_btc': self.stats['total_return_pct'] - btc_return
                }
        except:
            pass
        
        # ETH Buy & Hold
        try:
            eth_start = self.backtester.get_price_at_date("ETH-USD", self.backtester.start_date)
            eth_end = self.backtester.get_price_at_date("ETH-USD", self.backtester.end_date)
            if eth_start and eth_end:
                eth_return = ((eth_end / eth_start) - 1) * 100
                benchmarks['ETH_buy_hold'] = {
                    'return': eth_return,
                    'alpha_vs_eth': self.stats['total_return_pct'] - eth_return
                }
        except:
            pass
        
        return benchmarks
    
    def print_comprehensive_analysis(self):
        """Imprime análisis comprehensivo"""
        report = self.generate_comprehensive_report()
        
        print("\n" + "📊" * 60)
        print(" ANÁLISIS COMPREHENSIVO CRYPTONITA BOT")
        print("📊" * 60)
        
        # Resumen ejecutivo
        summary = report['summary']
        print(f"\n🎯 RESUMEN EJECUTIVO:")
        print(f"   📅 Período: {summary['period']}")
        print(f"   💰 Capital: ${summary['initial_capital']:,.0f} → ${summary['final_value']:,.0f}")
        print(f"   📈 Retorno Total: {summary['total_return_pct']:+.2f}%")
        print(f"   📊 CAGR: {summary['cagr']:+.2f}%")
        print(f"   ⚡ Sharpe Ratio: {summary['sharpe_ratio']:.2f}")
        print(f"   📉 Max Drawdown: {summary['max_drawdown']:.2f}%")
        
        # Trading performance
        print(f"\n📋 PERFORMANCE DE TRADING:")
        print(f"   🔄 Total Trades: {summary['total_trades']}")
        print(f"   🎯 Win Rate: {summary['win_rate']:.1f}%")
        
        # Análisis por activo
        if report['trade_analysis']:
            print(f"\n🏆 TOP PERFORMERS:")
            sorted_tickers = sorted(report['trade_analysis'].items(), 
                                  key=lambda x: x[1]['total_pnl'], reverse=True)
            
            for ticker, data in sorted_tickers[:5]:
                print(f"   {ticker}: ${data['total_pnl']:+.2f} | {data['win_rate']:.0f}% WR | {data['avg_hold_days']:.0f}d hold")
        
        # Performance mensual
        monthly = report['monthly_performance']
        print(f"\n📆 ANÁLISIS MENSUAL:")
        print(f"   🟢 Meses positivos: {monthly['positive_months']}")
        print(f"   🔴 Meses negativos: {monthly['negative_months']}")
        print(f"   🏆 Mejor mes: {monthly['best_month']['return']:+.1f}% ({monthly['best_month']['date']})")
        print(f"   📉 Peor mes: {monthly['worst_month']['return']:+.1f}% ({monthly['worst_month']['date']})")
        
        # Métricas de riesgo
        risk = report['risk_metrics']
        print(f"\n⚠️ ANÁLISIS DE RIESGO:")
        print(f"   📊 VaR 95%: {risk['var_95']:+.2f}%")
        print(f"   📊 CVaR 95%: {risk['cvar_95']:+.2f}%")
        print(f"   📊 Sortino Ratio: {risk['sortino_ratio']:.2f}")
        print(f"   📊 Calmar Ratio: {risk['calmar_ratio']:.2f}")
        
        # Comparación con benchmarks
        if report['benchmark_comparison']:
            print(f"\n🏁 VS BENCHMARKS:")
            for bench_name, bench_data in report['benchmark_comparison'].items():
                bench_return = bench_data['return']
                alpha = bench_data.get('alpha_vs_btc', bench_data.get('alpha_vs_eth', 0))
                print(f"   {bench_name.replace('_', ' ').title()}: {bench_return:+.1f}% | Alpha: {alpha:+.1f}%")
        
        print("📊" * 60)

def create_visualization_report(backtester, save_path=None):
    """Crea reporte visual con gráficos"""
    
    analyzer = BacktestAnalyzer(backtester)
    
    # Configurar estilo
    plt.style.use('seaborn-v0_8')
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Cryptonita Bot - Backtest Analysis', fontsize=16, fontweight='bold')
    
    # 1. Evolución del portfolio
    portfolio_df = analyzer.portfolio_df.copy()
    portfolio_df['date'] = pd.to_datetime(portfolio_df['date'])
    
    axes[0, 0].plot(portfolio_df['date'], portfolio_df['portfolio_value'], linewidth=2, color='#2E86AB')
    axes[0, 0].axhline(y=backtester.initial_capital, color='red', linestyle='--', alpha=0.7, label='Initial Capital')
    axes[0, 0].set_title('Portfolio Value Evolution')
    axes[0, 0].set_ylabel('Portfolio Value ($)')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. Distribución de retornos diarios
    if not portfolio_df.empty:
        daily_returns = portfolio_df['portfolio_value'].pct_change().dropna() * 100
        axes[0, 1].hist(daily_returns, bins=30, alpha=0.7, color='#A23B72', edgecolor='black')
        axes[0, 1].axvline(daily_returns.mean(), color='red', linestyle='--', label=f'Mean: {daily_returns.mean():.2f}%')
        axes[0, 1].set_title('Daily Returns Distribution')
        axes[0, 1].set_xlabel('Daily Return (%)')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Drawdown
    portfolio_df['cummax'] = portfolio_df['portfolio_value'].cummax()
    portfolio_df['drawdown'] = (portfolio_df['portfolio_value'] - portfolio_df['cummax']) / portfolio_df['cummax'] * 100
    
    axes[1, 0].fill_between(portfolio_df['date'], portfolio_df['drawdown'], 0, 
                           alpha=0.7, color='red', label='Drawdown')
    axes[1, 0].set_title('Portfolio Drawdown')
    axes[1, 0].set_xlabel('Date')
    axes[1, 0].set_ylabel('Drawdown (%)')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. Número de posiciones activas
    axes[1, 1].plot(portfolio_df['date'], portfolio_df['num_positions'], 
                   linewidth=2, color='#F18F01', marker='o', markersize=3)
    axes[1, 1].set_title('Active Positions Over Time')
    axes[1, 1].set_xlabel('Date')
    axes[1, 1].set_ylabel('Number of Positions')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"📊 Gráficos guardados en: {save_path}")
    
    plt.show()
    
    # Imprimir análisis comprehensivo
    analyzer.print_comprehensive_analysis()
    
    return analyzer