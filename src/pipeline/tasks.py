# src/pipeline/tasks.py
from celery import current_task
from celery.utils.log import get_task_logger
from celery import group, chord, chain
import sys
import os
import importlib.util

# Agregar path del proyecto
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importar la aplicación Celery
from src.celery_app import app

# Configurar logger
logger = get_task_logger(__name__)

# =============================================
# FUNCIONES AUXILIARES PARA IMPORTAR MÓDULOS CON NÚMEROS
# =============================================

def import_production_module(filename, function_name):
    """Importa dinámicamente módulos de producción que empiezan con números"""
    module_path = os.path.join(project_root, 'src', 'production', filename)
    spec = importlib.util.spec_from_file_location(filename.replace('.py', ''), module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, function_name)

# =============================================
# TAREAS INDIVIDUALES (Conversión de tus scripts)
# =============================================

@app.task(bind=True, max_retries=3, default_retry_delay=60)
def ingest_data_task(self):
    """Convierte tu script 01_ingest_daily_data.py en tarea Celery"""
    try:
        logger.info("🔄 Iniciando ingesta de datos...")
        
        # Importar dinámicamente el módulo con número
        run_daily_ingestion = import_production_module('01_ingest_daily_data.py', 'run_daily_ingestion')
        
        # Ejecutar la función principal
        run_daily_ingestion()
        
        logger.info("✅ Ingesta de datos completada")
        return {"status": "success", "task": "ingest_data", "result": "completed"}
        
    except Exception as exc:
        logger.error(f"❌ Error en ingesta de datos: {exc}")
        if self.request.retries < 3:
            logger.info(f"🔄 Reintentando ingesta... ({self.request.retries + 1}/3)")
            raise self.retry(exc=exc, countdown=60)
        else:
            logger.error("💀 Ingesta falló después de 3 intentos")
            raise

@app.task(bind=True, max_retries=3, default_retry_delay=60)
def prepare_features_task(self, previous_result=None):
    """Convierte tu script 02_prepare_features.py en tarea Celery"""
    try:
        logger.info("🔄 Iniciando preparación de características...")
        
        # Importar dinámicamente el módulo con número
        run_feature_preparation = import_production_module('02_prepare_features.py', 'run_feature_preparation')
        
        # Tu función no retorna nada, pero eso está bien
        run_feature_preparation()
        
        logger.info("✅ Preparación de características completada")
        return {"status": "success", "task": "prepare_features", "result": "completed"}
        
    except Exception as exc:
        logger.error(f"❌ Error en preparación de características: {exc}")
        if self.request.retries < 3:
            logger.info(f"🔄 Reintentando preparación... ({self.request.retries + 1}/3)")
            raise self.retry(exc=exc, countdown=60)
        else:
            logger.error("💀 Preparación falló después de 3 intentos")
            raise

@app.task(bind=True, max_retries=3, default_retry_delay=60)  
def generate_signals_task(self, previous_result=None):
    """Convierte tu script 03_generate_signals.py en tarea Celery"""
    try:
        logger.info("🔄 Iniciando generación de señales...")
        
        # Importar dinámicamente el módulo con número
        run_inference = import_production_module('03_generate_signals.py', 'run_inference')
        
        # Tu función no retorna nada, pero genera signals.json
        run_inference()
        
        logger.info("✅ Generación de señales completada")
        return {"status": "success", "task": "generate_signals", "result": "completed"}
        
    except Exception as exc:
        logger.error(f"❌ Error en generación de señales: {exc}")
        if self.request.retries < 3:
            logger.info(f"🔄 Reintentando generación... ({self.request.retries + 1}/3)")
            raise self.retry(exc=exc, countdown=60)
        else:
            logger.error("💀 Generación de señales falló después de 3 intentos")
            raise

@app.task(bind=True, max_retries=2, default_retry_delay=30)
def execute_trades_task(self, previous_result=None):
    """Convierte tu script 04_execution_engine.py en tarea Celery"""
    try:
        logger.info("🔄 Iniciando ejecución de trades...")
        
        # Importar dinámicamente el módulo con número
        run_execution_engine = import_production_module('04_execution_engine.py', 'run_execution_engine')
        
        # Tu función no retorna nada, pero ejecuta las órdenes
        run_execution_engine()
        
        logger.info("✅ Ejecución de trades completada")
        return {"status": "success", "task": "execute_trades", "result": "completed"}
        
    except Exception as exc:
        logger.error(f"❌ Error en ejecución de trades: {exc}")
        if self.request.retries < 2:
            logger.info(f"🔄 Reintentando ejecución... ({self.request.retries + 1}/2)")
            raise self.retry(exc=exc, countdown=30)
        else:
            logger.error("💀 Ejecución de trades falló después de 2 intentos")
            raise

# =============================================
# PIPELINES COMPLEJOS (Workflows)
# =============================================

@app.task
def health_check_task():
    """Tarea de verificación de salud del sistema"""
    try:
        logger.info("🏥 Ejecutando health check del sistema...")
        
        from src.pipeline.monitoring import CryptonitaPipelineMonitor
        monitor = CryptonitaPipelineMonitor()
        
        health_status = monitor.health_check()
        signals_status = monitor.check_signals_file()
        
        logger.info(f"📊 Estado del sistema: {health_status['status']}")
        logger.info(f"📋 Estado de señales: {signals_status['status']}")
        
        return {
            "status": "success",
            "task": "health_check", 
            "system_health": health_status,
            "signals_health": signals_status
        }
        
    except Exception as exc:
        logger.error(f"❌ Error en health check: {exc}")
        return {"status": "error", "task": "health_check", "error": str(exc)}

@app.task
def pipeline_complete_callback(results):
    """Se ejecuta cuando termina todo el pipeline"""
    logger.info(f"🎉 Pipeline completado: {len(results)} tareas")
    
    # Analizar resultados
    successful = sum(1 for r in results if r and r.get('status') == 'success')
    logger.info(f"📊 Exitosas: {successful}/{len(results)}")
    
    return {
        "pipeline_status": "completed", 
        "success_count": successful,
        "total_tasks": len(results),
        "timestamp": str(current_task.request.id)
    }

@app.task
def run_complete_pipeline():
    """Ejecuta el pipeline completo secuencial"""
    logger.info("🚀 Iniciando pipeline completo de trading")
    
    # Crear cadena secuencial: ingest -> features -> signals -> execute
    workflow = chain(
        ingest_data_task.s(),
        prepare_features_task.s(),
        generate_signals_task.s(),
        execute_trades_task.s()
    )
    
    # Ejecutar workflow y agregar callback
    job = chord([workflow])(pipeline_complete_callback.s())
    
    logger.info(f"Pipeline iniciado con job_id: {job.id}")
    return f"Pipeline iniciado con job_id: {job.id}"