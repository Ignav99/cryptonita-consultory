# src/utils/db_cleanup.py

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

def cleanup_database():
    """
    Vacía las tablas que ya no son necesarias para la estrategia de producción.
    """
    # --- LISTA DE TABLAS A LIMPIAR ---
    # Estas tablas contienen datos que no se usan en las 15 características finales.
    tables_to_truncate = [
        'sentiment_metrics',
        'candle_patterns',
        'technical_indicators'
    ]

    logging.info("--- [INICIO] Proceso de limpieza de la base de datos. ---")
    engine = create_db_engine()
    if not engine:
        logging.error("No se pudo conectar a la base de datos. Abortando.")
        return

    try:
        with engine.connect() as connection:
            with connection.begin() as transaction:
                for table in tables_to_truncate:
                    logging.info(f" -> Vaciando la tabla '{table}'...")
                    # TRUNCATE es más rápido que DELETE y resetea los contadores.
                    # CASCADE elimina registros en tablas dependientes si existen.
                    connection.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))
                    logging.info(f"    ✅ Tabla '{table}' vaciada con éxito.")
                # La transacción se confirma (commit) al salir.
        logging.info("\n🎉 Proceso de limpieza de la base de datos completado con éxito.")
    except Exception as e:
        logging.error(f"❌ Ocurrió un error durante la limpieza: {e}")

if __name__ == "__main__":
    # --- ADVERTENCIA ---
    print("⚠️ ADVERTENCIA: Estás a punto de borrar TODOS los datos de las siguientes tablas:")
    print("   - sentiment_metrics")
    print("   - candle_patterns")
    print("   - technical_indicators")
    print("Esta acción es IRREVERSIBLE.")
    
    confirm = input("Escribe 'CONFIRMAR' para continuar: ")
    if confirm == "CONFIRMAR":
        cleanup_database()
    else:
        print("Limpieza cancelada por el usuario.")