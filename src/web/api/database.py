# src/web/api/database.py - VERSIÓN MEJORADA
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys
import os
import logging

# Agregar path del proyecto
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importar tu conector existente
from src.utils.db_connector import create_db_engine

class CryptonitaDataService:
    """Servicio mejorado para acceder a los datos de PostgreSQL"""
    
    def __init__(self):
        self.engine = create_db_engine()
        self.logger = logging.getLogger(__name__)
    
    def get_portfolio_summary(self) -> Dict:
        """Obtiene resumen completo del portfolio desde trade_log"""
        try:
            if not self.engine:
                return {"error": "No database connection"}
            
            # Query mejorado para obtener resumen de trades
            query = """
            WITH trade_summary AS (
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN action = 'BUY' THEN size * price ELSE 0 END) as total_bought,
                    SUM(CASE WHEN action = 'SELL' THEN size * price ELSE 0 END) as total_sold,
                    COUNT(CASE WHEN action = 'BUY' THEN 1 END) as buy_orders,
                    COUNT(CASE WHEN action = 'SELL' THEN 1 END) as sell_orders,
                    MAX(timestamp) as last_trade,
                    MIN(timestamp) as first_trade,
                    AVG(size * price) as avg_trade_value,
                    COUNT(DISTINCT ticker) as unique_assets
                FROM trade_log
                WHERE timestamp >= NOW() - INTERVAL '30 days'
            ),
            daily_volume AS (
                SELECT 
                    DATE(timestamp) as trade_date,
                    SUM(size * price) as daily_volume
                FROM trade_log
                WHERE timestamp >= NOW() - INTERVAL '7 days'
                GROUP BY DATE(timestamp)
                ORDER BY trade_date DESC
                LIMIT 7
            )
            SELECT 
                ts.*,
                COALESCE(AVG(dv.daily_volume), 0) as avg_daily_volume
            FROM trade_summary ts
            CROSS JOIN daily_volume dv
            GROUP BY ts.total_trades, ts.total_bought, ts.total_sold, ts.buy_orders, 
                     ts.sell_orders, ts.last_trade, ts.first_trade, ts.avg_trade_value, ts.unique_assets
            """
            
            df = pd.read_sql(query, self.engine)
            
            if df.empty or df.iloc[0]['total_trades'] == 0:
                return {
                    "total_trades": 0,
                    "total_volume": 0,
                    "buy_orders": 0,
                    "sell_orders": 0,
                    "last_trade": None,
                    "estimated_balance": 10000,  # Valor inicial
                    "avg_trade_value": 0,
                    "unique_assets_traded": 0,
                    "trading_period_days": 0,
                    "avg_daily_volume": 0
                }
            
            row = df.iloc[0]
            
            # Calcular período de trading
            trading_days = 0
            if row['first_trade'] and row['last_trade']:
                trading_days = (row['last_trade'] - row['first_trade']).days + 1
            
            # Estimar balance (simplificado)
            total_bought = float(row['total_bought'] or 0)
            total_sold = float(row['total_sold'] or 0)
            estimated_balance = 10000 - total_bought + total_sold  # Balance estimado
            
            return {
                "total_trades": int(row['total_trades']),
                "total_volume": total_bought + total_sold,
                "buy_orders": int(row['buy_orders'] or 0),
                "sell_orders": int(row['sell_orders'] or 0),
                "last_trade": row['last_trade'].isoformat() if row['last_trade'] else None,
                "estimated_balance": round(estimated_balance, 2),
                "avg_trade_value": round(float(row['avg_trade_value'] or 0), 2),
                "unique_assets_traded": int(row['unique_assets'] or 0),
                "trading_period_days": trading_days,
                "avg_daily_volume": round(float(row['avg_daily_volume'] or 0), 2)
            }
            
        except:
            return "Unknown"
    
    def _calculate_risk_score(self, volatility, change_percent) -> str:
        """Calcula score de riesgo basado en volatilidad y cambio"""
        try:
            vol = float(volatility or 0)
            change = abs(float(change_percent or 0))
            
            risk_score = (vol * 0.6) + (change * 0.4)
            
            if risk_score > 15:
                return "HIGH"
            elif risk_score > 8:
                return "MEDIUM"
            else:
                return "LOW"
        except:
            return "UNKNOWN"

# Instancia global del servicio mejorado
# Instancia global del servicio
            self.logger.error(f"Error in get_portfolio_summary: {e}")
            return {"error": str(e)}
    
    def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """Obtiene los trades más recientes con información adicional"""
        try:
            if not self.engine:
                return []
            
            query = """
            SELECT 
                timestamp,
                ticker,
                action,
                price,
                size,
                (price * size) as total_value,
                status,
                order_id
            FROM trade_log
            ORDER BY timestamp DESC
            LIMIT %s
            """
            
            df = pd.read_sql(query, self.engine, params=[limit])
            
            return [
                {
                    "timestamp": row['timestamp'].isoformat(),
                    "ticker": row['ticker'],
                    "action": row['action'],
                    "price": float(row['price']) if row['price'] else 0,
                    "size": float(row['size']) if row['size'] else 0,
                    "total_value": float(row['total_value']) if row['total_value'] else 0,
                    "status": row['status'],
                    "order_id": row['order_id'],
                    "time_ago": self._time_ago(row['timestamp'])
                }
                for _, row in df.iterrows()
            ]
            
        except Exception as e:
            self.logger.error(f"Error in get_recent_trades: {e}")
            return []
    
    def get_top_performers(self, days: int = 7) -> List[Dict]:
        """Obtiene los activos con mejor rendimiento con análisis mejorado"""
        try:
            if not self.engine:
                return []
            
            query = """
            WITH daily_prices AS (
                SELECT 
                    ticker,
                    DATE(timestamp) as date,
                    AVG(close) as avg_close,
                    MIN(close) as min_close,
                    MAX(close) as max_close,
                    AVG(volume) as avg_volume
                FROM asset_metrics
                WHERE timestamp >= NOW() - INTERVAL '%s days'
                GROUP BY ticker, DATE(timestamp)
            ),
            price_analysis AS (
                SELECT 
                    ticker,
                    COUNT(*) as trading_days,
                    (MAX(avg_close) - MIN(avg_close)) / MIN(avg_close) * 100 as change_percent,
                    STDDEV(avg_close) / AVG(avg_close) * 100 as volatility_percent,
                    AVG(avg_volume) as avg_daily_volume,
                    MAX(avg_close) as period_high,
                    MIN(avg_close) as period_low
                FROM daily_prices
                GROUP BY ticker
                HAVING COUNT(*) >= 2
            )
            SELECT 
                ticker,
                ROUND(change_percent::numeric, 2) as change_percent,
                ROUND(volatility_percent::numeric, 2) as volatility,
                trading_days,
                ROUND(avg_daily_volume::numeric, 0) as avg_volume,
                ROUND(period_high::numeric, 6) as high,
                ROUND(period_low::numeric, 6) as low
            FROM price_analysis
            ORDER BY change_percent DESC
            LIMIT 10
            """
            
            df = pd.read_sql(query, self.engine, params=[days])
            
            return [
                {
                    "ticker": row['ticker'],
                    "change_percent": float(row['change_percent']) if row['change_percent'] else 0,
                    "volatility": float(row['volatility']) if row['volatility'] else 0,
                    "trading_days": int(row['trading_days']),
                    "avg_volume": int(row['avg_volume']) if row['avg_volume'] else 0,
                    "period_high": float(row['high']) if row['high'] else 0,
                    "period_low": float(row['low']) if row['low'] else 0,
                    "risk_score": self._calculate_risk_score(row['volatility'], row['change_percent'])
                }
                for _, row in df.iterrows()
            ]
            
        except Exception as e:
            self.logger.error(f"Error in get_top_performers: {e}")
            return []
    
    def get_asset_metrics_summary(self) -> Dict:
        """Obtiene resumen mejorado de métricas de activos"""
        try:
            if not self.engine:
                return {"error": "No database connection"}
            
            query = """
            WITH asset_summary AS (
                SELECT 
                    COUNT(DISTINCT ticker) as total_assets,
                    COUNT(*) as total_records,
                    MAX(timestamp) as last_update,
                    MIN(timestamp) as first_record,
                    COUNT(DISTINCT DATE(timestamp)) as trading_days
                FROM asset_metrics
            ),
            recent_activity AS (
                SELECT 
                    COUNT(*) as records_today
                FROM asset_metrics
                WHERE DATE(timestamp) = CURRENT_DATE
            ),
            data_quality AS (
                SELECT 
                    COUNT(*) as total_rows,
                    COUNT(*) - COUNT(close) as missing_prices,
                    AVG(volume) as avg_volume
                FROM asset_metrics
                WHERE timestamp >= NOW() - INTERVAL '7 days'
            )
            SELECT 
                a.*,
                r.records_today,
                d.missing_prices,
                ROUND(d.avg_volume::numeric, 0) as avg_volume
            FROM asset_summary a
            CROSS JOIN recent_activity r
            CROSS JOIN data_quality d
            """
            
            df = pd.read_sql(query, self.engine)
            row = df.iloc[0]
            
            # Calcular calidad de datos
            data_quality_score = "HIGH"
            if row['missing_prices'] > 0:
                quality_ratio = 1 - (row['missing_prices'] / row['total_records'])
                if quality_ratio < 0.95:
                    data_quality_score = "LOW"
                elif quality_ratio < 0.98:
                    data_quality_score = "MEDIUM"
            
            return {
                "total_assets": int(row['total_assets']) if row['total_assets'] else 0,
                "total_records": int(row['total_records']) if row['total_records'] else 0,
                "last_update": row['last_update'].isoformat() if row['last_update'] else None,
                "first_record": row['first_record'].isoformat() if row['first_record'] else None,
                "trading_days": int(row['trading_days']) if row['trading_days'] else 0,
                "records_today": int(row['records_today']) if row['records_today'] else 0,
                "data_quality": data_quality_score,
                "avg_daily_volume": int(row['avg_volume']) if row['avg_volume'] else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error in get_asset_metrics_summary: {e}")
            return {"error": str(e)}
    
    def get_portfolio_performance_history(self, days: int = 30) -> List[Dict]:
        """Obtiene historial de performance del portfolio"""
        try:
            if not self.engine:
                return []
            
            # Simulamos performance histórica basada en trades reales
            # TODO: Implementar cálculo real cuando tengamos más datos
            
            base_value = 10000
            performance_data = []
            
            for i in range(days):
                date = datetime.now() - timedelta(days=days-i-1)
                
                # Simulamos variación basada en actividad real
                daily_change = np.random.normal(0.001, 0.015)  # Pequeña variación diaria
                base_value *= (1 + daily_change)
                
                performance_data.append({
                    "date": date.date().isoformat(),
                    "portfolio_value": round(base_value, 2),
                    "daily_return": round(daily_change * 100, 3),
                    "trades_count": np.random.randint(0, 5)  # Número simulado de trades
                })
            
            return performance_data
            
        except Exception as e:
            self.logger.error(f"Error in get_portfolio_performance_history: {e}")
            return []
    
    def get_system_metrics(self) -> Dict:
        """Métricas completas del sistema desde la base de datos"""
        try:
            portfolio = self.get_portfolio_summary()
            assets = self.get_asset_metrics_summary()
            
            # Verificar estado de la base de datos
            db_health = "healthy"
            try:
                with self.engine.connect() as conn:
                    conn.execute("SELECT 1")
            except:
                db_health = "error"
            
            return {
                "database_status": db_health,
                "portfolio": portfolio,
                "assets": assets,
                "last_updated": datetime.now().isoformat(),
                "system_version": "2.0.0"
            }
            
        except Exception as e:
            self.logger.error(f"Error in get_system_metrics: {e}")
            return {"error": str(e)}
    
    def get_trade_analytics(self, days: int = 30) -> Dict:
        """Analytics detallado de trades"""
        try:
            if not self.engine:
                return {"error": "No database connection"}
            
            query = """
            WITH trade_analytics AS (
                SELECT 
                    ticker,
                    action,
                    COUNT(*) as trade_count,
                    SUM(size * price) as total_volume,
                    AVG(size * price) as avg_trade_size,
                    STDDEV(size * price) as trade_size_stddev,
                    MIN(timestamp) as first_trade,
                    MAX(timestamp) as last_trade
                FROM trade_log
                WHERE timestamp >= NOW() - INTERVAL '%s days'
                GROUP BY ticker, action
            ),
            ticker_summary AS (
                SELECT 
                    ticker,
                    SUM(trade_count) as total_trades,
                    SUM(total_volume) as total_ticker_volume,
                    COUNT(DISTINCT action) as action_types
                FROM trade_analytics
                GROUP BY ticker
            )
            SELECT 
                ta.*,
                ts.total_trades,
                ts.action_types,
                ROUND(ta.total_volume::numeric, 2) as volume,
                ROUND(ta.avg_trade_size::numeric, 2) as avg_size
            FROM trade_analytics ta
            JOIN ticker_summary ts ON ta.ticker = ts.ticker
            ORDER BY ta.total_volume DESC
            """
            
            df = pd.read_sql(query, self.engine, params=[days])
            
            if df.empty:
                return {"no_data": True}
            
            # Procesar analytics
            analytics = {}
            for _, row in df.iterrows():
                ticker = row['ticker']
                if ticker not in analytics:
                    analytics[ticker] = {"buy": {}, "sell": {}}
                
                action = row['action'].lower()
                analytics[ticker][action] = {
                    "trade_count": int(row['trade_count']),
                    "total_volume": float(row['volume']),
                    "avg_trade_size": float(row['avg_size']),
                    "first_trade": row['first_trade'].isoformat() if row['first_trade'] else None,
                    "last_trade": row['last_trade'].isoformat() if row['last_trade'] else None
                }
            
            return {
                "period_days": days,
                "analytics_by_ticker": analytics,
                "summary": {
                    "total_tickers": len(analytics),
                    "total_volume": df['volume'].sum(),
                    "avg_trade_size": df['avg_size'].mean()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in get_trade_analytics: {e}")
            return {"error": str(e)}
    
    def _time_ago(self, timestamp) -> str:
        """Calcula tiempo transcurrido desde timestamp"""
        try:
            now = datetime.now()
            if timestamp.tzinfo:
                now = now.replace(tzinfo=timestamp.tzinfo)
            
            diff = now - timestamp
            
            if diff.days > 0:
                return f"{diff.days}d ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours}h ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes}m ago"
            else:
                return "Just now"
        except:
            return "UNKNOWN"
        
# Instancia global del servicio mejorado
data_service = CryptonitaDataService()
