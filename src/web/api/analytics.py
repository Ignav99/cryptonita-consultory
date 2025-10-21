# src/web/api/analytics.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys
import os

# Agregar path del proyecto
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.db_connector import create_db_engine

class AnalyticsService:
    """Servicio avanzado de analytics para Cryptonita"""
    
    def __init__(self):
        self.engine = create_db_engine()
    
    def calculate_portfolio_metrics(self, trades_data: List[Dict]) -> Dict:
        """Calcula métricas básicas del portfolio"""
        if not trades_data:
            return {
                "total_trades": 0,
                "total_volume": 0,
                "average_trade_size": 0,
                "buy_sell_ratio": 0,
                "most_active_asset": "N/A"
            }
        
        df = pd.DataFrame(trades_data)
        
        # Métricas básicas
        total_trades = len(df)
        total_volume = df['total_value'].sum()
        average_trade_size = df['total_value'].mean()
        
        # Ratio compra/venta
        buy_trades = len(df[df['action'] == 'BUY'])
        sell_trades = len(df[df['action'] == 'SELL'])
        buy_sell_ratio = buy_trades / sell_trades if sell_trades > 0 else float('inf')
        
        # Activo más activo
        most_active = df['ticker'].value_counts().index[0] if not df.empty else "N/A"
        
        return {
            "total_trades": total_trades,
            "total_volume": round(total_volume, 2),
            "average_trade_size": round(average_trade_size, 2),
            "buy_sell_ratio": round(buy_sell_ratio, 2),
            "most_active_asset": most_active
        }
    
    def calculate_risk_metrics(self, trades_data: List[Dict]) -> Dict:
        """Calcula métricas de riesgo"""
        if not trades_data:
            return {
                "max_single_trade": 0,
                "risk_concentration": 0,
                "daily_var": 0,
                "risk_score": "LOW"
            }
        
        df = pd.DataFrame(trades_data)
        
        # Riesgo máximo por trade
        max_trade = df['total_value'].max()
        
        # Concentración de riesgo (% del trade más grande)
        total_volume = df['total_value'].sum()
        risk_concentration = (max_trade / total_volume * 100) if total_volume > 0 else 0
        
        # VaR diario simplificado (95% percentil)
        daily_var = np.percentile(df['total_value'], 95) if len(df) > 0 else 0
        
        # Score de riesgo
        if risk_concentration > 20:
            risk_score = "HIGH"
        elif risk_concentration > 10:
            risk_score = "MEDIUM"
        else:
            risk_score = "LOW"
        
        return {
            "max_single_trade": round(max_trade, 2),
            "risk_concentration": round(risk_concentration, 2),
            "daily_var": round(daily_var, 2),
            "risk_score": risk_score
        }
    
    def calculate_performance_metrics(self, trades_data: List[Dict]) -> Dict:
        """Calcula métricas de performance detalladas"""
        if not trades_data:
            return {
                "total_return": 0,
                "sharpe_ratio": 0,
                "max_drawdown": 0,
                "win_rate": 0,
                "average_trade_duration": 0,
                "volatility": 0,
                "profit_factor": 0
            }
        
        # Por ahora calculamos métricas simuladas
        # TODO: Implementar cálculos reales cuando tengamos más datos históricos
        
        np.random.seed(42)  # Para resultados consistentes
        
        return {
            "total_return": round(np.random.uniform(-5, 15), 2),
            "sharpe_ratio": round(np.random.uniform(0.5, 2.5), 2),
            "max_drawdown": round(np.random.uniform(-15, -2), 2),
            "win_rate": round(np.random.uniform(45, 75), 2),
            "average_trade_duration": round(np.random.uniform(2, 8), 1),
            "volatility": round(np.random.uniform(10, 25), 2),
            "profit_factor": round(np.random.uniform(1.1, 2.2), 2)
        }
    
    def get_historical_portfolio_data(self, days: int) -> List[Dict]:
        """Obtiene datos históricos del portfolio para gráficos"""
        # Simulamos datos históricos por ahora
        # TODO: Implementar con datos reales de la base de datos
        
        base_value = 10000
        data = []
        
        for i in range(days):
            date = datetime.now() - timedelta(days=days-i-1)
            # Simulamos una evolución realista
            daily_change = np.random.normal(0.002, 0.02)  # 0.2% promedio, 2% volatilidad
            base_value *= (1 + daily_change)
            
            data.append({
                "date": date.isoformat(),
                "portfolio_value": round(base_value, 2),
                "daily_return": round(daily_change * 100, 2)
            })
        
        return data
    
    def analyze_signals(self, signals_data: Dict) -> Dict:
        """Analiza la distribución y calidad de las señales"""
        if not signals_data:
            return {
                "signal_quality": "NO_DATA",
                "market_sentiment": "NEUTRAL",
                "confidence_score": 0,
                "recommendation": "WAIT"
            }
        
        # Contar señales
        buy_count = sum(1 for signal in signals_data.values() if signal == "BUY")
        sell_count = sum(1 for signal in signals_data.values() if signal == "SELL")
        hold_count = sum(1 for signal in signals_data.values() if signal == "HOLD")
        total = len(signals_data)
        
        # Calcular sentiment del mercado
        buy_ratio = buy_count / total if total > 0 else 0
        sell_ratio = sell_count / total if total > 0 else 0
        
        if buy_ratio > 0.6:
            market_sentiment = "BULLISH"
        elif sell_ratio > 0.6:
            market_sentiment = "BEARISH"
        else:
            market_sentiment = "NEUTRAL"
        
        # Score de confianza basado en concentración de señales
        max_signal_ratio = max(buy_ratio, sell_ratio, hold_count/total)
        confidence_score = round(max_signal_ratio * 100, 1)
        
        # Recomendación
        if confidence_score > 70:
            if buy_ratio > sell_ratio:
                recommendation = "STRONG_BUY"
            else:
                recommendation = "STRONG_SELL"
        elif confidence_score > 50:
            recommendation = "MODERATE"
        else:
            recommendation = "WAIT"
        
        return {
            "signal_quality": "HIGH" if confidence_score > 70 else "MEDIUM" if confidence_score > 50 else "LOW",
            "market_sentiment": market_sentiment,
            "confidence_score": confidence_score,
            "recommendation": recommendation,
            "distribution": {
                "buy_percentage": round(buy_ratio * 100, 1),
                "sell_percentage": round(sell_ratio * 100, 1),
                "hold_percentage": round((hold_count/total) * 100, 1)
            }
        }
    
    def get_market_sentiment(self) -> Dict:
        """Obtiene el sentiment general del mercado"""
        try:
            if not self.engine:
                return {"sentiment": "UNKNOWN", "confidence": 0}
            
            # Query para obtener datos recientes de precios
            query = """
            SELECT ticker, close, timestamp
            FROM asset_metrics 
            WHERE timestamp >= NOW() - INTERVAL '7 days'
            AND ticker IN ('BTC-USD', 'ETH-USD', 'BNB-USD')
            ORDER BY ticker, timestamp DESC
            """
            
            df = pd.read_sql(query, self.engine)
            
            if df.empty:
                return {"sentiment": "NEUTRAL", "confidence": 0}
            
            # Calcular cambios de precio de 7 días
            price_changes = []
            for ticker in df['ticker'].unique():
                ticker_data = df[df['ticker'] == ticker].sort_values('timestamp')
                if len(ticker_data) >= 2:
                    latest_price = ticker_data.iloc[-1]['close']
                    week_ago_price = ticker_data.iloc[0]['close']
                    change = (latest_price - week_ago_price) / week_ago_price
                    price_changes.append(change)
            
            if not price_changes:
                return {"sentiment": "NEUTRAL", "confidence": 0}
            
            avg_change = np.mean(price_changes)
            confidence = min(abs(avg_change) * 1000, 100)  # Escalar confianza
            
            if avg_change > 0.05:
                sentiment = "BULLISH"
            elif avg_change < -0.05:
                sentiment = "BEARISH"
            else:
                sentiment = "NEUTRAL"
            
            return {
                "sentiment": sentiment,
                "confidence": round(confidence, 1),
                "avg_change_7d": round(avg_change * 100, 2)
            }
            
        except Exception as e:
            return {"sentiment": "UNKNOWN", "confidence": 0, "error": str(e)}
    
    def generate_daily_report(self) -> Dict:
        """Genera un reporte diario completo"""
        try:
            # Obtener datos del día
            today = datetime.now().date()
            
            if not self.engine:
                return {"error": "No database connection"}
            
            # Query para trades del día
            trades_query = """
            SELECT * FROM trade_log 
            WHERE DATE(timestamp) = %s
            ORDER BY timestamp DESC
            """
            
            trades_df = pd.read_sql(trades_query, self.engine, params=[today])
            
            # Métricas del día
            daily_trades = len(trades_df)
            daily_volume = trades_df['size'].sum() if not trades_df.empty else 0
            
            # Señales generadas
            signals_path = os.path.join(project_root, 'signals.json')
            signals_count = 0
            if os.path.exists(signals_path):
                with open(signals_path, 'r') as f:
                    signals_data = json.load(f)
                    signals_count = len(signals_data)
            
            # Estado del sistema
            system_health = "HEALTHY"  # Simplificado por ahora
            
            return {
                "date": today.isoformat(),
                "summary": {
                    "trades_executed": daily_trades,
                    "total_volume": round(daily_volume, 2),
                    "signals_generated": signals_count,
                    "system_health": system_health
                },
                "performance": {
                    "daily_return": round(np.random.uniform(-2, 3), 2),  # Placeholder
                    "portfolio_value": 10000,  # Placeholder
                    "active_positions": 0  # Placeholder
                },
                "alerts": [],
                "next_execution": "07:00 tomorrow"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def generate_weekly_report(self) -> Dict:
        """Genera un reporte semanal detallado"""
        try:
            week_start = datetime.now() - timedelta(days=7)
            
            if not self.engine:
                return {"error": "No database connection"}
            
            # Query para trades de la semana
            trades_query = """
            SELECT * FROM trade_log 
            WHERE timestamp >= %s
            ORDER BY timestamp DESC
            """
            
            trades_df = pd.read_sql(trades_query, self.engine, params=[week_start])
            
            # Calcular métricas semanales
            weekly_trades = len(trades_df)
            weekly_volume = trades_df['size'].sum() if not trades_df.empty else 0
            
            # Análisis por ticker
            ticker_analysis = {}
            if not trades_df.empty:
                ticker_stats = trades_df.groupby('ticker').agg({
                    'size': 'sum',
                    'timestamp': 'count'
                }).rename(columns={'timestamp': 'trades_count'})
                
                for ticker, stats in ticker_stats.iterrows():
                    ticker_analysis[ticker] = {
                        "total_volume": round(stats['size'], 2),
                        "trade_count": int(stats['trades_count'])
                    }
            
            # Performance simulada
            weekly_performance = {
                "total_return": round(np.random.uniform(-5, 8), 2),
                "volatility": round(np.random.uniform(15, 25), 2),
                "max_drawdown": round(np.random.uniform(-8, -1), 2),
                "sharpe_ratio": round(np.random.uniform(0.8, 2.0), 2)
            }
            
            return {
                "period": f"{week_start.date()} to {datetime.now().date()}",
                "summary": {
                    "total_trades": weekly_trades,
                    "total_volume": round(weekly_volume, 2),
                    "unique_assets_traded": len(ticker_analysis),
                    "avg_trades_per_day": round(weekly_trades / 7, 1)
                },
                "performance": weekly_performance,
                "by_asset": ticker_analysis,
                "recommendations": [
                    "Continuar con la estrategia actual",
                    "Monitorear volatilidad del mercado",
                    "Considerar ajustar parámetros de riesgo"
                ]
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_asset_performance_ranking(self, days: int = 30) -> List[Dict]:
        """Obtiene ranking de performance por activo"""
        try:
            if not self.engine:
                return []
            
            # Query para obtener precios de inicio y fin del período
            query = """
            WITH asset_prices AS (
                SELECT 
                    ticker,
                    timestamp,
                    close,
                    ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY timestamp ASC) as rn_first,
                    ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY timestamp DESC) as rn_last
                FROM asset_metrics 
                WHERE timestamp >= NOW() - INTERVAL '%s days'
            ),
            first_last_prices AS (
                SELECT 
                    ticker,
                    MAX(CASE WHEN rn_first = 1 THEN close END) as first_price,
                    MAX(CASE WHEN rn_last = 1 THEN close END) as last_price
                FROM asset_prices
                GROUP BY ticker
                HAVING MAX(CASE WHEN rn_first = 1 THEN close END) IS NOT NULL 
                   AND MAX(CASE WHEN rn_last = 1 THEN close END) IS NOT NULL
            )
            SELECT 
                ticker,
                first_price,
                last_price,
                ((last_price - first_price) / first_price * 100) as return_pct
            FROM first_last_prices
            ORDER BY return_pct DESC
            LIMIT 20
            """
            
            df = pd.read_sql(query, self.engine, params=[days])
            
            return [
                {
                    "ticker": row['ticker'],
                    "return_percentage": round(row['return_pct'], 2),
                    "first_price": round(row['first_price'], 4),
                    "last_price": round(row['last_price'], 4)
                }
                for _, row in df.iterrows()
            ]
            
        except Exception as e:
            return []
    
    def calculate_correlation_matrix(self, assets: List[str] = None) -> Dict:
        """Calcula matriz de correlación entre activos"""
        try:
            if not self.engine:
                return {}
            
            if not assets:
                assets = ['BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'ADA-USD']
            
            # Query para obtener precios diarios
            assets_str = "', '".join(assets)
            query = f"""
            SELECT 
                DATE(timestamp) as date,
                ticker,
                AVG(close) as avg_close
            FROM asset_metrics 
            WHERE ticker IN ('{assets_str}')
            AND timestamp >= NOW() - INTERVAL '30 days'
            GROUP BY DATE(timestamp), ticker
            ORDER BY date, ticker
            """
            
            df = pd.read_sql(query, self.engine)
            
            if df.empty:
                return {}
            
            # Pivot para tener activos como columnas
            pivot_df = df.pivot(index='date', columns='ticker', values='avg_close')
            
            # Calcular retornos diarios
            returns_df = pivot_df.pct_change().dropna()
            
            # Calcular matriz de correlación
            corr_matrix = returns_df.corr()
            
            # Convertir a formato JSON serializable
            correlation_data = {}
            for asset1 in corr_matrix.index:
                correlation_data[asset1] = {}
                for asset2 in corr_matrix.columns:
                    correlation_data[asset1][asset2] = round(corr_matrix.loc[asset1, asset2], 3)
            
            return correlation_data
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_volatility_analysis(self, days: int = 30) -> Dict:
        """Análisis de volatilidad del portfolio"""
        try:
            if not self.engine:
                return {}
            
            # Query para obtener precios diarios principales
            query = """
            SELECT 
                DATE(timestamp) as date,
                ticker,
                AVG(close) as avg_close
            FROM asset_metrics 
            WHERE ticker IN ('BTC-USD', 'ETH-USD', 'BNB-USD')
            AND timestamp >= NOW() - INTERVAL '%s days'
            GROUP BY DATE(timestamp), ticker
            ORDER BY date, ticker
            """
            
            df = pd.read_sql(query, self.engine, params=[days])
            
            if df.empty:
                return {"error": "No data available"}
            
            # Calcular volatilidad por activo
            volatility_data = {}
            
            for ticker in df['ticker'].unique():
                ticker_data = df[df['ticker'] == ticker].sort_values('date')
                if len(ticker_data) > 1:
                    prices = ticker_data['avg_close'].values
                    returns = np.diff(np.log(prices))
                    volatility = np.std(returns) * np.sqrt(252) * 100  # Anualizada
                    
                    volatility_data[ticker] = {
                        "daily_volatility": round(np.std(returns) * 100, 2),
                        "annualized_volatility": round(volatility, 2),
                        "current_price": round(prices[-1], 4)
                    }
            
            # Volatilidad promedio del portfolio
            avg_volatility = np.mean([v["annualized_volatility"] for v in volatility_data.values()])
            
            return {
                "portfolio_volatility": round(avg_volatility, 2),
                "by_asset": volatility_data,
                "risk_level": "HIGH" if avg_volatility > 50 else "MEDIUM" if avg_volatility > 30 else "LOW",
                "period_days": days
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_trading_efficiency_metrics(self) -> Dict:
        """Métricas de eficiencia de trading"""
        try:
            if not self.engine:
                return {}
            
            # Query para analizar trades recientes
            query = """
            SELECT 
                ticker,
                action,
                price,
                size,
                timestamp,
                (price * size) as trade_value
            FROM trade_log 
            WHERE timestamp >= NOW() - INTERVAL '30 days'
            ORDER BY timestamp
            """
            
            df = pd.read_sql(query, self.engine)
            
            if df.empty:
                return {"no_trades": True}
            
            # Calcular métricas de eficiencia
            total_trades = len(df)
            total_volume = df['trade_value'].sum()
            avg_trade_size = df['trade_value'].mean()
            
            # Análisis por par BUY/SELL
            buy_trades = df[df['action'] == 'BUY']
            sell_trades = df[df['action'] == 'SELL']
            
            efficiency_metrics = {
                "total_trades": total_trades,
                "total_volume": round(total_volume, 2),
                "average_trade_size": round(avg_trade_size, 2),
                "buy_sell_ratio": round(len(buy_trades) / len(sell_trades), 2) if len(sell_trades) > 0 else 0,
                "trades_per_day": round(total_trades / 30, 1),
                "volume_per_day": round(total_volume / 30, 2)
            }
            
            return efficiency_metrics
            
        except Exception as e:
            return {"error": str(e)}