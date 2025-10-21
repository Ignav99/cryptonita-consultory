# src/trading/long_only_trading_system.py

import pandas as pd
import numpy as np
import joblib
import os
import sys
import logging
import json
from datetime import datetime
from typing import Dict, List, Tuple

# --- Configuración ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.trading.advanced_money_management import advanced_money_manager

class LongOnlyTradingSystem:
    """
    Sistema de trading SOLO COMPRAS:
    - Compra cuando modelo dice BUY con alta confianza
    - Vende solo posiciones abiertas cuando modelo dice SELL
    - Recicla el dinero liberado en nuevas oportunidades
    """
    
    def __init__(self):
        # PARÁMETROS DE COMPRA
        self.buy_confidence_threshold = 0.75    # 75% mínimo para comprar
        self.min_position_size = 0.08           # 8% mínimo por posición  
        self.max_position_size = 0.15           # 15% máximo por posición
        self.max_total_invested = 0.85          # 85% máximo invertido
        
        # PARÁMETROS DE VENTA (protección)
        self.sell_confidence_threshold = 0.70   # 70% para vender posiciones abiertas
        self.stop_loss_threshold = -0.12        # Stop loss al -12%
        self.take_profit_threshold = 0.25       # Take profit al +25%
        
        # GESTIÓN DE PORTFOLIO
        self.min_cash_reserve = 0.15            # 15% siempre en cash
        self.rebalance_threshold = 0.20         # Rebalancear si posición crece >20%
        
        # SIMULACIÓN DE POSICIONES ABIERTAS (TODO: integrar con exchange real)
        self.open_positions = {}  # {"BTC-USD": {"amount": 100, "entry_price": 45000, "entry_date": "..."}}
    
    def execute_long_only_strategy(self):
        """Ejecuta la estrategia completa de solo compras"""
        logging.info("--- [INICIO] Sistema de Trading SOLO COMPRAS ---")
        
        # 1. Cargar modelo y datos
        model_data = self._load_model_and_data()
        if not model_data:
            return
        
        # 2. Generar predicciones
        predictions = self._generate_predictions(model_data)
        
        # 3. Obtener estado actual del portfolio
        portfolio_status = self._get_portfolio_status()
        
        # 4. Evaluar posiciones abiertas (vender si es necesario)
        sell_decisions = self._evaluate_open_positions(predictions, portfolio_status)
        
        # 5. Buscar nuevas oportunidades de compra
        buy_decisions = self._find_buy_opportunities(predictions, portfolio_status)
        
        # 6. Ejecutar las decisiones
        final_decisions = self._combine_decisions(buy_decisions, sell_decisions)
        
        # 7. Generar resumen y guardar
        self._save_and_report(final_decisions, portfolio_status)
        
        logging.info("--- [FIN] Sistema de Trading SOLO COMPRAS ---")
    
    def _load_model_and_data(self):
        """Carga modelo y datos"""
        try:
            model_path = os.path.join(project_root, 'models', 'ULTRA_MODEL_PACKAGE.joblib')
            model_package = joblib.load(model_path)
            
            data_path = os.path.join(project_root, 'notebooks', 'dataframes', 'model_input_features.parquet')
            features_df = pd.read_parquet(data_path)
            
            logging.info("✅ Modelo y datos cargados exitosamente")
            
            return {
                'primary_model': model_package['primary_model_pipeline'],
                'meta_model': model_package['meta_model'],
                'optimal_threshold': model_package['optimal_threshold'],
                'features_list': model_package['feature_list'],
                'features_df': features_df
            }
        except Exception as e:
            logging.error(f"❌ Error cargando modelo: {e}")
            return None
    
    def _generate_predictions(self, model_data):
        """Genera predicciones del modelo"""
        features_df = model_data['features_df']
        features_df['timestamp'] = pd.to_datetime(features_df['timestamp'])
        latest_features = features_df.sort_values('timestamp').groupby('ticker').last()
        
        # Preparar features
        original_features = [col.split('__')[1] for col in model_data['features_list']]
        X = latest_features[original_features]
        
        # Predicciones
        primary_proba = model_data['primary_model'].predict_proba(X)
        primary_preds = np.argmax(primary_proba, axis=1)
        
        meta_features = pd.DataFrame({'primary_model_prob': primary_proba.max(axis=1)}, index=X.index)
        meta_confidence = model_data['meta_model'].predict_proba(meta_features)[:, 1]
        
        # Estructura de predicciones
        predictions = {}
        for i, ticker in enumerate(X.index):
            predictions[ticker] = {
                'prediction': 'BUY' if primary_preds[i] == 1 else 'SELL',
                'confidence': meta_confidence[i],
                'buy_confidence': primary_proba[i][1],  # Probabilidad específica de BUY
                'sell_confidence': primary_proba[i][0]  # Probabilidad específica de SELL
            }
        
        logging.info(f"✅ Predicciones generadas para {len(predictions)} activos")
        return predictions
    
    def _get_portfolio_status(self):
        """Obtiene estado actual del portfolio"""
        portfolio_status = advanced_money_manager.get_portfolio_status()
        
        # TODO: Cargar posiciones reales desde exchange/base de datos
        # Por ahora simulamos algunas posiciones
        self.open_positions = {
            # "BTC-USD": {"amount_usdc": 100, "entry_price": 45000, "current_price": 46000, "entry_date": "2025-07-30"},
            # Vacío por ahora - se llenará con posiciones reales
        }
        
        # Calcular valor de posiciones abiertas
        open_positions_value = sum(pos.get("amount_usdc", 0) for pos in self.open_positions.values())
        cash_available = portfolio_status["cash_available"]
        total_portfolio = cash_available + open_positions_value
        
        portfolio_status.update({
            "open_positions": self.open_positions,
            "open_positions_value": open_positions_value,
            "total_portfolio_value": total_portfolio,
            "invested_percentage": (open_positions_value / total_portfolio * 100) if total_portfolio > 0 else 0,
            "cash_percentage": (cash_available / total_portfolio * 100) if total_portfolio > 0 else 100
        })
        
        return portfolio_status
    
    def _evaluate_open_positions(self, predictions, portfolio_status):
        """Evalúa si vender posiciones abiertas"""
        sell_decisions = {}
        
        if not self.open_positions:
            logging.info("📊 No hay posiciones abiertas para evaluar")
            return sell_decisions
        
        logging.info(f"📊 Evaluando {len(self.open_positions)} posiciones abiertas...")
        
        for ticker, position in self.open_positions.items():
            if ticker not in predictions:
                continue
            
            pred = predictions[ticker]
            should_sell = False
            sell_reason = ""
            
            # RAZÓN 1: Modelo predice SELL con alta confianza
            if pred['prediction'] == 'SELL' and pred['confidence'] >= self.sell_confidence_threshold:
                should_sell = True
                sell_reason = f"Modelo predice SELL con {pred['confidence']:.1%} confianza"
            
            # RAZÓN 2: Stop Loss (simulado)
            # TODO: Calcular P&L real cuando tengamos precios actuales
            # current_pnl = (current_price - entry_price) / entry_price
            # if current_pnl <= self.stop_loss_threshold:
            #     should_sell = True
            #     sell_reason = f"Stop Loss activado ({current_pnl:.1%})"
            
            # RAZÓN 3: Take Profit (simulado)
            # if current_pnl >= self.take_profit_threshold:
            #     should_sell = True
            #     sell_reason = f"Take Profit activado ({current_pnl:.1%})"
            
            if should_sell:
                sell_decisions[ticker] = {
                    "action": "SELL",
                    "reason": sell_reason,
                    "confidence": pred['confidence'],
                    "position_value": position.get("amount_usdc", 0),
                    "current_position": position
                }
                logging.info(f"🔴 {ticker}: VENDER - {sell_reason}")
            else:
                logging.info(f"✋ {ticker}: MANTENER - Confianza SELL: {pred['confidence']:.1%}")
        
        return sell_decisions
    
    def _find_buy_opportunities(self, predictions, portfolio_status):
        """Busca nuevas oportunidades de compra"""
        buy_opportunities = []
        
        # Calcular dinero disponible para nuevas compras
        cash_available = portfolio_status["cash_available"]
        total_portfolio = portfolio_status["total_portfolio_value"]
        current_invested = portfolio_status["invested_percentage"] / 100
        
        # Reserva mínima de cash
        min_cash_needed = total_portfolio * self.min_cash_reserve
        max_available_for_new_buys = max(0, cash_available - min_cash_needed)
        
        # Límite de inversión total
        max_additional_investment = max(0, (total_portfolio * self.max_total_invested) - portfolio_status["open_positions_value"])
        available_for_buys = min(max_available_for_new_buys, max_additional_investment)
        
        logging.info(f"💰 Dinero disponible para compras: ${available_for_buys:.2f}")
        
        if available_for_buys < total_portfolio * self.min_position_size:
            logging.info("⚠️ No hay suficiente dinero para nuevas posiciones")
            return {}
        
        # Buscar oportunidades BUY
        for ticker, pred in predictions.items():
            # Solo comprar si:
            # 1. Modelo predice BUY con alta confianza
            # 2. No tenemos ya una posición abierta en este activo
            if (pred['prediction'] == 'BUY' and 
                pred['confidence'] >= self.buy_confidence_threshold and 
                ticker not in self.open_positions):
                
                buy_opportunities.append({
                    "ticker": ticker,
                    "confidence": pred['confidence'],
                    "buy_confidence": pred['buy_confidence']
                })
                
                logging.info(f"🟢 {ticker}: OPORTUNIDAD - Confianza: {pred['confidence']:.1%}")
        
        # Ordenar por confianza descendente
        buy_opportunities.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Seleccionar las mejores y asignar capital
        buy_decisions = {}
        allocated_capital = 0
        
        for opportunity in buy_opportunities:
            ticker = opportunity['ticker']
            confidence = opportunity['confidence']
            
            # Calcular tamaño de posición basado en confianza
            # Más confianza = más dinero (entre min y max position size)
            confidence_factor = (confidence - self.buy_confidence_threshold) / (1 - self.buy_confidence_threshold)
            position_size_pct = self.min_position_size + (confidence_factor * (self.max_position_size - self.min_position_size))
            
            position_value = total_portfolio * position_size_pct
            
            # Verificar que no excedemos límites
            if allocated_capital + position_value <= available_for_buys:
                buy_decisions[ticker] = {
                    "action": "BUY",
                    "confidence": confidence,
                    "position_size_pct": position_size_pct * 100,
                    "position_value": position_value,
                    "reasoning": f"Alta confianza BUY ({confidence:.1%}), posición {position_size_pct*100:.1f}%"
                }
                
                allocated_capital += position_value
                logging.info(f"✅ {ticker}: COMPRAR ${position_value:.2f} ({position_size_pct*100:.1f}%)")
            else:
                logging.info(f"⚠️ {ticker}: Sin fondos suficientes para esta oportunidad")
                break
        
        return buy_decisions
    
    def _combine_decisions(self, buy_decisions, sell_decisions):
        """Combina decisiones de compra y venta"""
        all_decisions = {}
        
        # Añadir ventas
        for ticker, decision in sell_decisions.items():
            all_decisions[ticker] = decision
        
        # Añadir compras
        for ticker, decision in buy_decisions.items():
            all_decisions[ticker] = decision
        
        # Para el resto de activos: HOLD
        # TODO: Obtener lista completa de tickers monitoreados
        
        return all_decisions
    
    def _save_and_report(self, decisions, portfolio_status):
        """Guarda decisiones y genera reporte"""
        
        # Estadísticas
        buy_count = len([d for d in decisions.values() if d["action"] == "BUY"])
        sell_count = len([d for d in decisions.values() if d["action"] == "SELL"])
        total_buy_value = sum(d.get("position_value", 0) for d in decisions.values() if d["action"] == "BUY")
        total_sell_value = sum(d.get("position_value", 0) for d in decisions.values() if d["action"] == "SELL")
        
        # Resumen
        trading_summary = {
            "timestamp": datetime.now().isoformat(),
            "strategy": "LONG_ONLY",
            "decisions": decisions,
            "portfolio_status": portfolio_status,
            "statistics": {
                "buy_orders": buy_count,
                "sell_orders": sell_count,
                "total_buy_value": round(total_buy_value, 2),
                "total_sell_value": round(total_sell_value, 2),
                "net_investment": round(total_buy_value - total_sell_value, 2),
                "cash_after_trades": round(portfolio_status["cash_available"] + total_sell_value - total_buy_value, 2)
            }
        }
        
        # Guardar en archivos
        signals_for_compatibility = {}
        for ticker, decision in decisions.items():
            signals_for_compatibility[ticker] = decision["action"]
        
        # Archivo de señales básico (compatibilidad)
        with open(os.path.join(project_root, 'signals.json'), 'w') as f:
            json.dump(signals_for_compatibility, f, indent=4)
        
        # Archivo de decisiones completo
        with open(os.path.join(project_root, 'long_only_decisions.json'), 'w') as f:
            json.dump(trading_summary, f, indent=4, default=str)
        
        # Log del resumen
        self._log_final_summary(trading_summary)
    
    def _log_final_summary(self, summary):
        """Log del resumen final"""
        stats = summary["statistics"]
        portfolio = summary["portfolio_status"]
        
        logging.info("\n" + "="*60)
        logging.info(" RESUMEN DE TRADING SOLO COMPRAS")
        logging.info("="*60)
        logging.info(f"💰 Portfolio total: ${portfolio['total_portfolio_value']:.2f}")
        logging.info(f"💵 Cash disponible: ${portfolio['cash_available']:.2f}")
        logging.info(f"📊 Posiciones abiertas: ${portfolio['open_positions_value']:.2f} ({portfolio['invested_percentage']:.1f}%)")
        logging.info(f"🟢 Nuevas compras: {stats['buy_orders']} por ${stats['total_buy_value']:.2f}")
        logging.info(f"🔴 Ventas: {stats['sell_orders']} por ${stats['total_sell_value']:.2f}")
        logging.info(f"💸 Inversión neta: ${stats['net_investment']:.2f}")
        logging.info(f"💵 Cash después: ${stats['cash_after_trades']:.2f}")
        
        if summary["decisions"]:
            logging.info("\n📋 DECISIONES:")
            for ticker, decision in summary["decisions"].items():
                action = decision["action"]
                value = decision.get("position_value", 0)
                conf = decision.get("confidence", 0)
                emoji = "🟢" if action == "BUY" else "🔴"
                logging.info(f"   {emoji} {ticker}: {action} ${value:.2f} (Conf: {conf:.1%})")
        
        logging.info("="*60)

# Función principal
def run_long_only_strategy():
    """Ejecuta la estrategia de solo compras"""
    system = LongOnlyTradingSystem()
    system.execute_long_only_strategy()

if __name__ == "__main__":
    run_long_only_strategy()