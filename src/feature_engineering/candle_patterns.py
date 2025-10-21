# src/feature_engineering/candle_patterns.py (VERSIÓN CON FILTRADO)

import pandas as pd
import talib
from sqlalchemy import text
import sys, os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path: sys.path.insert(0, project_root)

from src.utils.db_connector import create_db_engine

def recognize_candle_patterns(df: pd.DataFrame) -> pd.DataFrame:
    # (Esta función auxiliar no cambia)
    df_out = df.copy()
    pattern_functions = talib.get_function_groups()['Pattern Recognition']
    for pattern in pattern_functions:
        try:
            result = getattr(talib, pattern)(df_out['open'], df_out['high'], df_out['low'], df_out['close'])
            if result.abs().sum() > 0:
                df_out[pattern.lower()] = result
        except Exception:
            continue
    return df_out

def generate_pattern_feature():
    table_name = 'candle_patterns'
    print(f"\n[FEATURE ENG]: Iniciando la generación de '{table_name}'...")
    engine = create_db_engine()
    if not engine: return

    try:
        sql_query = "SELECT * FROM asset_metrics ORDER BY ticker, timestamp"
        df = pd.read_sql(sql_query, engine)
        if df.empty:
            print("  -> La tabla 'asset_metrics' está vacía.")
            return

        patterns_df = df.groupby('ticker', group_keys=False).apply(recognize_candle_patterns)
        pattern_cols = [col for col in patterns_df.columns if col.startswith('cdl')]
        
        patterns_df['pattern_score'] = patterns_df[pattern_cols].sum(axis=1)
        
        def get_pattern_name(row):
            for col in pattern_cols:
                if row[col] != 0: return col
            return "No Pattern"
            
        patterns_df['pattern_name'] = patterns_df.apply(get_pattern_name, axis=1)

        # --- INICIO DEL BLOQUE DE FILTRADO ---
        print("  -> Filtrando para quedarnos con los 20 patrones más frecuentes...")
        patterns_with_score = patterns_df[patterns_df['pattern_score'] != 0].copy()
        pattern_counts = patterns_with_score['pattern_name'].value_counts()
        top_20_patterns = pattern_counts.nlargest(20).index
        final_df = patterns_with_score[patterns_with_score['pattern_name'].isin(top_20_patterns)]
        final_df = final_df[['ticker', 'timestamp', 'pattern_score', 'pattern_name']]
        # --- FIN DEL BLOQUE DE FILTRADO ---
        
        if final_df.empty:
            print("  -> No se encontraron patrones significativos tras el filtrado.")
            return

        with engine.connect() as connection:
            with connection.begin() as transaction:
                print(f"  -> Vaciando y guardando {len(final_df)} registros de patrones relevantes en '{table_name}'...")
                connection.execute(text(f"TRUNCATE TABLE {table_name};"))
                final_df.to_sql(table_name, connection, if_exists='append', index=False, method='multi')

        print(f"[TAREA COMPLETADA]: Generación de '{table_name}' finalizada.")

    except Exception as e:
        print(f"[ERROR EN TAREA]: Falló la generación de patrones de velas. Error: {e}")

if __name__ == "__main__":
    generate_pattern_feature()