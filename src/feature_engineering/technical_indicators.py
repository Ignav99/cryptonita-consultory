# src/feature_engineering/technical_indicators.py

import pandas as pd
import talib
from sqlalchemy import text
import sys, os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path: sys.path.insert(0, project_root)

from src.utils.db_connector import create_db_engine

def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula un conjunto de indicadores técnicos usando TA-Lib en un DataFrame de un solo ticker.
    """
    df_out = df.copy().set_index('timestamp')

    # Medias Móviles y MACD
    df_out['ema_12'] = talib.EMA(df_out['close'], timeperiod=12)
    df_out['ema_26'] = talib.EMA(df_out['close'], timeperiod=26)
    df_out['macd'], df_out['macd_signal'], df_out['macd_hist'] = talib.MACD(df_out['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    
    # RSI
    df_out['rsi_14'] = talib.RSI(df_out['close'], timeperiod=14)
    
    # Bandas de Bollinger
    df_out['bb_upper'], df_out['bb_middle'], df_out['bb_lower'] = talib.BBANDS(df_out['close'], timeperiod=20)
    
    # Indicadores de Volumen y Volatilidad
    df_out['obv'] = talib.OBV(df_out['close'], df_out['volume'].astype(float))
    df_out['atr_14'] = talib.ATR(df_out['high'], df_out['low'], df_out['close'], timeperiod=14)
    
    return df_out.reset_index()

def generate_technical_features():
    """
    Carga los datos de mercado, calcula indicadores técnicos para cada activo
    y los guarda en la tabla 'technical_indicators'.
    """
    table_name = 'technical_indicators'
    print(f"\n[FEATURE ENG]: Iniciando la generación de '{table_name}'...")
    
    engine = create_db_engine()
    if not engine: return

    try:
        sql_query = "SELECT * FROM asset_metrics ORDER BY ticker, timestamp;"
        market_data_df = pd.read_sql(sql_query, engine)

        if market_data_df.empty:
            print(f"  -> La tabla 'asset_metrics' está vacía. No se pueden generar indicadores.")
            return

        print(f"  -> Procesando {market_data_df['ticker'].nunique()} ticker(s)...")
        
        # Agrupamos por ticker y aplicamos la función de cálculo
        indicators_df = market_data_df.groupby('ticker', group_keys=False).apply(calculate_technical_indicators)
        
        indicators_df.dropna(inplace=True)

        feature_columns = [
            'ticker', 'timestamp', 'ema_12', 'ema_26', 'macd', 'macd_signal',
            'macd_hist', 'rsi_14', 'bb_upper', 'bb_middle', 'bb_lower', 'obv', 'atr_14'
        ]
        final_df = indicators_df[feature_columns]

        with engine.connect() as connection:
            with connection.begin() as transaction:
                print(f"  -> Vaciando y guardando {len(final_df)} registros en '{table_name}'...")
                connection.execute(text(f"TRUNCATE TABLE {table_name};"))
                final_df.to_sql(table_name, connection, if_exists='append', index=False, method='multi')

        print(f"[TAREA COMPLETADA]: Generación de '{table_name}' finalizada.")

    except Exception as e:
        print(f"[ERROR EN TAREA]: Falló la generación de indicadores técnicos. Error: {e}")

if __name__ == "__main__":
    generate_technical_features()