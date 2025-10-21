# src/config/settings.py
import os
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()

# Credenciales de la Base de Datos PostgreSQL
DB_USER = "cryptonita_user"
DB_PASSWORD = "TIZavoltio999"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "cryptonita_db2"

# Clave de API de Messari (la añadiremos más tarde)
MESSARI_API_KEY = "tEOSr6mBeP1WAJ0qmBPspgiIZsYZlSNkh+tzCgp0WBRsYJJj"

# Clave de API de NewsAPI
NEWS_API_KEY = "ff993add0bea49c7b3ff3f7a25804518"

NEWS_API_KEY_2 = "pub_434a3b1cb3e340f39aac6cb0e9aca5dc"

DUNE_API_KEY = "052d5xXEVkDXuCcClo2FagpZVTuEZmwe"

# settings.py

# ... (tus otras variables) ...


EXCHANGE_API_KEY = "5vO4Zpj5CVDgAhGXGqCE5ZklaGJbgXHy4NGUWa5Eofqll5jVL6yDCtFC6BhyPmND"
EXCHANGE_API_SECRET = "aHY78rV69UlczYgOYGdYpFf4Ji9u0OrQYFxwokWZKCoSKCwErs3L9S2NatwaYNqz"


## Rango de fechas por defecto para la ingesta histórica
HISTORIC_START_DATE = "2022-07-24"
HISTORIC_END_DATE = "2025-07-24"

# src/config/settings.py

# --- UNIVERSO DE ACTIVOS ---
## settings.py


# settings.py (CORREGIDO)

# ... (tus otras variables) ...

# UNIVERSO DE ACTIVOS DEFINITIVO (sin CFG y GNO)
UNIVERSE_TICKERS = [
    'BTC-USD', 'ETH-USD', 'BNB-USD', 'MATIC-USD', 'LINK-USD', 'ADA-USD', 
    'DOGE-USD', 'DOT-USD', 'LTC-USD', 'SHIB-USD', 'SOL-USD', 'XRP-USD',
    'ONDO-USD', 'RNDR-USD', 'AVAX-USD', 'FIL-USD', 'TAO-USD', 'AAVE-USD',
    'UNI-USD', 'HNT-USD', 'AR-USD', 'FET-USD', 'TON-USD',
    'STX-USD', 'NEAR-USD', 'ICP-USD', 'SUI-USD', 'HBAR-USD', 'TRX-USD',
    'XLM-USD', 'BCH-USD', 'THETA-USD', 'XMR-USD', 'INJ-USD', 'TIA-USD',
    'APT-USD', 'VET-USD', 'MKR-USD', 'RUNE-USD', 'GRT-USD',
    'DYDX-USD', 'ARB-USD', 'OP-USD', 'SNX-USD', 'LDO-USD', 'FTM-USD',
    'ENA-USD', 'KAS-USD', 'EGLD-USD', 'SEI-USD'
]

## settings.py

# ... (tus otras variables) ...

# REEMPLAZA la sección TICKER_MAP_BINANCE en tu settings.py con esto:

# MAPEO DE TICKERS PARA BINANCE (FORMATO CORRECTO SIN BARRAS)
TICKER_MAP_BINANCE = {
    'BTC-USD': 'BTCUSDT', 'ETH-USD': 'ETHUSDT', 'BNB-USD': 'BNBUSDT', 'SOL-USD': 'SOLUSDT',
    'XRP-USD': 'XRPUSDT', 'DOGE-USD': 'DOGEUSDT', 'ADA-USD': 'ADAUSDT', 'AVAX-USD': 'AVAXUSDT',
    'DOT-USD': 'DOTUSDT', 'LINK-USD': 'LINKUSDT', 'TRX-USD': 'TRXUSDT', 'MATIC-USD': 'MATICUSDT',
    'BCH-USD': 'BCHUSDT', 'ICP-USD': 'ICPUSDT', 'NEAR-USD': 'NEARUSDT', 'UNI-USD': 'UNIUSDT',
    'LTC-USD': 'LTCUSDT', 'AAVE-USD': 'AAVEUSDT', 'FTM-USD': 'FTMUSDT', 'XLM-USD': 'XLMUSDT',
    'GRT-USD': 'GRTUSDT', 'RNDR-USD': 'RENDERUSDT', 'HBAR-USD': 'HBARUSDT', 'FIL-USD': 'FILUSDT',
    'VET-USD': 'VETUSDT', 'INJ-USD': 'INJUSDT', 'OP-USD': 'OPUSDT', 'TIA-USD': 'TIAUSDT',
    'RUNE-USD': 'RUNEUSDT'
}


# Lista de tickers para los datos macro (con el nombre de tabla DXY corregido)
MACRO_TICKERS = {
    'SPY': 'macro_spy',
    '^VIX': 'macro_vix',
    '^TNX': 'macro_tnx',
    'DX-Y.NYB': 'macro_dx_y_nyb', # <-- NOMBRE CORREGIDO
    'GC=F': 'macro_gc',
    'CL=F': 'macro_cl'
}

# UNIVERSO DE 30 ACTIVOS CONFIGURADOS EN LA API
API_TICKERS = [
    'BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD', 'DOGE-USD', 
    'ADA-USD', 'AVAX-USD', 'SHIB-USD', 'DOT-USD', 'LINK-USD', 'TRX-USD', 
    'MATIC-USD', 'BCH-USD', 'ICP-USD', 'NEAR-USD', 'UNI-USD', 'LTC-USD', 
    'AAVE-USD', 'FTM-USD', 'XLM-USD', 'GRT-USD', 'RNDR-USD', 'HBAR-USD', 
    'FIL-USD', 'VET-USD', 'INJ-USD', 'OP-USD', 'TIA-USD', 'RUNE-USD'
]

# =============================================
# CONFIGURACIÓN CELERY + REDIS
# =============================================

# URL de conexión a Redis
REDIS_URL = "redis://localhost:6379/0"

# Configuración de Celery
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# Configuración adicional de Celery
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True

# Parámetros de producción
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutos máximo por tarea
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True

# Parámetro de riesgo para el trading (1% por defecto)
RISK_PER_TRADE = 0.01

# =============================================
# ALIAS PARA COMPATIBILIDAD CON SCRIPTS
# =============================================

TICKER_TO_BINANCE = TICKER_MAP_BINANCE