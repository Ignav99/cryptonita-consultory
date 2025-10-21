# src/data_ingestion/ingest_onchain.py
import requests
import pandas as pd
from src.utils.db_connector import create_db_engine
from src.config import settings

def ingest_onchain_data():
    engine = create_db_engine()
    df = pd.DataFrame(requests.get("https://api.blockchain.info/charts/n-unique-addresses?timespan=all&format=json").json()['values'])
    df['timestamp'] = pd.to_datetime(df['x'], unit='s')
    df.rename(columns={'y': 'unique_addresses'}, inplace=True)
    df['ticker'] = "BTC-USD"
    
    start, end = pd.to_datetime(settings.HISTORIC_START_DATE), pd.to_datetime(settings.HISTORIC_END_DATE)
    final_df = df[(df['timestamp'] >= start) & (df['timestamp'] <= end)][['ticker', 'timestamp', 'unique_addresses']]
    
    final_df.to_sql('onchain_metrics', engine, if_exists='append', index=False, method='multi')
    print(f"\n[INGESTA]: ¡Éxito! Se insertaron {len(final_df)} registros en 'onchain_metrics'.")