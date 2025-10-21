# src/data_ingestion/ingest_data.py (VERSIÓN FINAL CON VERIFICACIÓN INTEGRADA)

import yfinance as yf
import pandas as pd
from sqlalchemy import text
import sys, os

# Configuración del path para poder importar desde 'src'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.db_connector import create_db_engine
from src.config import settings

def run_ingestion_and_verify():
    """
    Script definitivo que ingesta los datos y verifica el resultado inmediatamente.
    """
    engine = create_db_engine()
    if not engine:
        return

    tickers = settings.ASSET_TICKERS
    table_name = 'asset_metrics'

    # ====================================================================
    # FASE 1: PREPARACIÓN DE DATOS
    # ====================================================================
    print(f"--- FASE 1: Preparando datos para '{table_name}' ---")
    try:
        df = yf.download(tickers, start=settings.HISTORIC_START_DATE, end=settings.HISTORIC_END_DATE, progress=False)
        if df.empty:
            print(" -> No se encontraron datos para descargar.")
            return

        df_processed = df.stack(level=1).reset_index()
        df_processed = df_processed.rename(columns={
            'Date': 'timestamp', 'Ticker': 'ticker', 'Open': 'open',
            'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'
        })
        
        final_df = pd.DataFrame({
            'timestamp': df_processed['timestamp'], 'ticker': df_processed['ticker'],
            'open': df_processed['open'], 'high': df_processed['high'],
            'low': df_processed['low'], 'close': df_processed['close'],
            'volume': pd.to_numeric(df_processed['volume'], errors='coerce').fillna(0)
        })
        final_df.dropna(subset=['close', 'timestamp', 'ticker'], inplace=True)
        print(f" -> Datos preparados. {len(final_df)} filas listas para insertar.")

    except Exception as e:
        print(f" -> [ERROR] en la preparación de datos: {e}")
        return

    # ====================================================================
    # FASE 2: INGESTA EN BASE DE DATOS (CON TRANSACCIÓN EXPLÍCITA)
    # ====================================================================
    print(f"\n--- FASE 2: Guardando datos en la tabla '{table_name}' ---")
    try:
        with engine.connect() as connection:
            # Usamos una transacción para asegurar que todo se confirma a la vez
            with connection.begin() as transaction:
                print("  -> Vaciando la tabla (TRUNCATE)...")
                connection.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY;"))
                print(f"  -> Insertando {len(final_df)} nuevos registros...")
                final_df.to_sql(table_name, connection, if_exists='append', index=False)
                # La transacción se confirma (commit) automáticamente al salir de este bloque
            print(" -> ¡Éxito! Transacción completada.")
    except Exception as e:
        print(f" -> [ERROR] durante la transacción con la base de datos: {e}")
        return

    # ====================================================================
    # FASE 3: VERIFICACIÓN INMEDIATA
    # ====================================================================
    print(f"\n--- FASE 3: Verificando datos en la tabla '{table_name}' ---")
    try:
        verification_query = """
            SELECT
                ticker,
                COUNT(*) AS record_count,
                MIN(timestamp)::date AS first_record,
                MAX(timestamp)::date AS last_record
            FROM
                asset_metrics
            GROUP BY
                ticker
            ORDER BY
                ticker;
        """
        with engine.connect() as connection:
            verification_df = pd.read_sql_query(verification_query, connection)
        
        print("\n--- RESULTADO REAL EN LA BASE DE DATOS ---\n")
        print(verification_df.to_string())

    except Exception as e:
        print(f" -> [ERROR] durante la verificación: {e}")


if __name__ == "__main__":
    run_ingestion_and_verify()