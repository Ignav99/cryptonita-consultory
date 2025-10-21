# src/production/exchange_connector.py (VERSIÓN MEJORADA PARA BINANCE)
import ccxt
import logging
import sys
import os
import time
from typing import Optional, Dict, Any, List
from decimal import Decimal
import asyncio

# --- Configuración ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config import settings

class BinanceConnectorError(Exception):
    """Excepción personalizada para errores del conector"""
    pass

class BinanceConnector:
    def __init__(self, testnet: bool = False):
        """
        Inicializa el conector de Binance
        
        Args:
            testnet (bool): Si True, usa el testnet de Binance
        """
        self.testnet = testnet
        self.exchange = None
        self.last_request_time = 0
        self.rate_limit_delay = 0.1  # 100ms entre requests para evitar rate limits
        
        self._initialize_exchange()
    
    def _initialize_exchange(self):
        """Inicializa la conexión con el exchange"""
        try:
            config = {
                'apiKey': settings.EXCHANGE_API_KEY,
                'secret': settings.EXCHANGE_API_SECRET,
                'options': { 
                    'defaultType': 'future',
                    'adjustForTimeDifference': True  # Ajusta automáticamente diferencias de tiempo
                },
                'enableRateLimit': True,  # Habilita rate limiting automático
                'rateLimit': 100,  # 100ms entre requests
            }
            
            if self.testnet:
                config['sandbox'] = True
                config['urls'] = {
                    'api': {
                        'public': 'https://testnet.binancefuture.com/fapi/v1',
                        'private': 'https://testnet.binancefuture.com/fapi/v1',
                    }
                }
                logging.info("🔧 Conectando a Binance TESTNET...")
            else:
                logging.info("🚀 Conectando a Binance PRODUCCIÓN...")
            
            self.exchange = ccxt.binance(config)
            
            # Verificar conectividad
            self._test_connection()
            
            env_type = "TESTNET" if self.testnet else "PRODUCCIÓN"
            logging.info(f"✅ Conexión con Binance {env_type} establecida correctamente")
            
        except Exception as e:
            logging.error(f"❌ Error al inicializar la conexión: {e}")
            raise BinanceConnectorError(f"No se pudo conectar a Binance: {e}")
    
    def _test_connection(self):
        """Prueba la conexión con una llamada básica"""
        try:
            self.exchange.fetch_balance()
            return True
        except ccxt.AuthenticationError as e:
            raise BinanceConnectorError(f"Error de autenticación: {e}")
        except ccxt.NetworkError as e:
            raise BinanceConnectorError(f"Error de red: {e}")
        except Exception as e:
            raise BinanceConnectorError(f"Error de conexión: {e}")
    
    def _rate_limit_wait(self):
        """Implementa rate limiting manual"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        
        self.last_request_time = time.time()
    
    def _handle_request(self, func, *args, **kwargs):
        """Wrapper para manejar requests con rate limiting y retry logic"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                self._rate_limit_wait()
                return func(*args, **kwargs)
                
            except ccxt.RateLimitExceeded as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    logging.warning(f"⚠️ Rate limit excedido, esperando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logging.error(f"❌ Rate limit excedido después de {max_retries} intentos")
                    raise BinanceConnectorError(f"Rate limit excedido: {e}")
                    
            except ccxt.NetworkError as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    logging.warning(f"⚠️ Error de red, reintentando en {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logging.error(f"❌ Error de red después de {max_retries} intentos")
                    raise BinanceConnectorError(f"Error de red: {e}")
                    
            except Exception as e:
                logging.error(f"❌ Error inesperado: {e}")
                raise BinanceConnectorError(f"Error inesperado: {e}")
    
    def get_balance(self, currency: str = 'USDT') -> Optional[float]:
        """
        Obtiene el balance de una moneda específica
        
        Args:
            currency (str): Moneda a consultar (default: USDT)
            
        Returns:
            float: Balance disponible o None si hay error
        """
        if not self.exchange:
            logging.error("❌ Exchange no inicializado")
            return None
            
        try:
            balance_data = self._handle_request(
                self.exchange.fetch_balance,
                params={'type': 'future'}
            )
            
            total_balance = balance_data['total'].get(currency, 0.0)
            free_balance = balance_data['free'].get(currency, 0.0)
            used_balance = balance_data['used'].get(currency, 0.0)
            
            logging.info(f"💰 Balance {currency} - Total: {total_balance}, Libre: {free_balance}, Usado: {used_balance}")
            return float(total_balance)
            
        except Exception as e:
            logging.error(f"❌ Error al obtener balance de {currency}: {e}")
            return None
    
    def get_all_balances(self) -> Optional[Dict[str, Dict[str, float]]]:
        """
        Obtiene todos los balances de la cuenta
        
        Returns:
            dict: Diccionario con todos los balances o None si hay error
        """
        if not self.exchange:
            return None
            
        try:
            balance_data = self._handle_request(
                self.exchange.fetch_balance,
                params={'type': 'future'}
            )
            
            # Filtrar solo las monedas con balance > 0
            filtered_balances = {}
            for currency, amounts in balance_data['total'].items():
                if float(amounts) > 0:
                    filtered_balances[currency] = {
                        'total': float(balance_data['total'].get(currency, 0)),
                        'free': float(balance_data['free'].get(currency, 0)),
                        'used': float(balance_data['used'].get(currency, 0))
                    }
            
            return filtered_balances
            
        except Exception as e:
            logging.error(f"❌ Error al obtener todos los balances: {e}")
            return None
    
    def get_position(self, symbol: str) -> Dict[str, Any]:
        """
        Obtiene información detallada de la posición para un símbolo
        
        Args:
            symbol (str): Par de trading (ej: 'BTC/USDT')
            
        Returns:
            dict: Información detallada de la posición
        """
        if not self.exchange:
            return {'size': 0.0, 'side': 'none', 'unrealized_pnl': 0.0, 'percentage': 0.0}
            
        try:
            positions = self._handle_request(
                self.exchange.fetch_positions,
                [symbol]
            )
            
            for position in positions:
                if position['symbol'] == symbol and position['contracts'] != 0:
                    return {
                        'size': float(position.get('contracts', 0.0)),
                        'side': position.get('side', 'none'),
                        'unrealized_pnl': float(position.get('unrealizedPnl', 0.0)),
                        'percentage': float(position.get('percentage', 0.0)),
                        'entry_price': float(position.get('entryPrice', 0.0)),
                        'mark_price': float(position.get('markPrice', 0.0)),
                        'notional': float(position.get('notional', 0.0))
                    }
            
            return {'size': 0.0, 'side': 'none', 'unrealized_pnl': 0.0, 'percentage': 0.0}
            
        except Exception as e:
            logging.error(f"❌ Error al obtener posición de {symbol}: {e}")
            return {'size': 0.0, 'side': 'none', 'unrealized_pnl': 0.0, 'percentage': 0.0}
    
    def get_all_positions(self) -> List[Dict[str, Any]]:
        """
        Obtiene todas las posiciones activas
        
        Returns:
            list: Lista de posiciones activas
        """
        if not self.exchange:
            return []
            
        try:
            all_positions = self._handle_request(self.exchange.fetch_positions)
            
            active_positions = []
            for position in all_positions:
                if position['contracts'] != 0:
                    active_positions.append({
                        'symbol': position['symbol'],
                        'size': float(position.get('contracts', 0.0)),
                        'side': position.get('side', 'none'),
                        'unrealized_pnl': float(position.get('unrealizedPnl', 0.0)),
                        'percentage': float(position.get('percentage', 0.0)),
                        'entry_price': float(position.get('entryPrice', 0.0)),
                        'mark_price': float(position.get('markPrice', 0.0))
                    })
            
            return active_positions
            
        except Exception as e:
            logging.error(f"❌ Error al obtener todas las posiciones: {e}")
            return []
    
    def get_ticker(self, symbol: str) -> Optional[Dict[str, float]]:
        """
        Obtiene información del ticker para un símbolo
        
        Args:
            symbol (str): Par de trading
            
        Returns:
            dict: Información del ticker o None si hay error
        """
        if not self.exchange:
            return None
            
        try:
            ticker = self._handle_request(self.exchange.fetch_ticker, symbol)
            
            return {
                'symbol': ticker['symbol'],
                'last': float(ticker['last']),
                'bid': float(ticker['bid']),
                'ask': float(ticker['ask']),
                'high': float(ticker['high']),
                'low': float(ticker['low']),
                'volume': float(ticker['baseVolume']),
                'change': float(ticker['change']),
                'percentage': float(ticker['percentage'])
            }
            
        except Exception as e:
            logging.error(f"❌ Error al obtener ticker de {symbol}: {e}")
            return None
    
    def health_check(self) -> bool:
        """
        Verifica si la conexión está funcionando correctamente
        
        Returns:
            bool: True si la conexión es saludable
        """
        try:
            if not self.exchange:
                return False
                
            # Prueba con una llamada ligera
            self._handle_request(self.exchange.fetch_status)
            return True
            
        except Exception as e:
            logging.error(f"❌ Health check falló: {e}")
            return False
    
    def reconnect(self):
        """Reestablece la conexión con el exchange"""
        logging.info("🔄 Reestableciendo conexión...")
        self._initialize_exchange()

def main():
    """Función principal para pruebas"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 === Iniciando pruebas del conector Binance ===")
    
    try:
        # Cambiar a testnet=True para pruebas en testnet
        connector = BinanceConnector(testnet=False)
        
        # Health check
        if not connector.health_check():
            print("❌ Health check falló")
            return
        
        print("✅ Health check exitoso")
        
        # Obtener balance de USDT
        usdt_balance = connector.get_balance('USDT')
        if usdt_balance is not None:
            print(f"💰 Balance USDT: {usdt_balance}")
        
        # Obtener todos los balances
        all_balances = connector.get_all_balances()
        if all_balances:
            print(f"💼 Balances activos: {len(all_balances)} monedas")
            for currency, balance_info in all_balances.items():
                print(f"   {currency}: {balance_info}")
        
        # Obtener posición de BTC
        btc_position = connector.get_position('BTC/USDT')
        print(f"📊 Posición BTC/USDT: {btc_position}")
        
        # Obtener todas las posiciones activas
        active_positions = connector.get_all_positions()
        if active_positions:
            print(f"📈 Posiciones activas: {len(active_positions)}")
            for pos in active_positions:
                print(f"   {pos['symbol']}: {pos['side']} {pos['size']} (PnL: {pos['unrealized_pnl']})")
        else:
            print("📈 No hay posiciones activas")
        
        # Obtener ticker de BTC
        btc_ticker = connector.get_ticker('BTC/USDT')
        if btc_ticker:
            print(f"💹 BTC/USDT - Precio: {btc_ticker['last']}, Cambio: {btc_ticker['percentage']:.2f}%")
        
        print("✅ Todas las pruebas completadas exitosamente")
        
    except BinanceConnectorError as e:
        print(f"❌ Error del conector: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == '__main__':
    main()