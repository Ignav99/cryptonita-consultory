# src/pipeline/scheduler.py
from celery.schedules import crontab
import os
import sys

# Agregar path del proyecto
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importar la aplicación Celery
from src.celery_app import app

# =============================================
# CONFIGURACIÓN DE HORARIOS AUTOMÁTICOS FINALES
# =============================================

# Configurar Beat Schedule (tareas programadas)
app.conf.beat_schedule = {
    
    # 🎯 PIPELINE PRINCIPAL - CADA DÍA A LAS 8:00 AM UTC
    # ✅ Timing optimal basado en análisis de mercados
    # ✅ Datos crypto consolidados + funding rates + macros disponibles
    'cryptonita-trading-diario': {
        'task': 'src.pipeline.tasks.run_complete_pipeline',
        'schedule': crontab(hour=8, minute=0),  # 8:00 AM UTC todos los días
        'options': {
            'expires': 2 * 60 * 60,  # Expira en 2 horas si no se ejecuta
        }
    },
    
    # 📊 ACTUALIZACIÓN DE DATOS - CADA 6 HORAS
    # Solo datos, no trading (mantener DB fresca)
    'actualizacion-datos-6h': {
        'task': 'src.pipeline.tasks.ingest_data_task',
        'schedule': crontab(minute=0, hour='2,8,14,20'),  # 02:00, 08:00, 14:00, 20:00 UTC
        'options': {
            'expires': 5 * 60 * 60,  # Expira en 5 horas
        }
    },
    
    # 🛡️ PIPELINE DE BACKUP - SOLO SI EL PRINCIPAL FALLA
    # 2:00 AM UTC (hora tranquila, sin mercados importantes)
    'cryptonita-backup-nocturno': {
        'task': 'src.pipeline.tasks.run_complete_pipeline',
        'schedule': crontab(hour=2, minute=0),  # 2:00 AM UTC como backup
        'options': {
            'expires': 1 * 60 * 60,  # Expira en 1 hora
        }
    },
    
    # 🏥 HEALTH CHECK - CADA 4 HORAS
    # Verificar que todo esté funcionando
    'health-check-4h': {
        'task': 'src.pipeline.tasks.health_check_task',
        'schedule': crontab(minute=30, hour='*/4'),  # Cada 4 horas a los 30 minutos
        'options': {
            'expires': 30 * 60,  # Expira en 30 minutos
        }
    }
}

# Configurar timezone
app.conf.timezone = 'UTC'

# =============================================
# FUNCIONES AUXILIARES PARA MANEJO MANUAL
# =============================================

def start_manual_pipeline():
    """Inicia el pipeline manualmente"""
    from src.pipeline.tasks import run_complete_pipeline
    result = run_complete_pipeline.delay()
    return result

def start_manual_ingestion():
    """Inicia solo la ingesta de datos manualmente"""
    from src.pipeline.tasks import ingest_data_task
    result = ingest_data_task.delay()
    return result

def get_scheduled_tasks():
    """Devuelve información sobre las tareas programadas"""
    schedule_info = {}
    for name, task_info in app.conf.beat_schedule.items():
        schedule_info[name] = {
            'task': task_info['task'],
            'schedule': str(task_info['schedule']),
            'next_run': 'Calculado por Celery Beat'
        }
    return schedule_info

# =============================================
# CONFIGURACIONES ADICIONALES DE RENDIMIENTO
# =============================================

# Evitar que tareas se acumulen si el worker está ocupado
app.conf.task_reject_on_worker_lost = True

# Configurar rutas para diferentes tipos de tareas
app.conf.task_routes = {
    'src.pipeline.tasks.ingest_data_task': {'queue': 'data_ingestion'},
    'src.pipeline.tasks.prepare_features_task': {'queue': 'data_processing'},
    'src.pipeline.tasks.generate_signals_task': {'queue': 'model_inference'},
    'src.pipeline.tasks.execute_trades_task': {'queue': 'trading'},
    'src.pipeline.tasks.run_complete_pipeline': {'queue': 'main_pipeline'},
}

if __name__ == '__main__':
    # Mostrar información de las tareas programadas
    print("📅 Tareas Programadas Configuradas:")
    print("=" * 50)
    for name, info in get_scheduled_tasks().items():
        print(f"• {name}:")
        print(f"  - Tarea: {info['task']}")
        print(f"  - Horario: {info['schedule']}")
        print(f"  - Próxima ejecución: {info['next_run']}")
        print()