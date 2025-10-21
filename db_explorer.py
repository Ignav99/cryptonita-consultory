#!/usr/bin/env python3
"""
🔍 EXPLORADOR DE BASE DE DATOS CRYPTONITA (CORREGIDO)
Analiza estructura de tablas y datos para corregir el GraphBuilder

Objetivo: Entender exactamente qué columnas tenemos disponibles
CORREGIDO: Manejo de compatibilidad SQLAlchemy
"""

import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
import warnings
warnings.filterwarnings('ignore')

def safe_query(engine, query, query_name="Query"):
    """Ejecuta query de forma segura con manejo de errores"""
    try:
        # Usar text() para queries SQL raw
        with engine.connect() as conn:
            result = conn.execute(text(query))
            # Convertir a DataFrame manualmente
            columns = result.keys()
            data = result.fetchall()
            df = pd.DataFrame(data, columns=columns)
        return df
    except Exception as e:
        print(f"❌ Error en {query_name}: {e}")
        return pd.DataFrame()

def main():
    print("🔍 EXPLORADOR DE BASE DE DATOS CRYPTONITA (CORREGIDO)")
    print("=" * 55)
    
    # Configuración DB
    db_config = {
        'user': 'cryptonita_user',
        'password': 'TIZavoltio999',
        'host': 'localhost',
        'port': '5432',
        'database': 'cryptonita_db2'
    }
    
    try:
        # Conectar con configuración mejorada
        connection_string = (
            f"postgresql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
        
        # Engine con configuración explícita
        engine = create_engine(
            connection_string,
            pool_pre_ping=True,
            pool_recycle=300
        )
        
        # Test de conexión
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        print("✅ Conectado a la base de datos\n")
        
        # 1. EXPLORAR TABLA gnn_technical_features
        print("🔍 TABLA: gnn_technical_features")
        print("-" * 30)
        
        # Verificar si la tabla existe primero
        table_exists_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'gnn_technical_features'
        """
        
        table_exists = safe_query(engine, table_exists_query, "Check table exists")
        
        if not table_exists.empty:
            # Estructura de la tabla
            columns_query = """
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'gnn_technical_features'
            ORDER BY ordinal_position
            """
            
            columns_df = safe_query(engine, columns_query, "Columns info")
            
            if not columns_df.empty:
                print("📋 COLUMNAS DISPONIBLES:")
                for _, row in columns_df.iterrows():
                    print(f"   {row['column_name']} ({row['data_type']}) - Nullable: {row['is_nullable']}")
                
                # Muestra de datos
                sample_query = "SELECT * FROM gnn_technical_features LIMIT 3"
                sample_df = safe_query(engine, sample_query, "Sample data")
                
                if not sample_df.empty:
                    print(f"\n📊 MUESTRA DE DATOS:")
                    print(sample_df.head().to_string())
                
                # Verificar tickers disponibles
                tickers_query = "SELECT DISTINCT ticker FROM gnn_technical_features ORDER BY ticker"
                tickers_df = safe_query(engine, tickers_query, "Tickers")
                
                if not tickers_df.empty:
                    print(f"\n🎯 TICKERS DISPONIBLES ({len(tickers_df)}):")
                    tickers_list = tickers_df['ticker'].tolist()
                    print(tickers_list)
                
                # Contar registros totales
                count_query = "SELECT COUNT(*) as total FROM gnn_technical_features"
                count_df = safe_query(engine, count_query, "Count records")
                if not count_df.empty:
                    print(f"\n📊 TOTAL REGISTROS: {count_df['total'].iloc[0]:,}")
            else:
                print("❌ No se pudieron obtener las columnas")
        else:
            print("❌ Tabla 'gnn_technical_features' NO EXISTE")
        
        # 2. EXPLORAR TABLA gnn_correlations
        print("\n" + "="*55)
        print("🔍 TABLA: gnn_correlations")
        print("-" * 30)
        
        # Verificar si existe
        check_corr_query = """
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'gnn_correlations'
        """
        
        corr_exists = safe_query(engine, check_corr_query, "Check correlations table")
        
        if not corr_exists.empty:
            # Estructura
            corr_columns_query = """
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'gnn_correlations'
            ORDER BY ordinal_position
            """
            
            corr_columns_df = safe_query(engine, corr_columns_query, "Correlations columns")
            
            if not corr_columns_df.empty:
                print("📋 COLUMNAS DISPONIBLES:")
                for _, row in corr_columns_df.iterrows():
                    print(f"   {row['column_name']} ({row['data_type']}) - Nullable: {row['is_nullable']}")
                
                # Muestra de datos
                corr_sample_query = "SELECT * FROM gnn_correlations LIMIT 3"
                corr_sample_df = safe_query(engine, corr_sample_query, "Correlations sample")
                
                if not corr_sample_df.empty:
                    print(f"\n📊 MUESTRA DE DATOS:")
                    print(corr_sample_df.to_string())
                
                # Contar registros
                count_query = "SELECT COUNT(*) as total FROM gnn_correlations"
                count_result = safe_query(engine, count_query, "Count correlations")
                if not count_result.empty:
                    print(f"\n📊 TOTAL REGISTROS: {count_result['total'].iloc[0]:,}")
        else:
            print("❌ Tabla 'gnn_correlations' NO EXISTE")
        
        # 3. LISTAR TODAS LAS TABLAS (MÉTODO ALTERNATIVO)
        print("\n" + "="*55)
        print("🔍 TODAS LAS TABLAS EN LA BASE DE DATOS")
        print("-" * 30)
        
        # Método alternativo usando psycopg2 directamente
        try:
            import psycopg2
            
            conn_params = {
                'host': db_config['host'],
                'port': db_config['port'],
                'database': db_config['database'],
                'user': db_config['user'],
                'password': db_config['password']
            }
            
            with psycopg2.connect(**conn_params) as conn:
                with conn.cursor() as cur:
                    # Obtener todas las tablas
                    cur.execute("""
                        SELECT schemaname, tablename 
                        FROM pg_tables 
                        WHERE schemaname = 'public'
                        ORDER BY tablename
                    """)
                    
                    tables = cur.fetchall()
                    
                    print("📋 TODAS LAS TABLAS DISPONIBLES:")
                    gnn_tables = []
                    other_tables = []
                    
                    for schema, table in tables:
                        if table.startswith('gnn_'):
                            gnn_tables.append(table)
                        else:
                            other_tables.append(table)
                    
                    print(f"\n🧠 TABLAS GNN ({len(gnn_tables)}):")
                    for table in gnn_tables:
                        # Contar registros
                        try:
                            cur.execute(f"SELECT COUNT(*) FROM {table}")
                            count = cur.fetchone()[0]
                            print(f"   {table}: {count:,} registros")
                        except Exception as e:
                            print(f"   {table}: Error contando - {e}")
                    
                    print(f"\n📊 OTRAS TABLAS ({len(other_tables)}):")
                    for table in other_tables[:10]:  # Solo primeras 10
                        try:
                            cur.execute(f"SELECT COUNT(*) FROM {table}")
                            count = cur.fetchone()[0]
                            print(f"   {table}: {count:,} registros")
                        except Exception as e:
                            print(f"   {table}: Error contando")
                    
                    if len(other_tables) > 10:
                        print(f"   ... y {len(other_tables) - 10} tablas más")
                        
        except ImportError:
            print("⚠️ psycopg2 no disponible, usando método SQLAlchemy alternativo")
            
            # Método alternativo con SQLAlchemy
            all_tables_query = """
            SELECT schemaname, tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
            """
            
            tables_df = safe_query(engine, all_tables_query, "All tables")
            
            if not tables_df.empty:
                print("📋 TABLAS ENCONTRADAS:")
                for _, row in tables_df.iterrows():
                    print(f"   {row['tablename']}")
        
        # 4. ANÁLISIS ESPECÍFICO PARA GRAPHBUILDER
        print("\n" + "="*55)
        print("🔍 ANÁLISIS ESPECÍFICO PARA GRAPHBUILDER")
        print("-" * 30)
        
        # Verificar las tablas que necesita el GraphBuilder
        required_tables = ['gnn_technical_features', 'gnn_correlations']
        
        for table_name in required_tables:
            print(f"\n🔍 Analizando {table_name}:")
            
            # Verificar existencia
            check_query = f"""
            SELECT COUNT(*) as exists 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = '{table_name}'
            """
            
            exists_df = safe_query(engine, check_query, f"Check {table_name}")
            
            if not exists_df.empty and exists_df['exists'].iloc[0] > 0:
                print(f"   ✅ Tabla existe")
                
                # Obtener columnas
                cols_query = f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
                """
                
                cols_df = safe_query(engine, cols_query, f"Columns {table_name}")
                
                if not cols_df.empty:
                    print("   📋 Columnas:")
                    for _, row in cols_df.iterrows():
                        print(f"      - {row['column_name']} ({row['data_type']})")
                
                # Verificar si tiene datos
                count_query = f"SELECT COUNT(*) as total FROM {table_name}"
                count_df = safe_query(engine, count_query, f"Count {table_name}")
                
                if not count_df.empty:
                    total = count_df['total'].iloc[0]
                    print(f"   📊 Registros: {total:,}")
                    
                    if total > 0:
                        # Muestra pequeña
                        sample_query = f"SELECT * FROM {table_name} LIMIT 2"
                        sample_df = safe_query(engine, sample_query, f"Sample {table_name}")
                        
                        if not sample_df.empty:
                            print("   📄 Muestra:")
                            print(sample_df.to_string().replace('\n', '\n      '))
            else:
                print(f"   ❌ Tabla NO existe")
        
        print("\n" + "="*55)
        print("✅ EXPLORACIÓN COMPLETADA")
        print("💡 RECOMENDACIONES:")
        print("   1. Verifica que las tablas gnn_* existan")
        print("   2. Si no existen, ejecuta el setup de schema primero")
        print("   3. Usa las columnas exactas mostradas arriba en tu código")
        print("   4. Considera los tipos de datos para conversiones")
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        print("\n🔍 Traceback completo:")
        traceback.print_exc()

if __name__ == "__main__":
    main()