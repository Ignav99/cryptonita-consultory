# src/production/05_strategy_simulation.py (VERSIÓN DEFINITIVA)

import pandas as pd
import numpy as np
import json
import os
import sys
import logging
import vectorbt as vbt
import joblib

# --- Configuración ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def run_full_simulation():
    """
    Carga el modelo y los datos, y ejecuta una simulación de trading completa
    a lo largo de todo el histórico de datos con una lógica robusta.
    """
    logging.info("--- [INICIO] Simulación de Estrategia Completa (Versión Robusta) ---")

    # --- 1. Cargar Artefactos ---
    try:
        model_path = os.path.join(project_root, 'models', 'ULTRA_MODEL_PACKAGE.joblib')
        model_package = joblib.load(model_path)
        primary_model = model_package['primary_model_pipeline']
        meta_model = model_package['meta_model']
        optimal_threshold = model_package['optimal_threshold']
        model_features_list = model_package['feature_list']
        logging.info("✅ Modelo Maestro cargado.")

        data_path = os.path.join(project_root, 'notebooks', 'dataframes', 'model_input_features.parquet')
        features_df = pd.read_parquet(data_path)
        features_df['timestamp'] = pd.to_datetime(features_df['timestamp'], utc=True)
        # NO establecemos el índice aquí para evitar problemas de duplicados
        logging.info(f"✅ Datos de características cargados (Shape: {features_df.shape}).")
        
    except Exception as e:
        logging.error(f"❌ Error al cargar artefactos: {e}"); return

    # --- 2. GENERACIÓN DE SEÑALES (MÉTODO ROBUSTO) ---
    logging.info("\n--- [SIMULACIÓN] Generando señales para todo el histórico...")
    
    all_tickers = features_df['ticker'].unique()
    
    # --- INICIO DE LA CORRECCIÓN CLAVE ---
    all_signals_list = [] # Guardaremos las señales en una lista
    
    for ticker in all_tickers:
        print(f" -> Procesando histórico para: {ticker}")
        
        # Filtramos los datos para el ticker actual
        ticker_data = features_df[features_df['ticker'] == ticker].set_index('timestamp')
        
        # Seleccionamos solo las 15 características que el modelo necesita
        original_model_features = [col.split('__')[1] for col in model_features_list]
        ticker_features = ticker_data[original_model_features]
        
        if ticker_features.empty: continue

        # Generar predicciones
        primary_proba = primary_model.predict_proba(ticker_features)
        primary_preds = np.argmax(primary_proba, axis=1)
        
        meta_features = pd.DataFrame({'primary_model_prob': primary_proba.max(axis=1)}, index=ticker_features.index)
        meta_confidence = meta_model.predict_proba(meta_features)[:, 1]
        
        passes_threshold = meta_confidence >= optimal_threshold
        
        # Creamos una serie de señales: 1 para Compra, -1 para Venta, 0 para Mantener
        signals = np.zeros(len(ticker_features))
        signals[(primary_preds == 1) & passes_threshold] = 1  # BUY
        signals[(primary_preds == 0) & passes_threshold] = -1 # SELL
        
        signals_series = pd.Series(signals, index=ticker_features.index, name=ticker)
        all_signals_list.append(signals_series)

    # Unimos todas las series de señales en un único DataFrame
    signals_df = pd.concat(all_signals_list, axis=1)
    
    # Convertimos a señales de entrada y salida para vectorbt
    entries = signals_df == 1
    exits = signals_df == -1
    # --- FIN DE LA CORRECCIÓN CLAVE ---
    
    logging.info("✅ Señales generadas para todo el histórico.")

    # --- 3. EJECUCIÓN DEL BACKTEST COMPLETO ---
    logging.info("\n--- [BACKTEST] Ejecutando simulación de portfolio...")
    
    # Pivotamos los precios para que tengan el formato correcto (índice=fecha, columnas=tickers)
    close_prices = features_df.pivot(index='timestamp', columns='ticker', values='close')
    
    portfolio = vbt.Portfolio.from_signals(
        close=close_prices,
        entries=entries,
        exits=exits,
        fees=0.002,
        sl_stop=0.05,
        init_cash=100000,
        freq='D'
    )
    
    print("\n" + "="*50); print(" " * 10 + "INFORME FINAL DE LA SIMULACIÓN COMPLETA"); print("="*50)
    print(portfolio.stats())

if __name__ == "__main__":
    run_full_simulation()