# src/pipeline/monitoring.py
import redis
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any

# Agregar path del proyecto
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config.settings import REDIS_URL

class CryptonitaPipelineMonitor:
    """Monitor del pipeline de trading de Cryptonita"""
    
    def __init__(self):
        self.redis_client = redis.Redis.from_url(REDIS_URL)
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del pipeline de las últimas 24 horas"""
        try:
            # Esto se conectaría con Flower API en producción
            # Por ahora retornamos stats básicas
            return {
                "last_execution": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "total_tasks_24h": "N/A",
                "successful_tasks": "N/A", 
                "failed_tasks": "N/A",
                "active_workers": "N/A"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica que todos los componentes estén funcionando"""
        status = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "redis": "unknown",
            "workers": 0,
            "database": "unknown",
            "model_files": "unknown",
            "status": "unknown"
        }
        
        try:
            # Test Redis
            self.redis_client.ping()
            status["redis"] = "healthy"
            
            # Test Celery workers
            from src.celery_app import app
            inspect = app.control.inspect()
            active_nodes = inspect.active()
            status["workers"] = len(active_nodes) if active_nodes else 0
            
            # Test archivos críticos
            model_path = os.path.join(project_root, 'models', 'ULTRA_MODEL_PACKAGE.joblib')
            if os.path.exists(model_path):
                status["model_files"] = "healthy"
            else:
                status["model_files"] = "missing"
            
            # Test base de datos (básico)
            try:
                from src.utils.db_connector import create_db_engine
                engine = create_db_engine()
                if engine:
                    status["database"] = "healthy"
                else:
                    status["database"] = "connection_failed"
            except Exception:
                status["database"] = "error"
            
            # Estado general
            if (status["redis"] == "healthy" and 
                status["workers"] > 0 and 
                status["model_files"] == "healthy" and 
                status["database"] == "healthy"):
                status["status"] = "healthy"
            else:
                status["status"] = "degraded"
                
        except Exception as e:
            status["status"] = "unhealthy"
            status["error"] = str(e)
        
        return status
    
    def check_signals_file(self) -> Dict[str, Any]:
        """Verifica el archivo de señales más reciente"""
        signals_path = os.path.join(project_root, 'signals.json')
        
        if not os.path.exists(signals_path):
            return {"status": "missing", "message": "signals.json no encontrado"}
        
        try:
            # Leer última modificación
            mtime = os.path.getmtime(signals_path)
            last_modified = datetime.fromtimestamp(mtime)
            hours_ago = (datetime.now() - last_modified).total_seconds() / 3600
            
            # Leer contenido
            with open(signals_path, 'r') as f:
                signals = json.load(f)
            
            # Contar señales
            buy_count = sum(1 for signal in signals.values() if signal == "BUY")
            sell_count = sum(1 for signal in signals.values() if signal == "SELL") 
            hold_count = sum(1 for signal in signals.values() if signal == "HOLD")
            
            return {
                "status": "healthy" if hours_ago < 25 else "stale",  # Debe ser < 25h para ser fresco
                "last_modified": last_modified.strftime("%Y-%m-%d %H:%M:%S"),
                "hours_ago": round(hours_ago, 1),
                "total_tickers": len(signals),
                "signals": {
                    "BUY": buy_count,
                    "SELL": sell_count, 
                    "HOLD": hold_count
                }
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}

def print_status():
    """Imprime el estado completo del sistema"""
    monitor = CryptonitaPipelineMonitor()
    
    print("🏥 ESTADO DEL SISTEMA CRYPTONITA")
    print("=" * 50)
    
    health = monitor.health_check()
    print(f"📊 Estado General: {health['status'].upper()}")
    print(f"🕐 Timestamp: {health['timestamp']}")
    print(f"🔴 Redis: {health['redis']}")
    print(f"👷 Workers activos: {health['workers']}")
    print(f"🗄️  Base de datos: {health['database']}")
    print(f"🧠 Archivos del modelo: {health['model_files']}")
    
    if 'error' in health:
        print(f"❌ Error: {health['error']}")
    
    print("\n📋 SEÑALES DE TRADING")
    print("-" * 30)
    signals_status = monitor.check_signals_file()
    if signals_status['status'] == 'healthy':
        print(f"✅ Archivo actualizado hace {signals_status['hours_ago']}h")
        print(f"📈 Señales: {signals_status['signals']}")
    elif signals_status['status'] == 'stale':
        print(f"⚠️  Archivo desactualizado ({signals_status['hours_ago']}h)")
    else:
        print(f"❌ {signals_status.get('message', 'Error con signals.json')}")

if __name__ == "__main__":
    print_status()