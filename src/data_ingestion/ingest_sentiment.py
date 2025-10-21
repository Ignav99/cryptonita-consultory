# src/data_ingestion/ingest_sentiment.py (VERSIÓN CON AGREGACIÓN DIARIA)

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
    
    print(f"\n--- [TAREA]: AGREGACIÓN DIARIA DE SENTIMIENTO PARA BTC ---")
    
    engine = create_db_engine()
    if not engine: return

    try:
        # --- PASO 1: LECTURA Y FILTRADO ---
        print(f"  [1/4] Leyendo y filtrando noticias de '{file_name}' para 'BTC'...")
        df = pd.read_csv(csv_path, usecols=['date', 'sentiment', 'tickers'])
        df_btc = df[df['tickers'].str.contains('BTC', case=False, na=False)].copy()
        
        if df_btc.empty:
            print("  -> ERROR: No se encontraron noticias de BTC.")
            return
            
        # --- PASO 2: TRANSFORMACIÓN A SCORE NUMÉRICO ---
        print(f"  [2/4] Transformando {len(df_btc)} noticias a score numérico...")
        sentiment_map = {'Positive': 3.0, 'Neutral': 2.0, 'Negative': 1.0}
        df_btc['sentiment_score'] = df_btc['sentiment'].map(sentiment_map)
        df_btc['timestamp'] = pd.to_datetime(df_btc['date'], utc=True, errors='coerce')
        df_btc.dropna(subset=['timestamp', 'sentiment_score'], inplace=True)
        
        # --- PASO 3: AGREGACIÓN POR DÍA (EL PASO CLAVE) ---
        print(f"  [3/4] Agregando scores de sentimiento por día...")
        daily_sentiment_df = df_btc.groupby(df_btc['timestamp'].dt.date)['sentiment_score'].mean().reset_index()
        daily_sentiment_df.rename(columns={'timestamp': 'date'}, inplace=True) # Renombrar para claridad
        daily_sentiment_df['timestamp'] = pd.to_datetime(daily_sentiment_df['date']) # Convertir de nuevo a datetime
        
        final_df = daily_sentiment_df[['timestamp', 'sentiment_score']]
        
        # --- PASO 4: INSERCIÓN Y VERIFICACIÓN ---
        with engine.connect() as connection:
            with connection.begin() as transaction:
                print(f"  [4/4] Guardando {len(final_df)} scores diarios en '{table_name}'...")
                connection.execute(text(f"TRUNCATE TABLE {table_name};"))
                final_df.to_sql(table_name, connection, if_exists='append', index=False, method='multi')
                
                count = connection.execute(text(f"SELECT COUNT(*) FROM {table_name};")).scalar_one()
                print(f"\n--- ¡TAREA COMPLETADA! ---")
                print(f"VERIFICACIÓN: La tabla '{table_name}' ahora contiene {count} registros diarios.")

    except Exception as e:
        print(f"\n--- [ERROR] LA TAREA FALLÓ --- \nRazón: {e}")

if __name__ == "__main__":
    run_sentiment_aggregation()