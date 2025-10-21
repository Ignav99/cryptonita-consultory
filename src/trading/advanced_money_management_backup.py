# src/trading/money_management.py
import sys
import os
from typing import Dict, List, Tuple
import numpy as np

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.web.api.binance_service import binance_service

class ProfessionalMoneyManager:
    """Sistema profesional de gestión de dinero para Cryptonita"""
    
    def __init__(self):
        self.min_trade_percentage = 0.01  # 1% mínimo
        self.max_trade_percentage = 0.15  # 15% máximo por trade
        self.max_total_exposure = 0.80    # 80% máximo del portfolio invertido
        self.reserve_cash = 0.20          # 20% siempre en cash
        
    def calculate_position_size(self, 
                              confidence_score: float, 
                              market_sentiment: str,
                              portfolio_value: float,
                              current_exposure: float = 0.0) -> Dict:
        """
        Calcula el tamaño de posición basado en:
        - Confianza del modelo (0-1)
        - Sentiment del mercado
        - Valor total del portfolio
        - Exposición actual
        """
        
        # BASE: Tamaño según confianza (1-15%)
        confidence_factor = max(0.1, min(1.0, confidence_score))
        base_percentage = self.min_trade_percentage + (confidence_factor * 0.14)
        
        # AJUSTE POR SENTIMENT DEL MERCADO
        sentiment_multiplier = self._get_sentiment_multiplier(market_sentiment)
        adjusted_percentage = base_percentage * sentiment_multiplier
        
        # AJUSTE POR EXPOSICIÓN ACTUAL
        exposure_factor = self._calculate_exposure_factor(current_exposure)
        final_percentage = adjusted_percentage * exposure_factor
        
        # LÍMITES DE SEGURIDAD
        final_percentage = max(self.min_trade_percentage, 
                             min(self.max_trade_percentage, final_percentage))
        
        # VERIFICAR QUE NO EXCEDAMOS EXPOSICIÓN MÁXIMA
        if current_exposure + final_percentage > self.max_total_exposure:
            final_percentage = max(0, self.max_total_exposure - current_exposure)
        
        # CALCULAR VALORES ABSOLUTOS
        trade_amount = portfolio_value * final_percentage
        
        return {
            "percentage": round(final_percentage * 100, 2),
            "amount_usdc": round(trade_amount, 2),
            "confidence_score": confidence_score,
            "market_sentiment": market_sentiment,
            "exposure_factor": round(exposure_factor, 3),
            "sentiment_multiplier": round(sentiment_multiplier, 3),
            "current_exposure": round(current_exposure * 100, 2),
            "recommendation": self._get_recommendation(final_percentage, confidence_score)
        }
    
    def _get_sentiment_multiplier(self, sentiment: str) -> float:
        """Ajusta el tamaño según sentiment del mercado"""
        multipliers = {
            "BULLISH": 1.3,      # Aumentar posiciones en mercado alcista
            "NEUTRAL": 1.0,      # Tamaño normal
            "BEARISH": 0.7,      # Reducir posiciones en mercado bajista
            "UNKNOWN": 0.8       # Conservador si no sabemos
        }
        return multipliers.get(sentiment, 0.8)
    
    def _calculate_exposure_factor(self, current_exposure: float) -> float:
        """Reduce el tamaño si ya tenemos mucha exposición"""
        if current_exposure < 0.3:      # Menos del 30% invertido
            return 1.0
        elif current_exposure < 0.5:    # 30-50% invertido
            return 0.8
        elif current_exposure < 0.7:    # 50-70% invertido
            return 0.6
        else:                           # Más del 70% invertido
            return 0.3
    
    def _get_recommendation(self, percentage: float, confidence: float) -> str:
        """Genera recomendación textual"""
        if percentage < 0.02:
            return "POSICIÓN MÍNIMA - Baja confianza o alta exposición"
        elif percentage < 0.05:
            return "POSICIÓN PEQUEÑA - Confianza moderada"
        elif percentage < 0.10:
            return "POSICIÓN ESTÁNDAR - Buena confianza"
        else:
            return "POSICIÓN GRANDE - Alta confianza y buenas condiciones"
    
    def get_portfolio_status(self) -> Dict:
        """Obtiene estado actual del portfolio"""
        try:
            balance_data = binance_service.get_real_balance()
            
            if balance_data["status"] == "success":
                total_value = sum(balance_data["total_balances"].values())
                usdc_free = balance_data["total_balances"].get("USDC", 0)
                
                # TODO: Calcular posiciones abiertas cuando implementemos el tracking
                open_positions_value = 0  # Placeholder
                current_exposure = open_positions_value / total_value if total_value > 0 else 0
                
                return {
                    "total_portfolio_value": total_value,
                    "cash_available": usdc_free,
                    "open_positions_value": open_positions_value,
                    "current_exposure": current_exposure,
                    "cash_percentage": usdc_free / total_value * 100 if total_value > 0 else 0,
                    "max_new_position": total_value * self.max_trade_percentage,
                    "status": "healthy"
                }
            else:
                return {"status": "error", "error": balance_data.get("error")}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def evaluate_trade_opportunity(self, 
                                 ticker: str, 
                                 signal: str, 
                                 confidence: float,
                                 market_sentiment: str = "NEUTRAL") -> Dict:
        """Evalúa una oportunidad de trading completa"""
        
        portfolio_status = self.get_portfolio_status()
        if portfolio_status["status"] != "healthy":
            return {"recommendation": "NO_TRADE", "reason": "Portfolio status error"}
        
        # Solo operar si tenemos suficiente cash
        if portfolio_status["cash_available"] < 50:  # Mínimo $50 USDC
            return {"recommendation": "NO_TRADE", "reason": "Insufficient cash"}
        
        # Calcular tamaño de posición
        position_calc = self.calculate_position_size(
            confidence_score=confidence,
            market_sentiment=market_sentiment,
            portfolio_value=portfolio_status["total_portfolio_value"],
            current_exposure=portfolio_status["current_exposure"]
        )
        
        # Verificar que podemos ejecutar el trade
        if position_calc["amount_usdc"] > portfolio_status["cash_available"]:
            position_calc["amount_usdc"] = portfolio_status["cash_available"] * 0.95  # 95% del disponible
            position_calc["percentage"] = (position_calc["amount_usdc"] / portfolio_status["total_portfolio_value"]) * 100
        
        return {
            "ticker": ticker,
            "signal": signal,
            "recommendation": "EXECUTE_TRADE" if position_calc["amount_usdc"] >= 10 else "NO_TRADE",
            "position_size": position_calc,
            "portfolio_status": portfolio_status,
            "reasoning": f"Confianza {confidence:.1%}, Sentiment {market_sentiment}, Exposición {portfolio_status['current_exposure']:.1%}"
        }

# Instancia global
money_manager = ProfessionalMoneyManager()
# Instancia global
advanced_money_manager = AdvancedMoneyManager()
