# src/trading/advanced_money_management.py
import sys
import os
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import math

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.web.api.binance_service import binance_service

class AdvancedMoneyManager:
    """
    Sistema avanzado de gestión de dinero basado en:
    1. Kelly Criterion optimizado
    2. Volatilidad adaptativa
    3. Correlación entre activos
    4. Drawdown dinámico
    5. Risk Parity
    """
    
    def __init__(self):
        # Parámetros base
        self.base_kelly_fraction = 0.25  # Usar solo 25% del Kelly completo (más conservador)
        self.max_position_size = 0.20    # 20% máximo por posición
        self.max_total_exposure = 0.85   # 85% máximo total
        self.min_position_size = 0.005   # 0.5% mínimo
        
        # Parámetros de volatilidad
        self.target_portfolio_vol = 0.15  # 15% volatilidad objetivo anual
        self.lookback_days = 30          # Días para calcular volatilidad
        
        # Parámetros de drawdown
        self.max_drawdown_threshold = 0.10  # Si drawdown > 10%, reducir posiciones
        self.drawdown_reduction_factor = 0.5  # Reducir posiciones a la mitad
        
    def calculate_kelly_position_size(self, 
                                    win_rate: float, 
                                    avg_win: float, 
                                    avg_loss: float,
                                    confidence_adjustment: float = 1.0) -> float:
        """
        Calcula el tamaño de posición usando Kelly Criterion optimizado
        
        Kelly = (bp - q) / b
        donde:
        b = ratio de ganancia (avg_win / avg_loss)
        p = probabilidad de ganar (win_rate)
        q = probabilidad de perder (1 - win_rate)
        """
        if avg_loss <= 0 or win_rate <= 0 or win_rate >= 1:
            return self.min_position_size
        
        b_ratio = avg_win / abs(avg_loss)
        p = win_rate
        q = 1 - win_rate
        
        kelly_fraction = (b_ratio * p - q) / b_ratio
        
        # Aplicar factor de seguridad y ajuste de confianza
        safe_kelly = kelly_fraction * self.base_kelly_fraction * confidence_adjustment
        
        return max(self.min_position_size, min(self.max_position_size, safe_kelly))
    
    def calculate_volatility_adjusted_size(self, 
                                         asset_volatility: float, 
                                         portfolio_value: float) -> float:
        """
        Ajusta el tamaño de posición basado en la volatilidad del activo
        Activos más volátiles = posiciones más pequeñas
        """
        if asset_volatility <= 0:
            return self.min_position_size
        
        # Calcular factor de ajuste por volatilidad
        vol_adjustment = self.target_portfolio_vol / asset_volatility
        
        # Limitar el ajuste entre 0.3 y 2.0
        vol_adjustment = max(0.3, min(2.0, vol_adjustment))
        
        base_size = 0.05  # 5% base
        adjusted_size = base_size * vol_adjustment
        
        return max(self.min_position_size, min(self.max_position_size, adjusted_size))
    
    def calculate_correlation_adjustment(self, 
                                       new_asset: str, 
                                       current_positions: List[str]) -> float:
        """
        Ajusta el tamaño si el nuevo activo está correlacionado con posiciones existentes
        """
        if not current_positions:
            return 1.0
        
        # Simplificado: agrupar activos por categorías correlacionadas
        crypto_majors = ['BTC-USD', 'ETH-USD']
        altcoins = ['ADA-USD', 'SOL-USD', 'AVAX-USD', 'DOT-USD']
        defi_tokens = ['UNI-USD', 'AAVE-USD', 'LINK-USD']
        
        def get_category(asset):
            if asset in crypto_majors:
                return 'majors'
            elif asset in altcoins:
                return 'altcoins'
            elif asset in defi_tokens:
                return 'defi'
            else:
                return 'other'
        
        new_asset_category = get_category(new_asset)
        
        # Contar activos en la misma categoría
        same_category_count = sum(1 for pos in current_positions 
                                if get_category(pos) == new_asset_category)
        
        # Reducir tamaño si ya tenemos muchos activos correlacionados
        if same_category_count == 0:
            return 1.0
        elif same_category_count == 1:
            return 0.8
        elif same_category_count == 2:
            return 0.6
        else:
            return 0.4
    
    def calculate_drawdown_adjustment(self, portfolio_value: float) -> float:
        """
        Ajusta el tamaño basado en el drawdown actual del portfolio
        """
        # TODO: Implementar tracking del equity peak
        # Por ahora simulamos
        current_drawdown = 0.02  # 2% drawdown ejemplo
        
        if current_drawdown > self.max_drawdown_threshold:
            return self.drawdown_reduction_factor
        else:
            return 1.0
    
    def calculate_time_based_adjustment(self) -> float:
        """
        Ajusta según condiciones temporales (volatilidad de mercado, eventos macro)
        """
        hour = datetime.now().hour
        
        # Reducir posiciones durante horas de baja liquidez
        if 2 <= hour <= 6:  # Madrugada
            return 0.7
        elif 14 <= hour <= 16:  # Apertura de mercados tradicionales (alta volatilidad)
            return 1.2
        else:
            return 1.0
    
    def evaluate_professional_trade(self, 
                                  ticker: str, 
                                  signal: str,
                                  model_confidence: float,
                                  market_conditions: Dict) -> Dict:
        """
        Evaluación profesional completa de una oportunidad de trading
        """
        
        # 1. Obtener estado del portfolio
        portfolio_status = self.get_portfolio_status()
        if portfolio_status["status"] != "healthy":
            return self._create_no_trade_response("Portfolio unhealthy")
        
        # 2. Parámetros históricos del modelo (simulados por ahora)
        # TODO: Obtener de base de datos histórica
        historical_performance = {
            "win_rate": 0.65,        # 65% win rate
            "avg_win": 0.08,         # 8% ganancia promedio
            "avg_loss": 0.04,        # 4% pérdida promedio
            "asset_volatility": 0.25  # 25% volatilidad anual
        }
        
        # 3. Calcular tamaño usando múltiples métodos
        kelly_size = self.calculate_kelly_position_size(
            win_rate=historical_performance["win_rate"],
            avg_win=historical_performance["avg_win"],
            avg_loss=historical_performance["avg_loss"],
            confidence_adjustment=model_confidence
        )
        
        vol_adjusted_size = self.calculate_volatility_adjusted_size(
            asset_volatility=historical_performance["asset_volatility"],
            portfolio_value=portfolio_status["total_portfolio_value"]
        )
        
        # 4. Aplicar ajustes
        correlation_adj = self.calculate_correlation_adjustment(ticker, [])  # TODO: posiciones actuales
        drawdown_adj = self.calculate_drawdown_adjustment(portfolio_status["total_portfolio_value"])
        time_adj = self.calculate_time_based_adjustment()
        
        # 5. Combinar todos los factores
        base_size = min(kelly_size, vol_adjusted_size)  # Tomar el más conservador
        final_size = base_size * correlation_adj * drawdown_adj * time_adj
        
        # 6. Aplicar límites finales
        final_size = max(self.min_position_size, 
                        min(self.max_position_size, final_size))
        
        # 7. Verificar exposición total
        current_exposure = portfolio_status.get("current_exposure", 0)
        if current_exposure + final_size > self.max_total_exposure:
            final_size = max(0, self.max_total_exposure - current_exposure)
        
        # 8. Calcular valores absolutos
        trade_amount = portfolio_status["total_portfolio_value"] * final_size
        
        # 9. Verificar que tenemos suficiente cash
        if trade_amount > portfolio_status["cash_available"] * 0.95:
            trade_amount = portfolio_status["cash_available"] * 0.95
            final_size = trade_amount / portfolio_status["total_portfolio_value"]
        
        return {
            "ticker": ticker,
            "signal": signal,
            "recommendation": "EXECUTE" if trade_amount >= 10 else "SKIP",
            "position_size": {
                "percentage": round(final_size * 100, 2),
                "amount_usdc": round(trade_amount, 2),
                "kelly_component": round(kelly_size * 100, 2),
                "volatility_component": round(vol_adjusted_size * 100, 2),
                "correlation_adjustment": round(correlation_adj, 3),
                "drawdown_adjustment": round(drawdown_adj, 3),
                "time_adjustment": round(time_adj, 3)
            },
            "risk_metrics": {
                "expected_return": historical_performance["avg_win"] * historical_performance["win_rate"] - 
                                 historical_performance["avg_loss"] * (1 - historical_performance["win_rate"]),
                "win_rate": historical_performance["win_rate"],
                "risk_reward_ratio": historical_performance["avg_win"] / historical_performance["avg_loss"],
                "confidence": model_confidence
            },
            "reasoning": self._generate_reasoning(final_size, model_confidence, correlation_adj, drawdown_adj)
        }
    
    def _generate_reasoning(self, size: float, confidence: float, corr_adj: float, dd_adj: float) -> str:
        """Genera explicación del tamaño de posición"""
        reasons = []
        
        if size >= 0.15:
            reasons.append("POSICIÓN GRANDE: Alta confianza y buenas condiciones")
        elif size >= 0.08:
            reasons.append("POSICIÓN ESTÁNDAR: Condiciones favorables")
        elif size >= 0.03:
            reasons.append("POSICIÓN PEQUEÑA: Confianza moderada")
        else:
            reasons.append("POSICIÓN MÍNIMA: Baja confianza o restricciones")
        
        if corr_adj < 0.8:
            reasons.append("Reducido por correlación con posiciones existentes")
        
        if dd_adj < 1.0:
            reasons.append("Reducido por drawdown del portfolio")
        
        return " | ".join(reasons)
    
    def _create_no_trade_response(self, reason: str) -> Dict:
        """Respuesta estándar para no operar"""
        return {
            "recommendation": "NO_TRADE",
            "reason": reason,
            "position_size": {"percentage": 0, "amount_usdc": 0}
        }
    
    def get_portfolio_status(self) -> Dict:
        """Obtiene estado actual del portfolio"""
        try:
            balance_data = binance_service.get_real_balance()
            
            if balance_data["status"] == "success":
                total_value = sum(balance_data["total_balances"].values())
                usdc_free = balance_data["total_balances"].get("USDC", 0)
                
                # TODO: Implementar tracking de posiciones abiertas
                open_positions_value = 0
                current_exposure = open_positions_value / total_value if total_value > 0 else 0
                
                return {
                    "total_portfolio_value": total_value,
                    "cash_available": usdc_free,
                    "open_positions_value": open_positions_value,
                    "current_exposure": current_exposure,
                    "status": "healthy"
                }
            else:
                return {"status": "error", "error": balance_data.get("error")}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}

# Instancia global
advanced_money_manager = AdvancedMoneyManager()