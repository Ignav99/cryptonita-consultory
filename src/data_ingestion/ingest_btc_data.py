# src/data_ingestion/ingest_data.py (VERSIÓN ÚNICA Y FINAL)

import yfinance as yf
import pandas as pd
from sqlalchemy import text
import sys, os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path: sys.path.insert(0, project_root)

from src.utils.db_connector import create_db_engine
from src.config import settings

def run_ingestion():
    """
    Script unificado y final para la ingesta de datos.
    Descarga BTC y los datos macro y los guarda en sus tablas.
    """
    engine = create_db_engine()
    if not engine: return

    tasks = {
        'asset_metrics': settings.ASSET_TICKERS,
        'macro_metrics': settings.MACRO_TICKERS
    }

    print("--- INICIANDO INGESTA DE DATOS (VERSIÓN FINAL) ---")

    for table_name, tickers in tasks.items():
        print(f"\n-> Procesando tabla '{table_name}'...")
        
        try:
            df = yf.download(tickers, start=settings.HISTORIC_START_DATE, end=settings.HISTORIC_END_DATE)
            if df.empty:
                print(f"  -> No se encontraron datos para {tickers}.")
                continue

            # --- LÓGICA DE CORRECCIÓN DEFINITIVA ---
            if isinstance(df.columns, pd.MultiIndex):
                # Para múltiples tickers, aplanar la estructura
                df = df.stack(level=1).reset_index()
                df.rename(columns={'level_1': 'ticker', 'Date': 'timestamp', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Adj Close':'adj_close', 'Volume': 'volume'}, inplace=True)
            else:
                # Para un solo ticker, solo renombrar
                df.reset_index(inplace=True)
                df.rename(columns={'Date': 'timestamp', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Adj Close':'adj_close', 'Volume': 'volume'}, inplace=True)
                df['ticker'] = tickers[0]
            # --- FIN DE LA CORRECCIÓN ---

            # Limpieza final de tipos
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0).astype('int64')
            df.dropna(subset=['close', 'timestamp'], inplace=True)
            
            # Asegurar que todas las columnas necesarias existen, rellenando si es necesario
            required_cols = ['ticker', 'timestamp', 'open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                if col not in df.columns: df[col] = 0.0 # Rellenar con 0 si falta (ej. VIX)
            final_df = df[required_cols]

            with engine.connect() as connection:
                with connection.begin() as transaction:
                    connection.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY;"))
                    final_df.to_sql(table_name, connection, if_exists='append', index=False, method='multi')
            print(f"  -> ¡Éxito! Se insertaron {len(final_df)} registros en '{table_name}'.")

        except Exception as e:
            print(f"  -> [ERROR] en la ingesta para la tabla '{table_name}': {e}")
            
    print("\n--- INGESTA DE DATOS DE MERCADO FINALIZADA ---")

if __name__ == "__main__":
    run_ingestion()