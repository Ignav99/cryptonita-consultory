# src/utils/create_trade_log_table.py

from sqlalchemy import text
import sys
import os
import logging

# --- Configuración ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.db_connector import create_db_engine

def create_table():
    """
    Crea la tabla 'trade_log' en la base de datos si no existe.
    """
    table_name = 'trade_log'
    # Definimos la estructura de la tabla
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMPTZ NOT NULL,
        ticker VARCHAR(20) NOT NULL,
        action VARCHAR(10) NOT NULL, -- 'BUY' o 'SELL'
        price FLOAT,
        size FLOAT,
        order_id VARCHAR(50) UNIQUE,
        status VARCHAR(20)
    );
    """
    
    logging.info(f"--- Intentando crear la tabla '{table_name}'... ---")
    engine = create_db_engine()
    if not engine:
        logging.error("No se pudo conectar a la base de datos. Abortando.")
        return

    try:
        with engine.connect() as connection:
            with connection.begin() as transaction:
                connection.execute(text(create_table_query))
        logging.info(f"✅ Tabla '{table_name}' verificada/creada con éxito.")
    except Exception as e:
        logging.error(f"❌ Ocurrió un error al crear la tabla: {e}")

if __name__ == "__main__":
    create_table()