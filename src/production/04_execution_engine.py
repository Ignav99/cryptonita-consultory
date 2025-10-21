# src/production/04_execution_engine.py (VERSIÓN REAL)

import json
import os
import sys
import logging
import time

# --- Configuración ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.production.exchange_connector import BinanceConnector
from src.config import settings

def run_execution_engine():
    """
    Ejecuta el ciclo de trading completo: lee señales, consulta el estado
    del portfolio y envía las órdenes necesarias al exchange.
    """
    logging.info("--- [INICIO] Motor de Ejecución Iniciado ---")

    # --- 1. Cargar Señales del Modelo ---
    try:
        signals_path = os.path.join(project_root, 'signals.json')
        with open(signals_path, 'r') as f:
            signals = json.load(f)
        logging.info(f"✅ Señales cargadas para {len(signals)} tickers.")
    except Exception as e:
        logging.error(f"❌ No se pudo cargar 'signals.json': {e}")
        return

    # --- 2. Conectar al Exchange ---
    connector = BinanceConnector()
    if not connector.exchange:
        logging.error("❌ No se pudo conectar al exchange. Abortando.")
        return

    # --- 3. Obtener Estado Actual del Portfolio ---
    balance_usdt = connector.get_balance('USDT')
    if balance_usdt is None or balance_usdt <= 10: # Umbral de seguridad
        logging.error(f"❌ Balance insuficiente o no disponible ({balance_usdt} USDT). Abortando.")
        return
    
    logging.info(f"💰 Balance disponible en cuenta de Futuros: {balance_usdt:.2f} USDT")

    # --- 4. Lógica de Decisión y Ejecución ---
    # Usamos el parámetro de riesgo definido en settings.py
    RISK_PER_TRADE = getattr(settings, 'RISK_PER_TRADE', 0.01) # 1% por defecto
    
    for yahoo_ticker, signal in signals.items():
        # Traducir el ticker al formato que usa Binance (ej. 'BTC/USDT')
        binance_symbol = settings.TICKER_MAP_BINANCE.get(yahoo_ticker)
        if not binance_symbol:
            logging.warning(f" -> No se encontró mapeo para {yahoo_ticker}. Saltando.")
            continue

        logging.info(f"\n--- Procesando {yahoo_ticker} ({binance_symbol}) ---")
        
        # Consultamos la posición actual en el exchange
        current_position = connector.get_position(binance_symbol)
        logging.info(f" -> Posición actual: {current_position} {yahoo_ticker.split('-')[0]}")
        logging.info(f" -> Señal del modelo: {signal}")

        # Lógica de Trading (solo opera en largo por ahora)
        if signal == "BUY" and current_position == 0:
            # Si la señal es COMPRAR y no tenemos posición...
            price = connector.get_ticker_price(binance_symbol)
            if price:
                amount_to_invest = balance_usdt * RISK_PER_TRADE
                order_size = round(amount_to_invest / price, 3) # Redondear a 3 decimales para la mayoría de pares
                logging.info(f"   -> ACCIÓN: ABRIR ORDEN DE COMPRA de {order_size} {binance_symbol}")
                # DESCOMENTA LA SIGUIENTE LÍNEA PARA OPERAR EN REAL
                # connector.create_market_order(binance_symbol, 'buy', order_size)
            else:
                logging.error("   -> No se pudo obtener el precio para calcular el tamaño de la orden.")
        
        elif signal == "SELL" and current_position > 0:
            # Si la señal es VENDER y SÍ tenemos una posición comprada...
            logging.info(f"   -> ACCIÓN: CERRAR POSICIÓN de {current_position} {binance_symbol}")
            # DESCOMENTA LA SIGUIENTE LÍNEA PARA OPERAR EN REAL
            # connector.create_market_order(binance_symbol, 'sell', current_position)

        else:
            # En cualquier otro caso (HOLD, o BUY cuando ya estamos comprados, etc.)
            logging.info("   -> ACCIÓN: NO HACER NADA (Mantener)")
        
        time.sleep(1) # Pequeña pausa para no saturar la API

    logging.info("\n--- [FIN] Motor de Ejecución Finalizado ---")

if __name__ == "__main__":
    run_execution_engine()