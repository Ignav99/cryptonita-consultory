# src/data_ingestion/ingest_sentiment.py (VERSIÓN FINAL Y CORREGIDA)

import pandas as pd
from sqlalchemy import text
import sys, os

# --- Bloque de importación ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.db_connector import create_db_engine
from src.config import settings

def run_sentiment_aggregation():
    table_name = 'sentiment_metrics'
    file_name = 'crypto_news_api.csv'
    csv_path = os.path.join(project_root, 'data', 'raw', file_name)
    
    print(f"\n--- [TAREA]: AGREGACIÓN DIARIA DE SENTIMIENTO PARA TODOS LOS ACTIVOS ---")
    
    engine = create_db_engine()
    if not engine: return

    try:
        # --- Lectura y Preparación ---
        df = pd.read_csv(csv_path, usecols=['date', 'sentiment', 'tickers'])
        sentiment_map = {'Positive': 3.0, 'Neutral': 2.0, 'Negative': 1.0}
        df['sentiment_score'] = df['sentiment'].map(sentiment_map)
        df['timestamp'] = pd.to_datetime(df['date'], utc=True, errors='coerce')
        df.dropna(subset=['timestamp', 'sentiment_score', 'tickers'], inplace=True)
        
        # --- Limpieza y "Explosión" de Tickers ---
        df['tickers'] = df['tickers'].astype(str).str.replace(r"\[|\]|'", "", regex=True).str.split(',')
        df_exploded = df.explode('tickers')
        df_exploded['tickers'] = df_exploded['tickers'].str.strip()

        # --- Filtrado por Universo de Activos ---
        asset_base_tickers = [t.replace('-USD', '') for t in settings.ASSET_TICKERS]
        df_filtered = df_exploded[df_exploded['tickers'].isin(asset_base_tickers)]

        # --- Agregación por Día y Ticker ---
        daily_sentiment_df = df_filtered.groupby([df_filtered['timestamp'].dt.date, 'tickers'])['sentiment_score'].mean().reset_index()
        
        # --- Preparación del DataFrame Final ---
        # Renombramos 'tickers' a 'ticker_base' para evitar confusión
        daily_sentiment_df.rename(columns={'tickers': 'ticker_base'}, inplace=True)
        # Reconstruimos el ticker con '-USD' y ajustamos el timestamp
        daily_sentiment_df['ticker'] = daily_sentiment_df['ticker_base'] + '-USD'
        daily_sentiment_df['timestamp'] = pd.to_datetime(daily_sentiment_df['timestamp']) # La columna ya se llama timestamp
        
        final_df = daily_sentiment_df[['ticker', 'timestamp', 'sentiment_score']]
        
        # --- Inserción en la Base de Datos ---
        with engine.connect() as connection:
            with connection.begin() as transaction:
                print(f"  -> Guardando {len(final_df)} scores diarios en '{table_name}'...")
                connection.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY;"))
                final_df.to_sql(table_name, connection, if_exists='append', index=False)
                
                count = connection.execute(text(f"SELECT COUNT(*) FROM {table_name};")).scalar_one()
                print(f"\n--- ¡TAREA COMPLETADA! ---")
                print(f"VERIFICACIÓN: La tabla '{table_name}' ahora contiene {count} registros.")

    except Exception as e:
        print(f"\n--- [ERROR] LA TAREA FALLÓ --- \nRazón: {e}")

if __name__ == "__main__":
    run_sentiment_aggregation()