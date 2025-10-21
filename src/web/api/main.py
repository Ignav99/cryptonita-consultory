# src/web/api/main.py - VERSIÓN MEJORADA
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import numpy as np


# Agregar path del proyecto
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importar componentes del sistema
from src.pipeline.monitoring import CryptonitaPipelineMonitor
from src.web.api.database import data_service
from src.web.api.analytics import AnalyticsService
from src.config import settings
from src.trading.advanced_money_management import advanced_money_manager

# Crear aplicación FastAPI
app = FastAPI(
    title="Cryptonita Trading Dashboard Pro",
    description="Dashboard avanzado para el sistema de trading automatizado Cryptonita",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar archivos estáticos y templates
try:
    app.mount("/static", StaticFiles(directory="src/web/static"), name="static")
    templates = Jinja2Templates(directory="src/web/templates")
except Exception as e:
    print(f"Warning: Could not mount static files or templates: {e}")

# Inicializar servicios
analytics_service = AnalyticsService()

# =============================================
# ENDPOINTS PRINCIPALES DEL DASHBOARD
# =============================================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Página principal del dashboard mejorado"""
    try:
        return templates.TemplateResponse("enhanced_dashboard.html", {"request": request})
    except Exception as e:
        # Fallback si no hay template disponible
        return HTMLResponse("""
        <html>
            <head><title>Cryptonita Dashboard</title></head>
            <body>
                <h1>Cryptonita Trading Dashboard</h1>
                <p>API funcionando correctamente. Visite <a href="/api/docs">/api/docs</a> para la documentación.</p>
                <script>window.location.href = '/api/docs';</script>
            </body>
        </html>
        """)

# =============================================
# ENDPOINTS DE DATOS MEJORADOS
# =============================================

@app.get("/api/status")
async def get_system_status():
    """Estado completo del sistema con métricas detalladas"""
    try:
        monitor = CryptonitaPipelineMonitor()
        
        # Obtener estado del sistema
        health = monitor.health_check()
        signals = monitor.check_signals_file()
        system_metrics = data_service.get_system_metrics()
        
        # Calcular métricas adicionales
        uptime = datetime.now() - datetime(2024, 1, 1)  # Placeholder
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "system": {
                **health,
                "uptime_days": uptime.days,
                "version": "2.0.0"
            },
            "signals": signals,
            "database": system_metrics,
            "performance": {
                "response_time_ms": 50,  # Placeholder
                "memory_usage_mb": 256,  # Placeholder
                "cpu_usage_percent": 15  # Placeholder
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )

@app.get("/api/portfolio")
async def get_portfolio_data():
    """Datos completos del portfolio con análisis"""
    try:
        # Datos básicos del portfolio
        portfolio = data_service.get_portfolio_summary()
        recent_trades = data_service.get_recent_trades(limit=10)
        top_performers = data_service.get_top_performers(days=7)
        
        # Análisis adicional
        portfolio_analysis = analytics_service.calculate_portfolio_metrics(recent_trades)
        risk_metrics = analytics_service.calculate_risk_metrics(recent_trades)
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "portfolio": {
                **portfolio,
                "analysis": portfolio_analysis,
                "risk_metrics": risk_metrics
            },
            "recent_trades": recent_trades,
            "top_performers": top_performers,
            "market_conditions": analytics_service.get_market_sentiment()
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )

# REEMPLAZAR el endpoint @app.get("/api/signals") en main.py con este:

@app.get("/api/signals")
async def get_current_signals():
    """Señales actuales con análisis avanzado de gestión de dinero"""
    try:
        signals_path = os.path.join(project_root, 'signals.json')
        advanced_signals_path = os.path.join(project_root, 'advanced_signals.json')
        
        if not os.path.exists(signals_path):
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": "No signals file found"}
            )
        
        # Cargar señales básicas
        with open(signals_path, 'r') as f:
            signals_data = json.load(f)
        
        # Cargar análisis avanzado si existe
        advanced_data = {}
        if os.path.exists(advanced_signals_path):
            try:
                with open(advanced_signals_path, 'r') as f:
                    advanced_data = json.load(f)
            except:
                advanced_data = {}
        
        # Análisis de señales básico
        signal_analysis = analytics_service.analyze_signals(signals_data)
        
        # Contar señales
        buy_count = sum(1 for signal in signals_data.values() if signal == "BUY")
        sell_count = sum(1 for signal in signals_data.values() if signal == "SELL")
        hold_count = sum(1 for signal in signals_data.values() if signal == "HOLD")
        
        # Preparar respuesta completa
        response_data = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "signals": signals_data,
            "summary": {
                "total": len(signals_data),
                "buy": buy_count,
                "sell": sell_count,
                "hold": hold_count
            },
            "analysis": signal_analysis,
            "generated_at": os.path.getmtime(signals_path)
        }
        
        # Añadir datos avanzados si están disponibles
        if advanced_data:
            trading_summary = advanced_data.get("trading_summary", {})
            trade_recommendations = advanced_data.get("trade_recommendations", {})
            
            response_data.update({
                "advanced_analysis": {
                    "market_sentiment": trading_summary.get("market_sentiment", "UNKNOWN"),
                    "trades_to_execute": trading_summary.get("trades_to_execute", 0),
                    "total_investment_usdc": trading_summary.get("total_investment_usdc", 0),
                    "portfolio_cash_available": trading_summary.get("portfolio_status", {}).get("cash_available", 0),
                    "trade_recommendations": trade_recommendations
                },
                "trading_decisions": {
                    "total_recommended_trades": len(trade_recommendations),
                    "total_capital_allocation": sum(
                        rec.get("position_size", {}).get("amount_usdc", 0) 
                        for rec in trade_recommendations.values()
                    ),
                    "average_position_size": (
                        sum(rec.get("position_size", {}).get("percentage", 0) 
                            for rec in trade_recommendations.values()) / 
                        max(1, len(trade_recommendations))
                    ) if trade_recommendations else 0,
                    "risk_distribution": {
                        "conservative": len([r for r in trade_recommendations.values() 
                                           if r.get("position_size", {}).get("percentage", 0) < 3]),
                        "moderate": len([r for r in trade_recommendations.values() 
                                       if 3 <= r.get("position_size", {}).get("percentage", 0) < 8]),
                        "aggressive": len([r for r in trade_recommendations.values() 
                                         if r.get("position_size", {}).get("percentage", 0) >= 8])
                    }
                }
            })
        
        return response_data
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )

# =============================================
# NUEVOS ENDPOINTS DE ANALYTICS
# =============================================

@app.get("/api/analytics/performance")
async def get_performance_analytics():
    """Métricas detalladas de performance"""
    try:
        trades_data = data_service.get_recent_trades(limit=100)
        
        if not trades_data:
            return {
                "status": "success",
                "data": {
                    "total_return": 0,
                    "sharpe_ratio": 0,
                    "max_drawdown": 0,
                    "win_rate": 0,
                    "average_trade_duration": 0,
                    "volatility": 0
                }
            }
        
        performance_metrics = analytics_service.calculate_performance_metrics(trades_data)
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "data": performance_metrics
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )

@app.get("/api/analytics/historical/{days}")
async def get_historical_data(days: int = 30):
    """Datos históricos para gráficos"""
    try:
        if days > 365:
            days = 365  # Límite máximo
        
        historical_data = analytics_service.get_historical_portfolio_data(days)
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "period_days": days,
            "data": historical_data
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )

# =============================================
# ENDPOINTS DE CONTROL
# =============================================

@app.post("/api/pipeline/manual")
async def trigger_manual_pipeline(background_tasks: BackgroundTasks):
    """Ejecutar pipeline manualmente"""
    try:
        # Importar y ejecutar pipeline en background
        from src.pipeline.tasks import run_complete_pipeline
        
        # Agregar tarea en background
        background_tasks.add_task(run_complete_pipeline)
        
        return {
            "status": "success",
            "message": "Pipeline iniciado en background",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Error al iniciar pipeline",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/api/config")
async def get_configuration():
    """Obtener configuración actual del sistema"""
    try:
        config = {
            "universe_size": len(settings.UNIVERSE_TICKERS),
            "risk_per_trade": getattr(settings, 'RISK_PER_TRADE', 0.01),
            "trading_enabled": True,  # Placeholder
            "auto_execution_time": "07:00",
            "database_url": f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}",
            "redis_url": getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
        }
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "config": config
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )

# =============================================
# ENDPOINTS DE REPORTES
# =============================================

@app.get("/api/reports/daily")
async def get_daily_report():
    """Reporte diario del sistema"""
    try:
        report = analytics_service.generate_daily_report()
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "report": report
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )

@app.get("/api/reports/weekly")
async def get_weekly_report():
    """Reporte semanal completo"""
    try:
        report = analytics_service.generate_weekly_report()
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "report": report
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": str(e)}
        )

# =============================================
# ENDPOINTS DE UTILIDAD
# =============================================

@app.get("/api/info")
async def get_system_info():
    """Información general del sistema"""
    return {
        "name": "Cryptonita Trading Bot Pro",
        "version": "2.0.0",
        "description": "Sistema avanzado de trading automatizado con ML",
        "status": "operational",
        "features": [
            "Trading automatizado con ML",
            "Análisis técnico avanzado",
            "Gestión de riesgo dinámica",
            "Dashboard en tiempo real",
            "Reportes automáticos",
            "API REST completa"
        ],
        "endpoints": [
            "/api/status - Estado del sistema",
            "/api/portfolio - Datos del portfolio",
            "/api/signals - Señales de trading",
            "/api/analytics/* - Métricas y análisis",
            "/api/reports/* - Reportes automáticos"
        ]
    }

@app.get("/api/health")
async def health_check():
    """Health check simple para monitoreo"""
    try:
        # Verificar conexión a base de datos
        db_status = data_service.get_system_metrics()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "api": "healthy",
                "database": "healthy" if not db_status.get("error") else "unhealthy",
                "redis": "unknown",  # TODO: Implementar check de Redis
                "celery": "unknown"  # TODO: Implementar check de Celery
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )

# =============================================
# MANEJO DE ERRORES
# =============================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "status": "error",
            "message": "Endpoint not found",
            "path": str(request.url.path),
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }
    )

# =============================================
# STARTUP Y SHUTDOWN
# =============================================

@app.on_event("startup")
async def startup_event():
    """Inicialización al arrancar la API"""
    print("🚀 Cryptonita API Pro iniciando...")
    
    # Verificar conexión a base de datos
    try:
        system_status = data_service.get_system_metrics()
        print("✅ Conexión a base de datos establecida")
    except Exception as e:
        print(f"⚠️ Warning: Error conectando a base de datos: {e}")
    
    print("✅ Cryptonita API Pro lista en http://localhost:8000")

@app.on_event("shutdown")
async def shutdown_event():
    """Limpieza al cerrar la API"""
    print("🛑 Cryptonita API Pro cerrando...")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando Cryptonita Dashboard Pro...")
    print("🌐 Dashboard: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/api/docs")
    print("❌ Presiona CTRL+C para detener")
    
    uvicorn.run(
        "src.web.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )