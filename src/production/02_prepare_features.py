# src/production/02_prepare_features.py (VERSIÓN FINAL Y ROBUSTA)

import pandas as pd
import numpy as np
import sqlalchemy
import os
import sys
import logging
import json

# --- Configuración ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.db_connector import create_db_engine

def run_feature_preparation():
    logging.info("--- [INICIO] Proceso de preparación de características (Versión Robusta) ---")
    
    engine = create_db_engine()
    if not engine:
        logging.error("No se pudo crear la conexión. Abortando."); return

    # --- 1. EXTRACCIÓN DE DATOS BRUTOS ---
    logging.info("Paso 1: Extrayendo datos brutos...")
    try:
        tables_to_load = {
            'asset_metrics': "SELECT * FROM asset_metrics",
            'derivatives_funding_rates': "SELECT * FROM derivatives_funding_rates",
            'macro_spy': "SELECT timestamp, close AS spy_close FROM macro_spy",
            'macro_vix': "SELECT timestamp, close AS vix_close FROM macro_vix",
            'macro_tnx': "SELECT timestamp, close AS tnx_close FROM macro_tnx",
            'macro_dxy': "SELECT timestamp, close AS dxy_close FROM macro_dx_y_nyb",
            'macro_gc': "SELECT timestamp, close AS gc_close FROM macro_gc",
            'macro_cl': "SELECT timestamp, close AS cl_close FROM macro_cl",
        }
        dataframes = {name: pd.read_sql(query, engine) for name, query in tables_to_load.items()}
        for name, df in dataframes.items():
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True).dt.normalize()
    except Exception as e:
        logging.error(f"Error en extracción: {e}"); return

    # --- 2. PROCESAMIENTO POR TICKER (LA CORRECCIÓN CLAVE) ---
    logging.info("Paso 2: Procesando características por cada ticker...")
    
    # Juntamos primero los datos que dependen del ticker
    crypto_df = pd.merge(dataframes['asset_metrics'], dataframes['derivatives_funding_rates'], on=['timestamp', 'ticker'], how='left')
    crypto_df['funding_rate'].fillna(0, inplace=True)
    
    def process_ticker_group(group):
        group.sort_values(by='timestamp', inplace=True)
        # Calcular EMAs y MACD
        ema_slow = group['close'].ewm(span=26, adjust=False).mean()
        ema_fast = group['close'].ewm(span=12, adjust=False).mean()
        group['ema_26'] = ema_slow
        group['macd'] = ema_fast - ema_slow
        group['macd_signal'] = group['macd'].ewm(span=9, adjust=False).mean()
        group['macd_hist'] = group['macd'] - group['macd_signal']
        # Calcular otras características
        group['log_return'] = np.log(group['close'] / group['close'].shift(1))
        group['volatility_7d'] = group['log_return'].rolling(7).std()
        group['price_to_ema_ratio'] = (group['close'] / group['ema_26']) - 1
        group['macd_norm'] = group['macd'] / group['close']
        return group

    processed_crypto_df = crypto_df.groupby('ticker', group_keys=False).apply(process_ticker_group)

    # --- 3. UNIÓN FINAL CON DATOS MACRO ---
    logging.info("Paso 3: Uniendo con datos macro...")
    master_df = processed_crypto_df
    for name in ['macro_spy', 'macro_vix', 'macro_tnx', 'macro_dxy', 'macro_gc', 'macro_cl']:
        master_df = pd.merge(master_df, dataframes[name], on='timestamp', how='left')

    # Rellenamos los huecos de los datos macro (ej. fines de semana)
    macro_cols = ['spy_close', 'vix_close', 'tnx_close', 'dxy_close', 'gc_close', 'cl_close']
    master_df.sort_values(by=['ticker', 'timestamp'], inplace=True)
    master_df[macro_cols] = master_df.groupby('ticker')[macro_cols].ffill()
    
    # Calculamos la última característica que depende de un macro
    master_df['log_return_gc_close'] = master_df.groupby('ticker')['gc_close'].transform(lambda x: np.log(x / x.shift(1)))
    
    # --- 4. FILTRADO Y LIMPIEZA FINAL ---
    logging.info("Paso 4: Filtrando a las 15 características finales y guardando...")
    try:
        features_path = os.path.join(project_root, 'notebooks', 'important_features.json')
        with open(features_path, 'r') as f:
            important_feature_names = json.load(f)
        original_model_features = [col.split('__')[1] for col in important_feature_names]
        structural_cols = ['timestamp', 'ticker', 'open', 'high', 'low', 'close', 'volume']
        final_cols_to_keep = list(set(original_model_features + structural_cols))
        model_ready_df = master_df[final_cols_to_keep].copy()
        
        # Corrección de look-ahead bias
        feature_cols_only = [col for col in original_model_features if col in model_ready_df.columns]
        model_ready_df[feature_cols_only] = model_ready_df.groupby('ticker')[feature_cols_only].shift(1)
        
        model_ready_df.dropna(inplace=True)
        
        # Verificación final de duplicados
        duplicates = model_ready_df.duplicated(subset=['timestamp', 'ticker']).sum()
        if duplicates > 0:
            logging.error(f"¡ALERTA! Se encontraron {duplicates} duplicados incluso después del nuevo proceso.")
            model_ready_df.drop_duplicates(subset=['timestamp', 'ticker'], keep='last', inplace=True)
        
        model_ready_df.reset_index(drop=True, inplace=True)
        output_path = os.path.join(project_root, 'notebooks', 'dataframes', 'model_input_features.parquet')
        model_ready_df.to_parquet(output_path)
        
        logging.info(f"✅ ¡Éxito! DataFrame guardado en: {output_path}")
        logging.info(f"   -> Forma final: {model_ready_df.shape}")
        
    except Exception as e:
        logging.error(f"Error en el filtrado y guardado: {e}"); return

if __name__ == "__main__":
    run_feature_preparation()