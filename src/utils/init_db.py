# src/utils/init_db.py
from sqlalchemy import text
from src.utils.db_connector import create_db_engine # Asumiendo que db_connector.py está en el mismo directorio

def initialize_database():
    engine = create_db_engine()
    if not engine: return
    
    tables_sql = {
        "asset_metrics": "CREATE TABLE asset_metrics (ticker TEXT, timestamp TIMESTAMPTZ, open NUMERIC, high NUMERIC, low NUMERIC, close NUMERIC, volume BIGINT, PRIMARY KEY (ticker, timestamp));",
        "macro_metrics": "CREATE TABLE macro_metrics (ticker TEXT, timestamp TIMESTAMPTZ, open NUMERIC, high NUMERIC, low NUMERIC, close NUMERIC, volume BIGINT, PRIMARY KEY (ticker, timestamp));",
        "onchain_metrics": "CREATE TABLE onchain_metrics (ticker TEXT, timestamp TIMESTAMPTZ, unique_addresses BIGINT, PRIMARY KEY (ticker, timestamp));",
        "technical_indicators": "CREATE TABLE technical_indicators (ticker TEXT, timestamp TIMESTAMPTZ, ema_12 NUMERIC, ema_26 NUMERIC, macd NUMERIC, macd_signal NUMERIC, macd_hist NUMERIC, rsi_14 NUMERIC, bb_upper NUMERIC, bb_middle NUMERIC, bb_lower NUMERIC, obv BIGINT, atr_14 NUMERIC, PRIMARY KEY (ticker, timestamp));",
        "candle_patterns": "CREATE TABLE candle_patterns (ticker TEXT, timestamp TIMESTAMPTZ, pattern_score INTEGER, pattern_name TEXT, PRIMARY KEY (ticker, timestamp));"
    }
    
    try:
        with engine.connect() as connection:
            with connection.begin() as transaction:
                for name, sql in tables_sql.items():
                    connection.execute(text(f"DROP TABLE IF EXISTS {name};"))
                    connection.execute(text(sql))
        print("Base de datos inicializada y tablas creadas desde cero.")
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")

if __name__ == "__main__":
    initialize_database()