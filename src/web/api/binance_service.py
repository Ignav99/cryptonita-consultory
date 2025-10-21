# src/web/api/binance_service.py
import ccxt
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import settings

class BinanceService:
    def __init__(self):
        self.exchange = ccxt.binance({
            'apiKey': settings.EXCHANGE_API_KEY,
            'secret': settings.EXCHANGE_API_SECRET,
            'sandbox': False,
            'enableRateLimit': True,
        })
    
    def get_real_balance(self):
        """Obtiene el balance real de Binance - VERSIÓN SIMPLE QUE FUNCIONA"""
        try:
            # Usar exactamente el mismo método que funcionó antes
            balance = self.exchange.fetch_balance()
            
            # Extraer datos como en el test que funcionó
            total_balances = {}
            usdt_free = 0
            
            # Mostrar balances principales (como en el test exitoso)
            for currency, amount in balance['total'].items():
                if amount > 0:
                    total_balances[currency] = amount
            
            # Obtener USDT libre específicamente
            if 'USDT' in balance:
                usdt_free = balance['USDT']['free']
            
            return {
                "status": "success",
                "total_balances": total_balances,
                "usdt_free": float(usdt_free),
                "total_currencies": len(total_balances)
            }
            
        except Exception as e:
            return {
                "status": "error", 
                "error": str(e)
            }

# Instancia global
binance_service = BinanceService()