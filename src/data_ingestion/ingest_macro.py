# src/data_ingestion/ingest_macro.py (VERSIÓN FINAL Y DEFINITIVA)

import yfinance as yf
import pandas as pd
from sqlalchemy import text
import time
import sys, os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.db_connector import create_db_engine
from src.config import settings

def run_macro_ingestion_and_verification():
    tickers = settings.MACRO_TICKERS
    
    print(f"--- INICIANDO TAREA AUTÓNOMA: INGESTA DE DATOS MACRO ---")
    
    engine = create_db_engine()
    if not engine: return

    for ticker in tickers:
        table_name = f"macro_{ticker.lower().replace('^', '').replace('-', '_').replace('=f', '').replace('.', '_')}"
        
        print(f"\n-> Procesando indicador: {ticker} -> Tabla: {table_name}")

        try:
            df = yf.download(ticker, start=settings.HISTORIC_START_DATE, end=settings.HISTORIC_END_DATE, auto_adjust=True)
            if df.empty:
                print(f"    -> ADVERTENCIA: No se encontraron datos para {ticker}.")
                continue
            
            # --- LÓGICA DE CORRECCIÓN DEFINITIVA ---
            df.reset_index(inplace=True)
            # Como yfinance devuelve tuplas en las columnas, accedemos al primer elemento ([0]) y lo ponemos en minúsculas
            df.columns = [col[0].lower() if isinstance(col, tuple) else col.lower() for col in df.columns]
            df.rename(columns={'date': 'timestamp'}, inplace=True)
            # --- FIN DE LA CORRECCIÓN ---

            if 'volume' not in df.columns:
                df['volume'] = 0
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0).astype('int64')

            final_df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

            with engine.connect() as connection:
                with connection.begin() as transaction:
                    connection.execute(text(f"DROP TABLE IF EXISTS {table_name};"))
                    connection.execute(text(f"""
                        CREATE TABLE {table_name} (
                            timestamp TIMESTAMPTZ PRIMARY KEY,
                            open NUMERIC, high NUMERIC, low NUMERIC,
                            close NUMERIC, volume BIGINT
                        );
                    """))
                    final_df.to_sql(table_name, connection, if_exists='append', index=False, method='multi')

            with engine.connect() as connection:
                count = connection.execute(text(f"SELECT COUNT(*) FROM {table_name};")).scalar_one()
                print(f"  -> ¡VERIFICACIÓN EXITOSA! La tabla '{table_name}' contiene {count} registros.")

        except Exception as e:
            print(f"  -> [ERROR] al procesar {ticker}: {e}")
        
        time.sleep(1)

    print("\n--- INGESTA DE DATOS MACRO FINALIZADA ---")

if __name__ == "__main__":
    run_macro_ingestion_and_verification()