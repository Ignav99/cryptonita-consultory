#!/usr/bin/env python3
"""
Optimizador específico para repetidor WiFi
Objetivo: Conseguir rendimiento similar al router principal
"""

import subprocess
import time
import json
from datetime import datetime

class RepeaterOptimizer:
    def __init__(self):
        self.router_baseline = {
            'avg': 6.048,
            'min': 4.174,
            'max': 11.017,
            'stddev': 2.043
        }
        
    def scan_available_networks(self):
        """Escanear redes disponibles para identificar router principal vs repetidor"""
        print("📡 Escaneando redes disponibles...")
        
        try:
            result = subprocess.run([
                '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', 
                '-s'
            ], capture_output=True, text=True)
            
            networks = {}
            lines = result.stdout.split('\n')[1:]  # Skip header
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 3:
                        ssid = parts[0]
                        signal = parts[1]
                        channel = parts[2] if len(parts) > 2 else "?"
                        
                        # Identificar router principal vs repetidor
                        if 'EXT' in ssid or 'ext' in ssid:
                            network_type = "🔄 REPETIDOR"
                        else:
                            network_type = "🏠 ROUTER PRINCIPAL"
                        
                        networks[ssid] = {
                            'signal': signal,
                            'channel': channel,
                            'type': network_type
                        }
            
            return networks
            
        except Exception as e:
            print(f"❌ Error escaneando: {e}")
            return {}
    
    def test_network_performance(self, network_name, duration_tests=12):
        """Test de rendimiento en una red específica"""
        print(f"\n🔍 Testing: {network_name}")
        print(f"⏱️  Tests: {duration_tests} (cada 5 segundos)")
        print("-" * 60)
        
        results = []
        
        for i in range(duration_tests):
            try:
                result = subprocess.run(['ping', '-c', '3', '192.168.0.1'], 
                                      capture_output=True, text=True, timeout=10)
                
                for line in result.stdout.split('\n'):
                    if 'round-trip' in line:
                        parts = line.split('=')[1].strip().split('/')
                        avg_ping = float(parts[1])
                        stddev = float(parts[3].split()[0])
                        
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        
                        # Comparar con baseline del router principal
                        if avg_ping <= self.router_baseline['avg'] * 1.5:  # Dentro del 150% del router
                            status = "✅ BUENO"
                        elif avg_ping <= self.router_baseline['avg'] * 3:   # Dentro del 300%
                            status = "⚠️  REGULAR"
                        else:
                            status = "❌ MALO"
                        
                        print(f"{timestamp} | Test {i+1:2d}/{duration_tests} | {avg_ping:6.1f}ms (±{stddev:4.1f}) | {status}")
                        
                        results.append({
                            'ping': avg_ping,
                            'stddev': stddev,
                            'timestamp': timestamp,
                            'test_num': i+1
                        })
                        break
                        
            except Exception as e:
                print(f"{datetime.now().strftime('%H:%M:%S')} | Test {i+1:2d}/{duration_tests} | ERROR: {e}")
            
            time.sleep(5)
        
        return results
    
    def analyze_performance(self, results, network_name):
        """Analizar rendimiento y comparar con router principal"""
        if not results:
            print("❌ No hay datos para analizar")
            return {}
        
        pings = [r['ping'] for r in results]
        stddevs = [r['stddev'] for r in results]
        
        analysis = {
            'network': network_name,
            'avg': sum(pings) / len(pings),
            'min': min(pings),
            'max': max(pings),
            'stddev_avg': sum(stddevs) / len(stddevs),
            'consistency': len([p for p in pings if p < self.router_baseline['avg'] * 2]) / len(pings) * 100
        }
        
        print(f"\n📊 ANÁLISIS: {network_name}")
        print("=" * 60)
        print(f"Promedio:      {analysis['avg']:6.1f}ms")
        print(f"Rango:         {analysis['min']:6.1f} - {analysis['max']:6.1f}ms")
        print(f"Variabilidad:  ±{analysis['stddev_avg']:5.1f}ms")
        print(f"Consistencia:  {analysis['consistency']:5.1f}%")
        
        # Comparación con router principal
        print(f"\n🎯 COMPARACIÓN CON ROUTER PRINCIPAL:")
        print(f"Router principal: {self.router_baseline['avg']:.1f}ms (±{self.router_baseline['stddev']:.1f})")
        print(f"Esta red:         {analysis['avg']:.1f}ms (±{analysis['stddev_avg']:.1f})")
        
        factor = analysis['avg'] / self.router_baseline['avg']
        if factor <= 1.5:
            rating = "🟢 EXCELENTE"
        elif factor <= 3:
            rating = "🟡 ACEPTABLE"
        elif factor <= 5:
            rating = "🟠 REGULAR"
        else:
            rating = "🔴 PROBLEMÁTICO"
        
        print(f"Factor de rendimiento: {factor:.1f}x más lento - {rating}")
        
        return analysis
    
    def suggest_optimizations(self, analysis):
        """Sugerir optimizaciones específicas basadas en el análisis"""
        print(f"\n💡 RECOMENDACIONES PARA MEJORAR:")
        print("=" * 60)
        
        avg_ping = analysis['avg']
        consistency = analysis['consistency']
        
        if avg_ping > 50:
            print("🚨 LATENCIA ALTA:")
            print("   - Cambiar canal del repetidor (evitar 1, 6, 11 en 2.4GHz)")
            print("   - Verificar posición del repetidor")
            print("   - Usar banda 5GHz si está disponible")
            print("   - Reducir ancho de canal (de 80MHz a 40MHz)")
        
        if consistency < 50:
            print("📡 BAJA CONSISTENCIA:")
            print("   - Reiniciar repetidor regularmente (programado)")
            print("   - Verificar interferencias (microondas, otros WiFi)")
            print("   - Actualizar firmware del repetidor")
            print("   - Limitar dispositivos conectados simultáneamente")
        
        if analysis['stddev_avg'] > 20:
            print("📊 ALTA VARIABILIDAD:")
            print("   - Activar QoS en el repetidor")
            print("   - Priorizar tu dispositivo en configuración")
            print("   - Desactivar ahorro de energía en adaptador WiFi")
        
        # Configuraciones específicas para macOS
        print("🔧 OPTIMIZACIONES PARA TU MAC:")
        print("   - Usar 'networksetup -setairportpower en0 off && sleep 2 && networksetup -setairportpower en0 on'")
        print("   - Configurar DNS: networksetup -setdnsservers Wi-Fi 1.1.1.1 1.0.0.1")
        print("   - Limpiar cache: sudo dscacheutil -flushcache")
    
    def create_switching_script(self):
        """Crear script para cambiar entre router y repetidor fácilmente"""
        script_content = '''#!/bin/bash
# Script para cambiar entre router principal y repetidor

echo "🔄 CAMBIADOR DE RED WiFi"
echo "========================"

echo "Redes disponibles:"
echo "1. Router principal (mejor rendimiento)"
echo "2. Repetidor (mayor cobertura)"

read -p "Elige red (1-2): " choice

case $choice in
    1)
        echo "🏠 Conectando al router principal..."
        # Aquí irían los comandos específicos para tu router
        networksetup -setairportnetwork en0 "NOMBRE_ROUTER_PRINCIPAL"
        ;;
    2)
        echo "🔄 Conectando al repetidor..."
        # Aquí irían los comandos específicos para tu repetidor
        networksetup -setairportnetwork en0 "M.S.R._5G-EXT5G"
        ;;
    *)
        echo "❌ Opción inválida"
        exit 1
        ;;
esac

echo "⏳ Esperando conexión..."
sleep 10

echo "✅ Conexión completada"
echo "🔍 Test de conectividad:"
ping -c 3 192.168.0.1 | grep "round-trip"
'''
        
        with open('network_switcher.sh', 'w') as f:
            f.write(script_content)
        
        subprocess.run(['chmod', '+x', 'network_switcher.sh'])
        print("📝 Script creado: network_switcher.sh")
    
    def compare_networks(self):
        """Comparar rendimiento entre todas las redes disponibles"""
        networks = self.scan_available_networks()
        
        if not networks:
            print("❌ No se encontraron redes")
            return
        
        print("\n📊 REDES DETECTADAS:")
        for ssid, info in networks.items():
            print(f"   {info['type']} {ssid} - Señal: {info['signal']}, Canal: {info['channel']}")
        
        print(f"\n🎯 OBJETIVO: Conseguir rendimiento similar al router principal")
        print(f"   Baseline: {self.router_baseline['avg']:.1f}ms (±{self.router_baseline['stddev']:.1f})")
        
        # Identificar repetidor para testing
        repeater_networks = [ssid for ssid, info in networks.items() if 'EXT' in ssid]
        
        if repeater_networks:
            print(f"\n🔄 REPETIDOR DETECTADO: {repeater_networks[0]}")
            
            choice = input("\n¿Quieres testear el repetidor ahora? (y/n): ").lower()
            if choice == 'y':
                print(f"\n🔄 Conectando al repetidor {repeater_networks[0]}...")
                subprocess.run(['networksetup', '-setairportnetwork', 'en0', repeater_networks[0]])
                time.sleep(10)
                
                results = self.test_network_performance(repeater_networks[0])
                analysis = self.analyze_performance(results, repeater_networks[0])
                self.suggest_optimizations(analysis)

def main():
    optimizer = RepeaterOptimizer()
    
    print("🔧 OPTIMIZADOR DE REPETIDOR WiFi")
    print("="*50)
    print("Objetivo: Conseguir rendimiento del repetidor similar al router principal")
    print(f"Baseline router: {optimizer.router_baseline['avg']:.1f}ms")
    print()
    print("1. Escanear y comparar redes")
    print("2. Test solo repetidor")
    print("3. Crear script de cambio de red")
    print("4. Análisis completo")
    
    choice = input("\nElige opción (1-4): ").strip()
    
    if choice == "1":
        optimizer.compare_networks()
    elif choice == "2":
        results = optimizer.test_network_performance("Repetidor actual")
        analysis = optimizer.analyze_performance(results, "Repetidor")
        optimizer.suggest_optimizations(analysis)
    elif choice == "3":
        optimizer.create_switching_script()
    elif choice == "4":
        optimizer.compare_networks()
        optimizer.create_switching_script()
    else:
        print("Ejecutando análisis completo...")
        optimizer.compare_networks()

if __name__ == "__main__":
    main()
