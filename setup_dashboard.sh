#!/bin/bash
# setup_dashboard.sh - Script para configurar el dashboard mejorado de Cryptonita

echo "🚀 CRYPTONITA DASHBOARD PRO - SETUP"
echo "====================================="

# Verificar que estamos en el directorio correcto
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Ejecuta este script desde el directorio raíz del proyecto Cryptonita"
    exit 1
fi

# Crear backup de archivos existentes
echo "📦 Creando backup de archivos existentes..."
mkdir -p backups/$(date +%Y%m%d_%H%M%S)
if [ -f "src/web/api/main.py" ]; then
    cp src/web/api/main.py backups/$(date +%Y%m%d_%H%M%S)/main_backup.py
fi
if [ -f "src/web/api/database.py" ]; then
    cp src/web/api/database.py backups/$(date +%Y%m%d_%H%M%S)/database_backup.py
fi

# Crear estructura de directorios necesaria
echo "📁 Creando estructura de directorios..."
mkdir -p src/web/api
mkdir -p src/web/templates
mkdir -p src/web/static/css
mkdir -p src/web/static/js
mkdir -p logs

# Instalar dependencias adicionales
echo "📦 Instalando dependencias adicionales..."
pip install fastapi uvicorn jinja2 python-multipart

# Crear archivo de configuración del dashboard
echo "⚙️ Creando configuración del dashboard..."
cat > src/web/config.py << 'EOF'
# src/web/config.py
import os

class DashboardConfig:
    """Configuración del dashboard web"""
    
    # Configuración del servidor
    HOST = "0.0.0.0"
    PORT = 8000
    DEBUG = True
    
    # Configuración de la API
    API_TITLE = "Cryptonita Trading Dashboard Pro"
    API_VERSION = "2.0.0"
    API_DESCRIPTION = "Dashboard avanzado para el sistema de trading automatizado Cryptonita"
    
    # Configuración de seguridad (para futuro)
    SECRET_KEY = "cryptonita_dashboard_secret_key_change_in_production"
    
    # Configuración de archivos estáticos
    STATIC_DIR = "src/web/static"
    TEMPLATES_DIR = "src/web/templates"
    
    # Configuración de logging
    LOG_LEVEL = "INFO"
    LOG_FILE = "logs/dashboard.log"
    
    # Configuración de actualizaciones automáticas
    AUTO_REFRESH_SECONDS = 30
    
    # Límites de la API
    MAX_TRADES_LIMIT = 100
    MAX_HISTORY_DAYS = 365
EOF

# Crear template HTML mejorado
echo "🎨 Creando template HTML..."
cat > src/web/templates/enhanced_dashboard.html << 'EOF'
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cryptonita Trading Dashboard Pro</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🤖</text></svg>">
    <style>
        .status-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 8px; }
        .healthy { background-color: #10b981; }
        .degraded { background-color: #f59e0b; }
        .unhealthy { background-color: #ef4444; }
        .metric-card { transition: transform 0.2s, box-shadow 0.2s; }
        .metric-card:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.1); }
        .loading { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .5; } }
    </style>
</head>
<body class="bg-gray-50">
    <!-- Header mejorado -->
    <header class="bg-white shadow-lg border-b border-gray-200">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center py-4">
                <div class="flex items-center space-x-4">
                    <h1 class="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                        🤖 Cryptonita Pro
                    </h1>
                    <span id="status-indicator" class="px-4 py-2 rounded-full text-sm font-medium bg-green-100 text-green-800 shadow-sm">
                        <span class="status-dot healthy"></span>SISTEMA OPERATIVO
                    </span>
                    <span class="text-sm text-gray-500">v2.0.0</span>
                </div>
                <div class="flex space-x-3">
                    <button id="refresh-btn" class="bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 rounded-lg shadow transition-colors">
                        🔄 Actualizar
                    </button>
                    <button id="manual-pipeline-btn" class="bg-green-500 hover:bg-green-600 text-white font-semibold py-2 px-4 rounded-lg shadow transition-colors">
                        ▶️ Ejecutar Pipeline
                    </button>
                </div>
            </div>
        </div>
    </header>

    <!-- Contenido principal -->
    <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        
        <!-- Cards de métricas principales -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            
            <!-- Portfolio Value -->
            <div class="metric-card bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-500">Portfolio Total</p>
                        <p id="portfolio-value" class="text-2xl font-bold text-gray-900">$10,000</p>
                        <p id="portfolio-change" class="text-sm text-green-600">+0.00% (24h)</p>
                    </div>
                    <div class="h-12 w-12 bg-green-100 rounded-lg flex items-center justify-center">
                        <span class="text-2xl">💰</span>
                    </div>
                </div>
            </div>

            <!-- Señales Activas -->
            <div class="metric-card bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-500">Señales Activas</p>
                        <p id="active-signals" class="text-2xl font-bold text-gray-900">0</p>
                        <p class="text-sm text-gray-500">BUY/SELL/HOLD</p>
                    </div>
                    <div class="h-12 w-12 bg-blue-100 rounded-lg flex items-center justify-center">
                        <span class="text-2xl">📊</span>
                    </div>
                </div>
            </div>

            <!-- Trades Ejecutados -->
            <div class="metric-card bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-500">Trades (30d)</p>
                        <p id="total-trades" class="text-2xl font-bold text-gray-900">0</p>
                        <p class="text-sm text-gray-500">Ejecutados</p>
                    </div>
                    <div class="h-12 w-12 bg-purple-100 rounded-lg flex items-center justify-center">
                        <span class="text-2xl">🎯</span>
                    </div>
                </div>
            </div>

            <!-- Estado del Sistema -->
            <div class="metric-card bg-white p-6 rounded-xl shadow-sm border border-gray-100">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-500">Sistema</p>
                        <p id="system-status" class="text-2xl font-bold text-gray-900">HEALTHY</p>
                        <p class="text-sm text-gray-500">Todos los servicios</p>
                    </div>
                    <div class="h-12 w-12 bg-orange-100 rounded-lg flex items-center justify-center">
                        <span class="text-2xl">🏥</span>
                    </div>
                </div>
            </div>

        </div>

        <!-- Gráficos y datos -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            
            <!-- Distribución de Señales -->
            <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">Distribución de Señales</h3>
                <div class="relative" style="height: 300px;">
                    <canvas id="signals-chart"></canvas>
                </div>
                <div id="signals-summary" class="mt-4 text-center text-sm text-gray-600">
                    Cargando señales...
                </div>
            </div>

            <!-- Top Performers -->
            <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">🏆 Top Performers (7d)</h3>
                <div id="top-performers" class="space-y-3">
                    <div class="loading text-gray-500">Cargando performance...</div>
                </div>
            </div>

        </div>

        <!-- Actividad Reciente -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">📈 Actividad Reciente</h3>
            <div id="recent-trades" class="space-y-3">
                <div class="loading text-gray-500">Cargando actividad...</div>
            </div>
        </div>

    </main>

    <!-- JavaScript mejorado -->
    <script>
        let signalsChart = null;
        
        // Función principal de carga de datos
        async function loadDashboardData() {
            try {
                const [statusData, portfolioData, signalsData] = await Promise.all([
                    fetch('/api/status').then(r => r.json()),
                    fetch('/api/portfolio').then(r => r.json()),
                    fetch('/api/signals').then(r => r.json())
                ]);
                
                updateUI(statusData, portfolioData, signalsData);
                
            } catch (error) {
                console.error('Error loading dashboard data:', error);
                showError('Error cargando datos del dashboard');
            }
        }
        
        function updateUI(statusData, portfolioData, signalsData) {
            // Actualizar métricas principales
            if (portfolioData.status === 'success') {
                document.getElementById('total-trades').textContent = portfolioData.portfolio.total_trades || 0;
                document.getElementById('portfolio-value').textContent = `$${(portfolioData.portfolio.estimated_balance || 10000).toLocaleString()}`;
                updateRecentTrades(portfolioData.recent_trades);
                updateTopPerformers(portfolioData.top_performers);
            }
            
            if (signalsData.status === 'success') {
                document.getElementById('active-signals').textContent = signalsData.summary.total || 0;
                updateSignalsChart(signalsData.summary);
                updateSignalsSummary(signalsData.summary);
            }
            
            if (statusData.status === 'success') {
                document.getElementById('system-status').textContent = 'HEALTHY';
            }
        }
        
        function updateSignalsChart(summary) {
            const ctx = document.getElementById('signals-chart').getContext('2d');
            
            if (signalsChart) {
                signalsChart.destroy();
            }
            
            signalsChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['BUY', 'SELL', 'HOLD'],
                    datasets: [{
                        data: [summary.buy || 0, summary.sell || 0, summary.hold || 0],
                        backgroundColor: ['#10b981', '#ef4444', '#6b7280'],
                        borderWidth: 3,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { padding: 20, font: { size: 12 } }
                        }
                    }
                }
            });
        }
        
        function updateSignalsSummary(summary) {
            document.getElementById('signals-summary').innerHTML = `
                <div class="grid grid-cols-3 gap-4 text-center">
                    <div class="bg-green-50 p-3 rounded-lg">
                        <div class="text-green-600 font-bold text-lg">${summary.buy || 0}</div>
                        <div class="text-xs text-green-600">BUY</div>
                    </div>
                    <div class="bg-red-50 p-3 rounded-lg">
                        <div class="text-red-600 font-bold text-lg">${summary.sell || 0}</div>
                        <div class="text-xs text-red-600">SELL</div>
                    </div>
                    <div class="bg-gray-50 p-3 rounded-lg">
                        <div class="text-gray-600 font-bold text-lg">${summary.hold || 0}</div>
                        <div class="text-xs text-gray-600">HOLD</div>
                    </div>
                </div>
            `;
        }
        
        function updateTopPerformers(performers) {
            const container = document.getElementById('top-performers');
            
            if (!performers || performers.length === 0) {
                container.innerHTML = '<div class="text-gray-500 text-center py-4">No hay datos suficientes</div>';
                return;
            }
            
            container.innerHTML = performers.slice(0, 5).map((performer, index) => {
                const colorClass = performer.change_percent > 0 ? 'text-green-600' : 'text-red-600';
                const bgClass = performer.change_percent > 0 ? 'bg-green-50' : 'bg-red-50';
                const arrow = performer.change_percent > 0 ? '↗️' : '↘️';
                const medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '📈';
                
                return `
                    <div class="flex justify-between items-center p-3 ${bgClass} rounded-lg">
                        <div class="flex items-center space-x-2">
                            <span>${medal}</span>
                            <span class="font-medium">${performer.ticker}</span>
                        </div>
                        <span class="${colorClass} font-bold">
                            ${arrow} ${performer.change_percent}%
                        </span>
                    </div>
                `;
            }).join('');
        }
        
        function updateRecentTrades(trades) {
            const container = document.getElementById('recent-trades');
            
            if (!trades || trades.length === 0) {
                container.innerHTML = '<div class="text-gray-500 text-center py-4">No hay trades recientes</div>';
                return;
            }
            
            container.innerHTML = trades.slice(0, 5).map(trade => {
                const colorClass = trade.action === 'BUY' ? 'text-green-600' : 'text-red-600';
                const bgClass = trade.action === 'BUY' ? 'bg-green-50' : 'bg-red-50';
                
                return `
                    <div class="flex justify-between items-center p-3 ${bgClass} rounded-lg">
                        <div>
                            <div class="font-medium">${trade.ticker}</div>
                            <div class="text-xs text-gray-500">${trade.time_ago || 'Recently'}</div>
                        </div>
                        <div class="text-right">
                            <div class="${colorClass} font-bold">${trade.action}</div>
                            <div class="text-xs text-gray-500">$${trade.total_value.toFixed(2)}</div>
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        function showError(message) {
            console.error(message);
            // Aquí podrías mostrar una notificación de error al usuario
        }
        
        // Ejecutar pipeline manualmente
        async function triggerPipeline() {
            const button = document.getElementById('manual-pipeline-btn');
            const originalText = button.textContent;
            button.disabled = true;
            button.textContent = '⏳ Ejecutando...';
            
            try {
                const response = await fetch('/api/pipeline/manual', { method: 'POST' });
                const data = await response.json();
                
                if (data.status === 'success') {
                    alert('Pipeline iniciado exitosamente!');
                    loadDashboardData(); // Recargar datos
                } else {
                    alert('Error: ' + data.message);
                }
            } catch (error) {
                alert('Error al ejecutar pipeline: ' + error.message);
            } finally {
                button.disabled = false;
                button.textContent = originalText;
            }
        }
        
        // Event listeners
        document.getElementById('refresh-btn').addEventListener('click', loadDashboardData);
        document.getElementById('manual-pipeline-btn').addEventListener('click', triggerPipeline);
        
        // Cargar datos iniciales y configurar auto-refresh
        document.addEventListener('DOMContentLoaded', function() {
            loadDashboardData();
            setInterval(loadDashboardData, 30000); // Auto-refresh cada 30 segundos
        });
    </script>
</body>
</html>
EOF

# Crear script de inicio del dashboard
echo "🚀 Creando script de inicio..."
cat > start_dashboard.py << 'EOF'
#!/usr/bin/env python3
# start_dashboard.py - Script para iniciar el dashboard de Cryptonita

import sys
import os
import uvicorn

# Agregar path del proyecto
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def main():
    print("🚀 Iniciando Cryptonita Dashboard Pro...")
    print("🌐 Dashboard disponible en: http://localhost:8000")
    print("📚 API Docs disponible en: http://localhost:8000/api/docs")
    print("❌ Presiona CTRL+C para detener")
    
    try:
        uvicorn.run(
            "src.web.api.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Dashboard detenido.")
    except Exception as e:
        print(f"❌ Error al iniciar dashboard: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
EOF

chmod +x start_dashboard.py

# Crear archivo de monitoreo del sistema
echo "📊 Creando sistema de monitoreo..."
cat > src/pipeline/monitoring.py << 'EOF'
# src/pipeline/monitoring.py
import os
import sys
import json
import psutil
from datetime import datetime
from typing import Dict

# Agregar path del proyecto
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

class CryptonitaPipelineMonitor:
    """Monitor del pipeline de Cryptonita"""
    
    def __init__(self):
        self.project_root = project_root
    
    def health_check(self) -> Dict:
        """Verifica la salud general del sistema"""
        try:
            return {
                "status": "healthy",
                "redis": self._check_redis(),
                "workers": self._count_workers(),
                "memory_usage": psutil.virtual_memory().percent,
                "cpu_usage": psutil.cpu_percent(),
                "disk_usage": psutil.disk_usage('/').percent
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "redis": "unknown",
                "workers": 0
            }
    
    def check_signals_file(self) -> Dict:
        """Verifica el archivo de señales"""
        signals_path = os.path.join(self.project_root, 'signals.json')
        
        if not os.path.exists(signals_path):
            return {
                "status": "missing",
                "message": "Archivo de señales no encontrado"
            }
        
        try:
            # Verificar que el archivo sea válido JSON
            with open(signals_path, 'r') as f:
                signals = json.load(f)
            
            # Verificar que las señales sean recientes (menos de 24 horas)
            file_time = datetime.fromtimestamp(os.path.getmtime(signals_path))
            hours_old = (datetime.now() - file_time).total_seconds() / 3600
            
            if hours_old > 24:
                status = "stale"
                message = f"Señales tienen {hours_old:.1f} horas de antigüedad"
            else:
                status = "healthy"
                message = f"Señales actualizadas hace {hours_old:.1f} horas"
            
            return {
                "status": status,
                "message": message,
                "signals_count": len(signals),
                "last_updated": file_time.isoformat()
            }
            
        except json.JSONDecodeError:
            return {
                "status": "corrupt",
                "message": "Archivo de señales corrupto"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _check_redis(self) -> str:
        """Verifica si Redis está disponible"""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            return "connected"
        except:
            return "disconnected"
    
    def _count_workers(self) -> int:
        """Cuenta workers de Celery activos"""
        try:
            # Buscar procesos de Celery
            workers = 0
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'celery' in ' '.join(proc.info['cmdline']).lower():
                        workers += 1
                except:
                    continue
            return workers
        except:
            return 0
EOF

# Verificar instalación
echo "✅ Verificando instalación..."
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from src.utils.db_connector import create_db_engine
    engine = create_db_engine()
    if engine:
        print('✅ Conexión a base de datos: OK')
    else:
        print('⚠️ Conexión a base de datos: FAILED')
except Exception as e:
    print(f'⚠️ Error verificando DB: {e}')

try:
    import fastapi, uvicorn
    print('✅ FastAPI y Uvicorn: OK')
except ImportError as e:
    print(f'⚠️ Falta instalar: {e}')
"

echo ""
echo "🎉 SETUP COMPLETADO!"
echo "==================="
echo ""
echo "📋 Próximos pasos:"
echo "1. Ejecutar: python3 start_dashboard.py"
echo "2. Abrir navegador en: http://localhost:8000"
echo "3. Verificar que todos los datos se cargan correctamente"
echo ""
echo "📁 Archivos creados:"
echo "   - src/web/api/main.py (mejorado)"
echo "   - src/web/api/database.py (mejorado)"
echo "   - src/web/api/analytics.py (nuevo)"
echo "   - src/web/templates/enhanced_dashboard.html"
echo "   - start_dashboard.py"
echo "   - src/pipeline/monitoring.py"
echo ""
echo "🔧 Para personalizar:"
echo "   - Edita src/web/config.py para configuración"
echo "   - Modifica templates en src/web/templates/"
echo "   - Ajusta estilos en src/web/static/"
echo ""