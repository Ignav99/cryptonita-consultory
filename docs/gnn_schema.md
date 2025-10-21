# 🗄️ CRYPTONITA GNN - DATABASE SCHEMA

**Fecha de creación**: 2025-08-04 09:49:50
**Cobertura temporal**: 2019-07-30 - 2025-07-30
**Total de activos**: 18

## 📊 Distribución de Activos

### Training Set (12 activos)
BTC-USD, ETH-USD, BNB-USD, ADA-USD, SOL-USD, AVAX-USD, DOT-USD, LINK-USD, UNI-USD, AAVE-USD, MATIC-USD, LTC-USD

### Validation Set (3 activos)  
XRP-USD, DOGE-USD, ATOM-USD

### Test Set (3 activos)
ALGO-USD, FTM-USD, NEAR-USD

## 🗂️ Estructura de Tablas

### 1. gnn_crypto_prices
**Descripción**: Datos OHLCV de criptomonedas - Nodos principales del grafo GNN
- Precios diarios de 18 activos crypto
- Período: 6 años completos
- Claves: ticker, date (UNIQUE)

### 2. gnn_funding_rates  
**Descripción**: Funding rates de futuros perpetuos - Información para edges del grafo
- Tasas de financiación cada 8 horas de Binance
- Open interest (cuando disponible)
- Índices: ticker, date

### 3. gnn_macro_indicators
**Descripción**: Indicadores macroeconómicos - Contexto global del grafo GNN
- SPY, VIX, TNX, DXY, GOLD, OIL
- Datos OHLCV diarios de Yahoo Finance
- Claves: indicator_symbol, date (UNIQUE)

### 4. gnn_technical_features
**Descripción**: Features técnicos calculados para cada activo - Node features del GNN
- Returns múltiples horizontes (1d, 3d, 7d, 30d)
- Indicadores técnicos (RSI, MACD, EMAs, Bollinger)
- Volatilidad y momentum
- Claves: ticker, date (UNIQUE)

### 5. gnn_correlations
**Descripción**: Correlaciones dinámicas entre activos - Edge features del GNN
- Correlaciones de precios y volatilidad
- Cointegración y betas
- Diferenciales de funding rates
- Constraint: ticker_a < ticker_b (evitar duplicados)

### 6. gnn_market_regime
**Descripción**: Régimen de mercado y contexto global - Global features del GNN
- Dominancia BTC/ETH
- Fear & Greed Index
- Condiciones de liquidez y volatilidad
- Métricas agregadas diarias

### 7. gnn_trade_log
**Descripción**: Log de operaciones del sistema GNN - Para análisis de performance
- Registro de trades (backtest y live)
- P&L y métricas de performance
- Contexto del modelo y features utilizadas

## 🎯 Uso del Schema para GNN

### Node Features
- **Precios base**: gnn_crypto_prices
- **Features técnicos**: gnn_technical_features
- **Embeddings de ticker**: Calculados dinámicamente

### Edge Features  
- **Correlaciones**: gnn_correlations
- **Funding differentials**: Calculados desde gnn_funding_rates
- **Flujos de volumen**: Relaciones entre volúmenes

### Global Features
- **Macro contexto**: gnn_macro_indicators
- **Régimen de mercado**: gnn_market_regime
- **Condiciones de liquidez**: Agregados de funding y volumen

## 🚀 Próximos Pasos

1. ✅ **Schema Creado** - Base de datos preparada
2. 🔄 **Ingesta de Datos** - Llenar tablas con 6 años de datos
3. 🧠 **Feature Engineering** - Calcular correlaciones y features técnicos
4. 🏗️ **Construcción del Grafo** - Crear estructura para GNN
5. 📈 **Modelo GNN** - Implementar arquitectura específica financiera

---
*Documentación generada automáticamente por Cryptonita GNN Database Setup*
