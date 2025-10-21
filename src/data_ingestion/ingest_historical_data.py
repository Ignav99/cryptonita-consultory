# src/data_ingestion/ingest_historical_data.py (VERSIÓN CORREGIDA)

import yfinance as yf
import pandas as pd
from sqlalchemy import text
from datetime import datetime, timedelta
import sys
import os
import logging
import requests
import time

# (La configuración de logging y path no cambia)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.db_connector import create_db_engine
from src.config import settings

# (La función ingest_asset_metrics no cambia)
def ingest_asset_metrics(engine, tickers, start_date, end_date):
    logging.info(f"Iniciando ingesta de 'asset_metrics' para {len(tickers)} tickers...")
    table_name = 'asset_metrics'
    try:
        df = yf.download(tickers, start=start_date, end=end_date, progress=False)
        df_processed = df.stack(level=1).reset_index().rename(columns={
            'Date': 'timestamp', 'Ticker': 'ticker', 'Open': 'open', 'High': 'high', 
            'Low': 'low', 'Close': 'close', 'Volume': 'volume'
        })
        final_df = df_processed[['timestamp', 'ticker', 'open', 'high', 'low', 'close', 'volume']].copy()
        final_df['volume'] = pd.to_numeric(final_df['volume'], errors='coerce').fillna(0)
        final_df.dropna(subset=['close', 'timestamp', 'ticker'], inplace=True)
        with engine.connect() as connection:
            with connection.begin() as transaction:
                connection.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;"))
                final_df.to_sql(table_name, connection, if_exists='append', index=False)
        logging.info(f"✅ Ingesta de '{table_name}' completada.")
        return True
    except Exception as e:
        logging.error(f"❌ Fallo en la ingesta de '{table_name}': {e}")
        return False

# (La función get_funding_rate_history no cambia)
def get_funding_rate_history(symbol, start_ts, end_ts, limit=1000):
    all_rates = []
    url = "https://fapi.binance.com/fapi/v1/fundingRate"
    while True:
        params = {'symbol': symbol, 'startTime': start_ts, 'endTime': end_ts, 'limit': limit}
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if not data: break
        all_rates.extend(data)
        start_ts = data[-1]['fundingTime'] + 1
        if len(data) < limit: break
        time.sleep(0.2)
    return all_rates

# (La función ingest_funding_rates no cambia)
def ingest_funding_rates(engine, ticker_mapping, start_date, end_date):
    logging.info(f"Iniciando ingesta de 'derivatives_funding_rates'...")
    table_name = 'derivatives_funding_rates'
    start_timestamp = int(start_date.timestamp() * 1000)
    end_timestamp = int(end_date.timestamp() * 1000)
    all_funding_data = []
    for yahoo_ticker, binance_symbol in ticker_mapping.items():
        logging.info(f"  -> Descargando funding rates para {yahoo_ticker} ({binance_symbol})...")
        try:
            rates = get_funding_rate_history(binance_symbol, start_timestamp, end_timestamp)
            if rates:
                df_funding = pd.DataFrame(rates)
                df_funding['timestamp'] = pd.to_datetime(df_funding['fundingTime'], unit='ms', utc=True)
                df_funding['funding_rate'] = pd.to_numeric(df_funding['fundingRate'])
                df_funding['ticker'] = yahoo_ticker
                all_funding_data.append(df_funding[['timestamp', 'ticker', 'funding_rate']])
                logging.info(f"    ✅ {len(df_funding)} registros obtenidos.")
        except Exception as e:
            logging.warning(f"    ⚠️ No se encontraron/falló {binance_symbol}: {e}")
    if not all_funding_data:
        final_df = pd.DataFrame(columns=['timestamp', 'ticker', 'funding_rate'])
    else:
        final_df = pd.concat(all_funding_data, ignore_index=True)
    with engine.connect() as connection:
        with connection.begin() as transaction:
            connection.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;"))
            if not final_df.empty:
                final_df.to_sql(table_name, connection, if_exists='append', index=False)
    logging.info(f"✅ Ingesta de '{table_name}' completada.")
    return True

# --- INICIO DE LA ACTUALIZACIÓN ---
def ingest_macro_data(engine, macro_tickers, start_date, end_date):
    """Descarga datos macro y los guarda en sus tablas, corrigiendo las columnas."""
    logging.info("Iniciando ingesta de datos Macro...")
    all_success = True
    for ticker, table_name in macro_tickers.items():
        try:
            logging.info(f"Procesando {ticker} para la tabla '{table_name}'...")
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            
            # CORRECCIÓN: Aplanar las columnas si yfinance devuelve un MultiIndex
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)

            df.reset_index(inplace=True)
            df = df.rename(columns={'Date': 'timestamp', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
            final_df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].copy()

            with engine.connect() as connection:
                with connection.begin() as transaction:
                    connection.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;"))
                    final_df.to_sql(table_name, connection, if_exists='append', index=False)
            logging.info(f" -> Ingesta de '{table_name}' completada.")
        except Exception as e:
            logging.error(f"❌ Fallo en la ingesta de '{table_name}': {e}")
            all_success = False
    if all_success:
        logging.info("✅ Ingesta de todos los datos Macro completada.")
    return all_success
# --- FIN DE LA ACTUALIZACIÓN ---


# (La función principal 'run_historical_ingestion' no cambia)
def run_historical_ingestion():
    engine = create_db_engine()
    if not engine: return
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3*365)
    logging.info(f"Rango de fechas para la ingesta: {start_date.date()} a {end_date.date()}")
    
    success1 = ingest_asset_metrics(engine, settings.UNIVERSE_TICKERS, start_date, end_date)
    success2 = ingest_funding_rates(engine, settings.TICKER_TO_BINANCE, start_date, end_date)
    success3 = ingest_macro_data(engine, settings.MACRO_TICKERS, start_date, end_date)
    
    if success1 and success2 and success3:
        logging.info("\n🎉 Proceso de ingesta histórica completado con éxito.")
    else:
        logging.warning("\n⚠️ El proceso de ingesta histórica finalizó con uno o más errores.")

if __name__ == "__main__":
    run_historical_ingestion()