# src/production/01_ingest_daily_data.py (VERSIÓN DE PRODUCCIÓN FINAL)

import pandas as pd
from sqlalchemy import text
from datetime import datetime, timedelta
import sys
import os
import logging
import requests
import time
import yfinance as yf

# --- Configuración ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.db_connector import create_db_engine
from src.config import settings

# --- FUNCIONES DE INGESTA ESPECIALIZADAS Y ROBUSTAS ---

def ingest_daily_asset_metrics(engine, ticker_mapping, start_date, end_date):
    """Ingesta datos de precios desde Binance, ticker por ticker."""
    table_name = 'asset_metrics'
    logging.info(f"Iniciando ingesta diaria para '{table_name}' desde Binance...")
    all_tickers_data = []

    for yahoo_ticker, binance_symbol in ticker_mapping.items():
        if yahoo_ticker not in settings.UNIVERSE_TICKERS: continue
        try:
            url_klines = "https://api.binance.com/api/v3/klines"
            start_ts = int(start_date.timestamp() * 1000)
            params = {'symbol': binance_symbol, 'interval': '1d', 'startTime': start_ts, 'limit': 1000}
            response = requests.get(url_klines, params=params)
            response.raise_for_status()
            data = response.json()
            if not data: continue

            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
            df['ticker'] = yahoo_ticker
            all_tickers_data.append(df[['timestamp', 'ticker', 'open', 'high', 'low', 'close', 'volume']])
        except Exception as e:
            logging.warning(f" -> No se pudieron obtener precios para {yahoo_ticker}: {e}")
        time.sleep(0.3)

    if not all_tickers_data:
        logging.warning("No se pudo obtener datos de precios para ningún activo."); return True

    final_df_api = pd.concat(all_tickers_data, ignore_index=True).dropna()
    
    with engine.connect() as connection:
        max_ts_query = f"SELECT ticker, MAX(timestamp) as max_ts FROM {table_name} GROUP BY ticker"
        df_db_max_ts = pd.read_sql(max_ts_query, connection)
        
        new_records = final_df_api.merge(df_db_max_ts, on='ticker', how='left')
        new_records['max_ts'] = new_records['max_ts'].fillna(pd.Timestamp.min.tz_localize('UTC'))
        new_records = new_records[new_records['timestamp'] > new_records['max_ts']]
        
        if not new_records.empty:
            logging.info(f"Insertando {len(new_records)} nuevos registros en '{table_name}'...")
            new_records[['timestamp', 'ticker', 'open', 'high', 'low', 'close', 'volume']].to_sql(table_name, connection, if_exists='append', index=False)
        else:
            logging.info(f"No hay registros de precios nuevos para insertar.")
    logging.info(f"✅ Ingesta diaria para '{table_name}' completada.")
    return True

def ingest_daily_funding_rates(engine, ticker_mapping, start_date):
    """
    Ingesta incremental de funding rates desde Binance. NO VACÍA LA TABLA.
    """
    table_name = 'derivatives_funding_rates'
    logging.info(f"Iniciando ingesta diaria incremental para '{table_name}'...")
    
    with engine.connect() as connection:
        max_ts_query = f"SELECT ticker, MAX(timestamp) as max_ts FROM {table_name} GROUP BY ticker"
        df_db_max_ts = pd.read_sql(max_ts_query, connection)

    all_funding_data = []
    for yahoo_ticker, binance_symbol in ticker_mapping.items():
        if yahoo_ticker not in settings.UNIVERSE_TICKERS: continue
        
        # Determinamos la fecha de inicio para este ticker
        db_max_ts_ticker = df_db_max_ts[df_db_max_ts['ticker'] == yahoo_ticker]
        start_ts_ticker = int(start_date.timestamp() * 1000)
        if not db_max_ts_ticker.empty:
            # Empezamos a buscar justo después del último registro que tenemos
            start_ts_ticker = int(db_max_ts_ticker['max_ts'].iloc[0].timestamp() * 1000) + 1

        try:
            url_fr = "https://fapi.binance.com/fapi/v1/fundingRate"
            params_fr = {'symbol': binance_symbol, 'startTime': start_ts_ticker, 'limit': 1000}
            response_fr = requests.get(url_fr, params=params_fr)
            response_fr.raise_for_status()
            data_fr = response_fr.json()
            if data_fr:
                df_funding = pd.DataFrame(data_fr)
                df_funding['timestamp'] = pd.to_datetime(df_funding['fundingTime'], unit='ms', utc=True)
                df_funding['funding_rate'] = pd.to_numeric(df_funding['fundingRate'])
                df_funding['ticker'] = yahoo_ticker
                all_funding_data.append(df_funding[['timestamp', 'ticker', 'funding_rate']])
        except Exception as e:
            logging.warning(f" -> No se pudieron obtener funding rates para {yahoo_ticker}: {e}")
        time.sleep(0.3)

    if not all_funding_data:
        logging.info(f"No hay registros de funding rates nuevos para insertar."); return True
        
    final_df = pd.concat(all_funding_data, ignore_index=True).dropna()
    
    with engine.connect() as connection:
        if not final_df.empty:
            logging.info(f"Insertando {len(final_df)} nuevos registros en '{table_name}'...")
            final_df.to_sql(table_name, connection, if_exists='append', index=False)
    logging.info(f"✅ Ingesta diaria para '{table_name}' completada.")
    return True

def ingest_daily_macro_data(engine, ticker, table_name, start_date, end_date):
    """Ingesta datos diarios para tablas macro (sin ticker)."""
    logging.info(f"Iniciando ingesta diaria para '{table_name}'...")
    try:
        df_api = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if df_api.empty:
            logging.warning(f"yf.download no devolvió datos para '{ticker}'."); return True
        if isinstance(df_api.columns, pd.MultiIndex):
            df_api.columns = df_api.columns.droplevel(1)
        df_api.reset_index(inplace=True)
        df_api = df_api.rename(columns={'Date': 'timestamp', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
        df_api = df_api[['timestamp', 'open', 'high', 'low', 'close', 'volume']].copy()
        df_api['timestamp'] = pd.to_datetime(df_api['timestamp'], utc=True)
        df_api.dropna(subset=['timestamp', 'close'], inplace=True)
        with engine.connect() as connection:
            max_timestamp_query = f"SELECT MAX(timestamp) as max_ts FROM {table_name}"
            max_ts_in_db = pd.read_sql(max_timestamp_query, connection).iloc[0, 0]
            if pd.notna(max_ts_in_db): final_df = df_api[df_api['timestamp'] > max_ts_in_db]
            else: final_df = df_api
            if not final_df.empty:
                final_df.to_sql(table_name, connection, if_exists='append', index=False)
        logging.info(f"✅ Ingesta diaria para '{table_name}' completada.")
        return True
    except Exception as e:
        logging.error(f"❌ Fallo en la ingesta diaria de '{table_name}': {e}"); return False

# --- FUNCIÓN PRINCIPAL ---
def run_daily_ingestion():
    engine = create_db_engine()
    if not engine: return
    
    # --- LÓGICA DE FECHAS CORREGIDA ---
    # Pedimos datos hasta 1 hora antes para asegurar que están consolidados
    end_date = datetime.now() - timedelta(hours=1)
    start_date = end_date - timedelta(days=7) # Un margen de seguridad de 7 días
    
    logging.info(f"Iniciando ingesta diaria para datos hasta: {end_date.strftime('%Y-%m-%d %H:%M')}")
    
    # --- EJECUCIÓN DE TODAS LAS FASES ---
    success_assets = ingest_daily_asset_metrics(engine, settings.TICKER_TO_BINANCE, start_date, end_date)
    success_funding = ingest_daily_funding_rates(engine, settings.TICKER_TO_BINANCE, start_date)
    
    success_macros = True
    for ticker, table_name in settings.MACRO_TICKERS.items():
        if not ingest_daily_macro_data(engine, ticker, table_name, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')):
            success_macros = False
            
    if success_assets and success_funding and success_macros:
        logging.info("\n🎉 Proceso de ingesta diaria completado con éxito.")
    else:
        logging.warning("\n⚠️ El proceso de ingesta diaria finalizó con uno o más errores.")

if __name__ == "__main__":
    run_daily_ingestion()