# src/celery_app.py
from celery import Celery
import os
import sys

# Agregar el directorio raíz al path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importar configuración
from src.config.settings import (
    CELERY_BROKER_URL,
    CELERY_RESULT_BACKEND,
    CELERY_TASK_SERIALIZER,
    CELERY_ACCEPT_CONTENT,
    CELERY_RESULT_SERIALIZER,
    CELERY_TIMEZONE,
    CELERY_ENABLE_UTC,
    CELERY_TASK_TIME_LIMIT,
    CELERY_WORKER_PREFETCH_MULTIPLIER,
    CELERY_TASK_ACKS_LATE
)

# Crear instancia de Celery
app = Celery('cryptonita_trading_bot')

# Configurar Celery
app.conf.update(
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND,
    task_serializer=CELERY_TASK_SERIALIZER,
    accept_content=CELERY_ACCEPT_CONTENT,
    result_serializer=CELERY_RESULT_SERIALIZER,
    timezone=CELERY_TIMEZONE,
    enable_utc=CELERY_ENABLE_UTC,
    task_track_started=True,
    task_time_limit=CELERY_TASK_TIME_LIMIT,
    worker_prefetch_multiplier=CELERY_WORKER_PREFETCH_MULTIPLIER,
    task_acks_late=CELERY_TASK_ACKS_LATE,
)

# Auto-descubrir tareas en el módulo pipeline
app.autodiscover_tasks(['src.pipeline'])

if __name__ == '__main__':
    app.start()