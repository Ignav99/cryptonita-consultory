# src/utils/db_connector.py

import os
from sqlalchemy import create_engine
import sys

# --- Bloque de importación ---
# Agrega el directorio raíz del proyecto al sys.path
# Esto nos permite importar módulos desde cualquier parte del proyecto
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- Fin del bloque de importación ---

from src.config import settings

def create_db_engine():
    """
    Crea y retorna un motor de conexión de SQLAlchemy para PostgreSQL
    usando las credenciales del archivo de configuración.
    """
    try:
        # Construimos la URL de conexión
        db_url = (
            f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}@"
            f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )
        engine = create_engine(db_url)
        # Probamos la conexión
        engine.connect()
        print("Conexión a la base de datos establecida exitosamente.")
        return engine
    except Exception as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None

if __name__ == '__main__':
    # Pequeña prueba para verificar que el conector funciona
    engine = create_db_engine()
    if engine:
        print("El motor de base de datos se ha creado correctamente.")