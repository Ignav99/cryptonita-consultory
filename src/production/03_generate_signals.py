# src/production/03_generate_signals.py - VERSIÓN FINAL INTEGRADA

import pandas as pd
import numpy as np
import joblib
import os
import sys
import logging
import json
from datetime import datetime

# --- Configuración ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importar sistema de gestión de dinero
from src.trading.advanced_money_management import advanced_money_manager

class CryptonitaTradingBot:
    """
    Bot de Trading Cryptonita - VERSIÓN FINAL
    Estrategia: Solo posiciones LONG
    - Compra cuando modelo dice BUY con 75%+ confianza
    - Vende solo posiciones abiertas cuando modelo dice SELL con 70%+ confianza
    - Recicla dinero automáticamente
    """
    
    def __init__(self):
        # PARÁMETROS DE TRADING
        self.buy_confidence_threshold = 0.75    # 75% mínimo para comprar
        self.sell_confidence_threshold = 0.70   # 70% para vender posiciones abiertas
        
        # GESTIÓN DE DINERO
        self.min_position_size = 0.08           # 8% mínimo por posición
        self.max_position_size = 0.15           # 15% máximo por posición
        self.max_total_invested = 0.85          # 85% máximo invertido
        self.min_cash_reserve = 0.15            # 15% siempre en cash
        
        # LÍMITES DE SEGURIDAD
        self.min_trade_amount = 30              # $30 mínimo por trade
        self.max_simultaneous_positions = 8     # Máximo 8 posiciones
        
        # SIMULACIÓN DE POSICIONES (TODO: reemplazar con datos reales)
        self.open_positions = {}
    
    def run_trading_bot(self):
        """Ejecuta el bot de trading completo"""
        logging.info("🤖 [INICIO] CRYPTONITA BOT - Estrategia Solo Compras")
        
        try:
            # 1. Cargar modelo y generar predicciones
            predictions = self._generate_model_predictions()
            if not predictions:
                return
            
            # 2. Obtener estado del portfolio real
            portfolio_status = self._get_real_portfolio_status()
            if portfolio_status["status"] != "healthy":
                logging.error("❌ Portfolio no saludable - Deteniendo bot")
                return
            
            # 3. Evaluar posiciones abiertas (decidir si vender)
            sell_decisions = self._evaluate_open_positions(predictions)
            
            # 4. Buscar nuevas oportunidades de compra
            buy_decisions = self._find_buy_opportunities(predictions, portfolio_status)
            
            # 5. Combinar todas las decisiones
            final_signals = self._create_final_signals(buy_decisions, sell_decisions, predictions)
            
            # 6. Guardar señales y generar reporte
            self._save_signals_and_report(final_signals, buy_decisions, sell_decisions, portfolio_status)
            
        except Exception as e:
            logging.error(f"❌ Error en el bot: {e}")
        
        logging.info("🤖 [FIN] CRYPTONITA BOT")
    
    def _generate_model_predictions(self):
        """Genera predicciones del modelo ML"""
        try:
            logging.info("🧠 Cargando modelo y generando predicciones...")
            
            # Cargar modelo
            model_path = os.path.join(project_root, 'models', 'ULTRA_MODEL_PACKAGE.joblib')
            model_package = joblib.load(model_path)
            primary_model = model_package['primary_model_pipeline']
            meta_model = model_package['meta_model']
            optimal_threshold = model_package['optimal_threshold']
            model_features_list = model_package['feature_list']
            
            # Cargar datos
            data_path = os.path.join(project_root, 'notebooks', 'dataframes', 'model_input_features.parquet')
            features_df = pd.read_parquet(data_path)
            
            # Preparar datos más recientes
            features_df['timestamp'] = pd.to_datetime(features_df['timestamp'])
            latest_features = features_df.sort_values('timestamp').groupby('ticker').last()
            
            original_model_features = [col.split('__')[1] for col in model_features_list]
            X = latest_features[original_model_features]
            
            # Generar predicciones
            primary_proba = primary_model.predict_proba(X)
            primary_preds = np.argmax(primary_proba, axis=1)
            
            meta_features = pd.DataFrame({'primary_model_prob': primary_proba.max(axis=1)}, index=X.index)
            meta_confidence = meta_model.predict_proba(meta_features)[:, 1]
            
            # Estructurar predicciones
            predictions = {}
            for i, ticker in enumerate(X.index):
                predictions[ticker] = {
                    'prediction': 'BUY' if primary_preds[i] == 1 else 'SELL',
                    'confidence': meta_confidence[i],
                    'buy_probability': primary_proba[i][1],
                    'sell_probability': primary_proba[i][0]
                }
            
            logging.info(f"✅ Predicciones generadas para {len(predictions)} activos")
            logging.info(f"📊 Threshold modelo: {optimal_threshold:.3f}, Bot BUY: {self.buy_confidence_threshold:.3f}")
            
            return predictions
            
        except Exception as e:
            logging.error(f"❌ Error generando predicciones: {e}")
            return None
    
    def _get_real_portfolio_status(self):
        """Obtiene estado real del portfolio desde Binance"""
        portfolio_status = advanced_money_manager.get_portfolio_status()
        
        # TODO: Cargar posiciones reales desde base de datos o exchange
        # Por ahora simulamos - pero aquí irían las posiciones reales
        self.open_positions = {
            # Ejemplo de formato:
            # "BTC-USD": {
            #     "amount_usdc": 150.0,
            #     "entry_price": 65000,
            #     "entry_date": "2025-07-30T10:00:00",
            #     "current_price": 66000  # Se actualizaría en tiempo real
            # }
        }
        
        # Calcular métricas del portfolio
        open_positions_value = sum(pos.get("amount_usdc", 0) for pos in self.open_positions.values())
        cash_available = portfolio_status["cash_available"]
        total_portfolio = cash_available + open_positions_value
        
        portfolio_status.update({
            "open_positions": self.open_positions,
            "open_positions_count": len(self.open_positions),
            "open_positions_value": open_positions_value,
            "total_portfolio_value": total_portfolio,
            "invested_percentage": (open_positions_value / total_portfolio * 100) if total_portfolio > 0 else 0,
            "cash_percentage": (cash_available / total_portfolio * 100) if total_portfolio > 0 else 100,
            "available_for_new_trades": max(0, cash_available - (total_portfolio * self.min_cash_reserve))
        })
        
        logging.info(f"💰 Portfolio Total: ${total_portfolio:.2f} | Cash: ${cash_available:.2f} | Posiciones: {len(self.open_positions)}")
        
        return portfolio_status
    
    def _evaluate_open_positions(self, predictions):
        """Evalúa si vender posiciones abiertas"""
        sell_decisions = {}
        
        if not self.open_positions:
            logging.info("📊 No hay posiciones abiertas para evaluar")
            return sell_decisions
        
        logging.info(f"📊 Evaluando {len(self.open_positions)} posiciones abiertas...")
        
        for ticker, position in self.open_positions.items():
            if ticker not in predictions:
                logging.warning(f"⚠️ {ticker}: No hay predicción disponible")
                continue
            
            pred = predictions[ticker]
            should_sell = False
            sell_reason = ""
            
            # CRITERIO PRINCIPAL: Modelo predice SELL con alta confianza
            if pred['prediction'] == 'SELL' and pred['confidence'] >= self.sell_confidence_threshold:
                should_sell = True
                sell_reason = f"Modelo predice SELL con {pred['confidence']:.1%} confianza"
            
            # TODO: Añadir más criterios de venta:
            # - Stop loss automático
            # - Take profit
            # - Time-based exit
            
            if should_sell:
                sell_decisions[ticker] = {
                    "action": "SELL",
                    "reason": sell_reason,
                    "confidence": pred['confidence'],
                    "position_value": position.get("amount_usdc", 0),
                    "expected_proceeds": position.get("amount_usdc", 0)  # Simplificado
                }
                logging.info(f"🔴 {ticker}: VENDER - {sell_reason}")
            else:
                logging.info(f"✋ {ticker}: MANTENER (Conf SELL: {pred['confidence']:.1%})")
        
        return sell_decisions
    
    def _find_buy_opportunities(self, predictions, portfolio_status):
        """Encuentra nuevas oportunidades de compra"""
        buy_opportunities = []
        
        # Dinero disponible para nuevas compras
        available_cash = portfolio_status["available_for_new_trades"]
        total_portfolio = portfolio_status["total_portfolio_value"]
        current_positions = len(self.open_positions)
        
        logging.info(f"💰 Dinero disponible para compras: ${available_cash:.2f}")
        
        # Verificar límites
        if available_cash < self.min_trade_amount:
            logging.info("⚠️ No hay suficiente cash para nuevas posiciones")
            return {}
        
        if current_positions >= self.max_simultaneous_positions:
            logging.info(f"⚠️ Ya tienes {current_positions} posiciones (máximo: {self.max_simultaneous_positions})")
            return {}
        
        # Buscar oportunidades BUY
        for ticker, pred in predictions.items():
            # Solo considerar si:
            # 1. Modelo predice BUY con alta confianza
            # 2. No tenemos ya esta posición abierta
            if (pred['prediction'] == 'BUY' and 
                pred['confidence'] >= self.buy_confidence_threshold and 
                ticker not in self.open_positions):
                
                buy_opportunities.append({
                    "ticker": ticker,
                    "confidence": pred['confidence'],
                    "buy_probability": pred['buy_probability']
                })
        
        logging.info(f"🔍 Encontradas {len(buy_opportunities)} oportunidades de compra")
        
        # Ordenar por confianza y seleccionar las mejores
        buy_opportunities.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Calcular tamaños de posición
        buy_decisions = {}
        allocated_capital = 0
        max_new_positions = self.max_simultaneous_positions - current_positions
        
        for i, opportunity in enumerate(buy_opportunities[:max_new_positions]):
            ticker = opportunity['ticker']
            confidence = opportunity['confidence']
            
            # Tamaño de posición basado en confianza
            confidence_excess = confidence - self.buy_confidence_threshold
            max_excess = 1.0 - self.buy_confidence_threshold
            confidence_factor = confidence_excess / max_excess
            
            position_size_pct = self.min_position_size + (confidence_factor * (self.max_position_size - self.min_position_size))
            position_value = total_portfolio * position_size_pct
            
            # Verificar límites
            if allocated_capital + position_value <= available_cash:
                buy_decisions[ticker] = {
                    "action": "BUY",
                    "confidence": confidence,
                    "position_size_pct": round(position_size_pct * 100, 1),
                    "position_value": round(position_value, 2),
                    "priority": i + 1,
                    "reasoning": f"BUY alta confianza ({confidence:.1%}) - Posición {position_size_pct*100:.1f}%"
                }
                
                allocated_capital += position_value
                logging.info(f"🟢 #{i+1} {ticker}: COMPRAR ${position_value:.2f} ({position_size_pct*100:.1f}%) - Conf: {confidence:.1%}")
            else:
                logging.info(f"⚠️ {ticker}: Sin fondos suficientes (necesita ${position_value:.2f})")
                break
        
        return buy_decisions
    
    def _create_final_signals(self, buy_decisions, sell_decisions, predictions):
        """Crea las señales finales para todos los activos"""
        final_signals = {}
        
        # Procesar todas las predicciones
        for ticker, pred in predictions.items():
            if ticker in buy_decisions:
                final_signals[ticker] = "BUY"
            elif ticker in sell_decisions:
                final_signals[ticker] = "SELL"
            else:
                final_signals[ticker] = "HOLD"
        
        # Estadísticas
        buy_count = len(buy_decisions)
        sell_count = len(sell_decisions)
        hold_count = len(final_signals) - buy_count - sell_count
        
        logging.info(f"📊 Señales finales: {buy_count} BUY, {sell_count} SELL, {hold_count} HOLD")
        
        return final_signals
    
    def _save_signals_and_report(self, signals, buy_decisions, sell_decisions, portfolio_status):
        """Guarda señales y genera reporte completo"""
        
        # Calcular estadísticas
        total_buy_value = sum(d["position_value"] for d in buy_decisions.values())
        total_sell_value = sum(d["position_value"] for d in sell_decisions.values())
        net_cash_flow = total_sell_value - total_buy_value
        
        # Crear reporte completo
        trading_report = {
            "timestamp": datetime.now().isoformat(),
            "strategy": "CRYPTONITA_LONG_ONLY",
            "model_version": "2.1_production",
            
            # Señales básicas (compatibilidad)
            "signals": signals,
            
            # Decisiones detalladas
            "buy_decisions": buy_decisions,
            "sell_decisions": sell_decisions,
            
            # Estado del portfolio
            "portfolio_status": portfolio_status,
            
            # Estadísticas de la sesión
            "session_stats": {
                "total_signals": len(signals),
                "buy_orders": len(buy_decisions),
                "sell_orders": len(sell_decisions),
                "hold_signals": len(signals) - len(buy_decisions) - len(sell_decisions),
                "total_buy_value": round(total_buy_value, 2),
                "total_sell_value": round(total_sell_value, 2),
                "net_cash_flow": round(net_cash_flow, 2),
                "cash_after_trades": round(portfolio_status["cash_available"] + net_cash_flow, 2)
            },
            
            # Configuración del bot
            "bot_config": {
                "buy_confidence_threshold": self.buy_confidence_threshold,
                "sell_confidence_threshold": self.sell_confidence_threshold,
                "min_position_size": self.min_position_size,
                "max_position_size": self.max_position_size,
                "max_total_invested": self.max_total_invested
            }
        }
        
        # Guardar archivos
        # 1. Señales básicas (compatibilidad con sistema existente)
        signals_path = os.path.join(project_root, 'signals.json')
        with open(signals_path, 'w') as f:
            json.dump(signals, f, indent=4)
        
        # 2. Reporte completo del bot
        bot_report_path = os.path.join(project_root, 'cryptonita_bot_report.json')
        with open(bot_report_path, 'w') as f:
            json.dump(trading_report, f, indent=4, default=str)
        
        # 3. Log del resumen final
        self._log_trading_summary(trading_report)
        
        logging.info(f"✅ Archivos guardados:")
        logging.info(f"   📄 {signals_path}")
        logging.info(f"   📊 {bot_report_path}")
    
    def _log_trading_summary(self, report):
        """Log del resumen de trading"""
        stats = report["session_stats"]
        portfolio = report["portfolio_status"]
        
        logging.info("\n" + "🤖"*20)
        logging.info(" CRYPTONITA BOT - RESUMEN DE SESIÓN")
        logging.info("🤖"*20)
        logging.info(f"💰 Portfolio Total: ${portfolio['total_portfolio_value']:.2f}")
        logging.info(f"💵 Cash Disponible: ${portfolio['cash_available']:.2f} ({portfolio['cash_percentage']:.1f}%)")
        logging.info(f"📊 Posiciones Abiertas: {portfolio['open_positions_count']} por ${portfolio['open_positions_value']:.2f}")
        logging.info(f"📈 % Invertido: {portfolio['invested_percentage']:.1f}%")
        logging.info("")
        logging.info(f"🟢 Nuevas Compras: {stats['buy_orders']} por ${stats['total_buy_value']:.2f}")
        logging.info(f"🔴 Ventas: {stats['sell_orders']} por ${stats['total_sell_value']:.2f}")
        logging.info(f"💸 Flujo Neto: ${stats['net_cash_flow']:.2f}")
        logging.info(f"💵 Cash Final: ${stats['cash_after_trades']:.2f}")
        logging.info("")
        
        # Detalles de operaciones
        if report["buy_decisions"]:
            logging.info("🟢 COMPRAS PLANIFICADAS:")
            for ticker, decision in report["buy_decisions"].items():
                logging.info(f"   #{decision['priority']} {ticker}: ${decision['position_value']:.2f} ({decision['position_size_pct']:.1f}%) - Conf: {decision['confidence']:.1%}")
        
        if report["sell_decisions"]:
            logging.info("🔴 VENTAS PLANIFICADAS:")
            for ticker, decision in report["sell_decisions"].items():
                logging.info(f"   {ticker}: ${decision['position_value']:.2f} - {decision['reason']}")
        
        logging.info("🤖"*20)
        logging.info(f"⚙️ Config: BUY≥{self.buy_confidence_threshold:.0%} | SELL≥{self.sell_confidence_threshold:.0%} | Max Pos: {self.max_simultaneous_positions}")
        logging.info("🤖"*20)

# Función principal
def run_inference():
    """Ejecuta el bot de trading Cryptonita"""
    bot = CryptonitaTradingBot()
    bot.run_trading_bot()

if __name__ == "__main__":
    run_inference()