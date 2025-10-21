# 🎯 AUDITORÍA CRÍTICA Y PLAN MVP - CRYPTONITA

**Fecha:** 2025-10-21
**Objetivo:** Sistema de trading REAL operativo en 30 días
**Estrategia:** Migrar solo lo esencial, descartar experimentos incompletos

---

## ✅ CÓDIGO QUE SIRVE Y VAMOS A USAR

### 1. **CONFIGURACIÓN** - `src/config/settings.py`
- **Estado:** ✅ USAR (con mejoras de seguridad)
- **Qué rescatar:**
  - Universe de tickers
  - Configuración de DB
  - APIs keys structure
- **Qué mejorar:**
  - Migrar a .env (CRÍTICO)
  - Añadir validación

### 2. **INGESTA DE DATOS** - `src/data_ingestion/`
- **Estado:** ✅ USAR (core funcional)
- **Scripts a migrar:**
  - `ingest_historical_data.py` → Datos de Yahoo Finance ✅
  - `ingest_macro.py` → SPY, VIX, etc. ✅
  - `ingest_data.py` → Funciones base ✅
- **Descartar:**
  - `ingest_sentiment.py` → No añade valor al MVP
  - `ingest_onchain.py` → Experimental, para fase 2

### 3. **MODELO ML** - `models/ULTRA_MODEL_PACKAGE.joblib`
- **Estado:** ✅ USAR (es tu mejor modelo)
- **Accuracy:** 50.4% (marginal pero es lo que tienes funcionando)
- **Arquitectura:** StandardScaler → PCA → LGBM → LogisticRegression
- **Features:** 15 features (precios + macro + técnicos)
- **Acción:** Validar con backtest antes de usar en real

### 4. **FEATURE ENGINEERING** - `src/feature_engineering/`
- **Estado:** ✅ USAR
- **Rescatar:**
  - `technical_indicators.py` → RSI, MACD, EMAs ✅
  - `candle_patterns.py` → Patrones básicos ✅

### 5. **GENERACIÓN DE SEÑALES** - `src/production/03_generate_signals.py`
- **Estado:** ✅ USAR (lógica de trading bien pensada)
- **Estrategia LONG ONLY:**
  - BUY: confianza ≥ 75%
  - SELL: confianza ≥ 70% (solo posiciones abiertas)
  - Max 8 posiciones simultáneas
- **Qué mejorar:**
  - Añadir stop loss
  - Conectar con posiciones reales de Binance

### 6. **MONEY MANAGEMENT** - `src/trading/advanced_money_management.py`
- **Estado:** ✅ USAR (muy bien implementado)
- **Características:**
  - Gestión dinámica de riesgo
  - Scoring de volatilidad
  - Tamaño de posición adaptativo
- **Es uno de tus mejores archivos** 👍

### 7. **PIPELINE** - `src/pipeline/tasks.py`
- **Estado:** ✅ USAR (estructura Celery)
- **Workflow:**
  - ingest_data → features → signals → execute
- **Qué mejorar:**
  - Simplificar para MVP (quitar Celery inicialmente)
  - Usar cron simple primero

### 8. **DATABASE UTILS** - `src/utils/`
- **Estado:** ✅ USAR
- **Rescatar:**
  - `db_connector.py` → Conexión PostgreSQL ✅
  - `init_db.py` → Setup de tablas ✅

---

## ❌ CÓDIGO QUE NO SIRVE (DESCARTAR PARA MVP)

### 1. **TODO EL PROYECTO GNN** - `new_model/`
- **Razón:** Experimental, incompleto, no hay resultados
- **Decisión:** ❌ DESCARTAR del MVP
- **Futuro:** Retomar en Fase 2 (después de operar)
- **Archivos:** `new_model/data/*.py`, `CRYPTONITA_GNN_MASTER_PLAN.md`

### 2. **NOTEBOOKS** - `notebooks/`
- **Razón:** Exploración, no código de producción
- **Decisión:** ❌ NO MIGRAR al nuevo repo
- **Guardar:** Sí, pero en repo separado de análisis
- **Archivos:** `*.ipynb`, análisis exploratorios

### 3. **DASHBOARD WEB COMPLEJO** - `src/web/`
- **Razón:** Demasiado complejo para MVP
- **Decisión:** ⚠️ SIMPLIFICAR DRÁSTICAMENTE
- **MVP:** Un dashboard básico con métricas clave
- **Descartar:** Templates complejos, analytics avanzados

### 4. **SCRIPTS SUELTOS** - Raíz del proyecto
- **Descartar:**
  - `annotators.py` → Análisis de anotaciones (no relacionado)
  - `db_explorer.py` → Herramienta exploratoria
  - `repeater_optimizer.py` → Experimental
  - `post_reboot_monitor.py` → Utils específico
  - `test.py` → Script temporal
  - `replica_model.py` → Duplicado de lógica

### 5. **BACKUPS** - `backups/`
- **Razón:** Código antiguo duplicado
- **Decisión:** ❌ NO MIGRAR

### 6. **DATAFRAMES ANTIGUOS** - `dataframes/`
- **Razón:** Datos viejos, se regenerarán
- **Decisión:** ❌ NO MIGRAR (regenerar desde cero)

---

## 🏗️ ARQUITECTURA DEL NUEVO REPO

```
cryptonita-mvp/
│
├── .env.example              # Template de variables de entorno
├── .gitignore               # Ignorar credenciales y cache
├── README.md                # Documentación principal
├── requirements.txt         # Dependencias exactas
│
├── config/
│   ├── __init__.py
│   ├── settings.py          # Configuración central (con .env)
│   └── universe.py          # Lista de activos
│
├── data/
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── crypto_data.py   # Ingesta de precios crypto
│   │   ├── macro_data.py    # Ingesta de indicadores macro
│   │   └── binance_data.py  # Datos específicos de Binance
│   │
│   └── storage/
│       ├── __init__.py
│       └── db_manager.py    # PostgreSQL manager
│
├── features/
│   ├── __init__.py
│   ├── technical.py         # Indicadores técnicos
│   └── builder.py           # Constructor de features
│
├── model/
│   ├── __init__.py
│   ├── predictor.py         # Wrapper del modelo LGBM
│   └── trained/
│       └── ultra_model.joblib  # Modelo entrenado
│
├── trading/
│   ├── __init__.py
│   ├── signal_generator.py  # Genera señales BUY/SELL/HOLD
│   ├── risk_manager.py      # Money management
│   ├── order_executor.py    # Ejecuta órdenes en Binance
│   └── portfolio.py         # Track de posiciones
│
├── exchange/
│   ├── __init__.py
│   ├── binance_client.py    # Cliente de Binance
│   └── paper_trading.py     # Simulación sin dinero real
│
├── backtesting/
│   ├── __init__.py
│   ├── engine.py            # Motor de backtesting
│   └── metrics.py           # Cálculo de métricas
│
├── monitoring/
│   ├── __init__.py
│   ├── logger.py            # Sistema de logs
│   └── dashboard.py         # Dashboard simple FastAPI
│
├── scripts/
│   ├── setup_database.py    # Setup inicial de DB
│   ├── run_backtest.py      # Ejecutar backtest
│   ├── run_paper_trading.py # Paper trading
│   └── run_live_trading.py  # Trading real (con confirmación)
│
├── tests/
│   ├── __init__.py
│   ├── test_ingestion.py
│   ├── test_features.py
│   ├── test_model.py
│   └── test_trading.py
│
└── docs/
    ├── SETUP.md             # Cómo instalar
    ├── OPERATION.md         # Cómo operar
    └── SAFETY.md            # Medidas de seguridad
```

---

## 📅 PLAN DE 30 DÍAS

### **SEMANA 1: FUNDAMENTOS (Días 1-7)**
- [ ] Día 1-2: Crear nuevo repo con estructura limpia
- [ ] Día 3: Migrar y securizar configuración (.env)
- [ ] Día 4-5: Migrar ingesta de datos (crypto + macro)
- [ ] Día 6: Setup PostgreSQL y tablas
- [ ] Día 7: Migrar feature engineering

### **SEMANA 2: MODELO Y TRADING (Días 8-14)**
- [ ] Día 8-9: Migrar modelo LGBM y crear wrapper
- [ ] Día 10: Migrar signal generator (lógica LONG ONLY)
- [ ] Día 11-12: Migrar money management
- [ ] Día 13: Implementar cliente de Binance (básico)
- [ ] Día 14: Crear sistema de portfolio tracking

### **SEMANA 3: VALIDACIÓN (Días 15-21)**
- [ ] Día 15-17: Backtesting exhaustivo (6 meses de datos)
- [ ] Día 18-19: Análisis de resultados (Sharpe, drawdown, win rate)
- [ ] Día 20: Implementar mejoras basadas en backtest
- [ ] Día 21: Paper trading en Binance testnet (3 días)

### **SEMANA 4: PRODUCCIÓN (Días 22-30)**
- [ ] Día 22-23: Dashboard de monitoring básico
- [ ] Día 24: Tests automatizados críticos
- [ ] Día 25: Documentación operativa completa
- [ ] Día 26-27: Pruebas finales en testnet
- [ ] Día 28: Deploy en servidor
- [ ] Día 29: Primera operación real con $100-500 USD
- [ ] Día 30: Monitoring intensivo 24h

---

## 🎯 MVP FEATURES (LO MÍNIMO FUNCIONAL)

### ✅ DEBE TENER (CRÍTICO)
1. Ingesta diaria automática de datos
2. Generación de señales con modelo LGBM
3. Ejecución de órdenes en Binance
4. Gestión de riesgo (stop loss, position sizing)
5. Logs de todas las operaciones
6. Dashboard básico para ver estado
7. Sistema de alertas (email/Telegram)

### ⚠️ BUENO TENER (SI HAY TIEMPO)
8. Backtesting visual
9. Dashboard con gráficos
10. Análisis de performance

### ❌ NO PARA MVP (FASE 2)
- GNN o modelos experimentales
- Sentiment analysis
- On-chain data
- Dashboard complejo
- Machine learning automático

---

## 🔒 MEDIDAS DE SEGURIDAD CRÍTICAS

### 1. **PROTECCIÓN DE CREDENCIALES**
```bash
# .env
BINANCE_API_KEY=xxx
BINANCE_SECRET=xxx
DB_PASSWORD=xxx

# NUNCA commitear .env
```

### 2. **LÍMITES DE SEGURIDAD EN CÓDIGO**
```python
# En order_executor.py
MAX_ORDER_SIZE_USD = 500      # Máximo $500 por orden
MAX_DAILY_LOSS_USD = 200      # Stop si pierdes $200 en un día
MAX_TOTAL_RISK_PERCENT = 2    # Max 2% del capital en riesgo
REQUIRE_MANUAL_APPROVAL = True  # Al inicio, aprobación manual
```

### 3. **TESTNET PRIMERO**
- Usar Binance Testnet 1 semana antes de dinero real
- Validar TODAS las órdenes funcionan correctamente
- Confirmar que stop loss funciona

### 4. **EMPEZAR PEQUEÑO**
- Primera semana: $100-500 USD máximo
- Si funciona 1 semana sin problemas → subir a $1000
- Escalar gradualmente, nunca todo de golpe

---

## 📊 MÉTRICAS DE ÉXITO DEL MVP

### Técnicas:
- [ ] Sistema ejecuta trades sin errores
- [ ] Ingesta de datos sin fallos por 7 días
- [ ] Stop loss funciona correctamente
- [ ] Dashboard muestra datos en tiempo real

### Financieras (después de 1 mes operando):
- [ ] No perder más del 5% del capital inicial
- [ ] Win rate > 45%
- [ ] Sharpe ratio > 0.5
- [ ] Máximo drawdown < 10%

---

## 🚀 PRÓXIMO PASO INMEDIATO

**ACCIÓN AHORA:** Crear el nuevo repositorio con la estructura limpia

¿Quieres que empiece a:
1. Crear el nuevo repo en este mismo directorio?
2. O prefieres que lo creemos en una ubicación diferente?

Dime y empezamos YA. Vamos a hacer esto realidad. 💪
