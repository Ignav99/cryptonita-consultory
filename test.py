#!/usr/bin/env python3
"""
Comparación directa entre router principal y repetidor
"""

import subprocess
import time
from datetime import datetime

def test_network_performance(network_name, duration_minutes=3):
    """Test de rendimiento en una red específica"""
    print(f"📡 Testing network: {network_name}")
    print(f"⏱️  Duration: {duration_minutes} minutes")
    print("-" * 60)
    
    results = []
    tests = duration_minutes * 4  # Test cada 15 segundos
    
    for i in range(tests):
        try:
            # Test al gateway (router)
            result = subprocess.run(['ping', '-c', '3', '192.168.0.1'], 
                                  capture_output=True, text=True, timeout=10)
            
            # Extraer latencia
            for line in result.stdout.split('\n'):
                if 'round-trip' in line:
                    parts = line.split('=')[1].strip().split('/')
                    avg_ping = float(parts[1])
                    stddev = float(parts[3].split()[0])
                    
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    
                    # Clasificar
                    if avg_ping < 5:
                        status = "🟢 EXCELENTE"
                    elif avg_ping < 15:
                        status = "🟡 BUENO"
                    elif avg_ping < 50:
                        status = "🟠 REGULAR"
                    else:
                        status = "🔴 MALO"
                    
                    print(f"{timestamp} | {avg_ping:6.1f}ms (±{stddev:4.1f}) | {status}")
                    
                    results.append({
                        'ping': avg_ping,
                        'stddev': stddev,
                        'timestamp': timestamp
                    })
                    break
        except Exception as e:
            print(f"{datetime.now().strftime('%H:%M:%S')} | ERROR: {e}")
        
        time.sleep(15)
    
    return results

def compare_networks():
    """Comparar rendimiento entre diferentes redes"""
    print("🔍 COMPARADOR DE REDES WIFI")
    print("="*50)
    
    # Mostrar redes disponibles
    print("📡 Buscando redes disponibles...")
    try:
        scan_result = subprocess.run([
            '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', 
            '-s'
        ], capture_output=True, text=True)
        
        print("\nRedes WiFi detectadas:")
        networks = []
        for line in scan_result.stdout.split('\n')[1:]:  # Skip header
            if line.strip():
                parts = line.split()
                if parts:
                    network_name = parts[0]
                    if network_name not in networks:
                        networks.append(network_name)
                        print(f"  - {network_name}")
        
        if not networks:
            print("❌ No se pudieron detectar redes")
            return
            
    except Exception as e:
        print(f"❌ Error escaneando redes: {e}")
        return
    
    print(f"\n📍 Red actual:")
    try:
        current = subprocess.run(['networksetup', '-getairportnetwork', 'en0'], 
                               capture_output=True, text=True)
        current_network = current.stdout.strip().split(': ')[-1]
        print(f"   {current_network}")
    except:
        current_network = "Desconocida"
    
    print(f"\n🎯 PLAN DE TESTING:")
    print(f"1. Test en red actual: {current_network}")
    print(f"2. Cambiar a router principal (si disponible)")
    print(f"3. Comparar resultados")
    
    # Test red actual
    print(f"\n" + "="*60)
    print(f"🔍 TEST 1: RED ACTUAL ({current_network})")
    print("="*60)
    
    current_results = test_network_performance(current_network, 3)
    
    if current_results:
        current_avg = sum(r['ping'] for r in current_results) / len(current_results)
        current_max = max(r['ping'] for r in current_results)
        current_min = min(r['ping'] for r in current_results)
        
        print(f"\n📊 RESUMEN RED ACTUAL:")
        print(f"   Promedio: {current_avg:.1f}ms")
        print(f"   Mínimo:   {current_min:.1f}ms")
        print(f"   Máximo:   {current_max:.1f}ms")
        print(f"   Tests:    {len(current_results)}")
    
    # Preguntar por cambio de red
    print(f"\n🔄 ¿Quieres cambiar a otra red para comparar?")
    print("Redes disponibles:")
    for i, network in enumerate(networks, 1):
        if network != current_network:
            print(f"   {i}. {network}")
    
    print("   0. No cambiar")
    
    try:
        choice = input("\nElige red (número): ").strip()
        if choice == "0":
            print("✅ Manteniendo red actual")
            return current_results
        
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(networks):
            target_network = networks[choice_idx]
            
            print(f"\n🔄 Cambiando a: {target_network}")
            subprocess.run(['networksetup', '-setairportnetwork', 'en0', target_network])
            
            print("⏳ Esperando conexión...")
            time.sleep(10)
            
            # Test nueva red
            print(f"\n" + "="*60)
            print(f"🔍 TEST 2: NUEVA RED ({target_network})")
            print("="*60)
            
            new_results = test_network_performance(target_network, 3)
            
            if new_results:
                new_avg = sum(r['ping'] for r in new_results) / len(new_results)
                new_max = max(r['ping'] for r in new_results)
                new_min = min(r['ping'] for r in new_results)
                
                print(f"\n" + "="*60)
                print(f"📊 COMPARACIÓN FINAL")
                print("="*60)
                print(f"RED ANTERIOR ({current_network}):")
                print(f"   Promedio: {current_avg:.1f}ms")
                print(f"   Rango:    {current_min:.1f} - {current_max:.1f}ms")
                
                print(f"\nNUEVA RED ({target_network}):")
                print(f"   Promedio: {new_avg:.1f}ms")
                print(f"   Rango:    {new_min:.1f} - {new_max:.1f}ms")
                
                improvement = current_avg - new_avg
                print(f"\n🎯 DIFERENCIA: {improvement:+.1f}ms")
                
                if improvement > 20:
                    print("🎉 ¡MEJORA SIGNIFICATIVA! Usa esta red.")
                elif improvement > 5:
                    print("✅ Mejora moderada. Esta red es mejor.")
                elif improvement < -20:
                    print("⚠️  Esta red es peor. Vuelve a la anterior.")
                else:
                    print("📊 Rendimiento similar.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def quick_network_scan():
    """Escaneo rápido de redes"""
    print("📡 ESCANEO RÁPIDO DE REDES")
    print("-" * 40)
    
    try:
        result = subprocess.run([
            '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', 
            '-s'
        ], capture_output=True, text=True)
        
        lines = result.stdout.split('\n')
        if len(lines) > 1:
            print("Redes encontradas:")
            for line in lines[1:10]:  # Primeras 10 redes
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        name = parts[0]
                        signal = parts[1] if len(parts) > 1 else "?"
                        print(f"  📶 {name} (señal: {signal})")
        else:
            print("❌ No se encontraron redes")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("📡 COMPARADOR DE RENDIMIENTO WIFI")
    print("="*50)
    print("1. Escaneo rápido de redes")
    print("2. Test completo con comparación")
    print("3. Solo test red actual")
    
    choice = input("\nElige opción (1-3): ").strip()
    
    if choice == "1":
        quick_network_scan()
    elif choice == "2":
        compare_networks()
    elif choice == "3":
        current_results = test_network_performance("Red actual", 3)
        if current_results:
            avg = sum(r['ping'] for r in current_results) / len(current_results)
            print(f"\n📊 Promedio: {avg:.1f}ms")
    else:
        print("Ejecutando escaneo rápido...")
        quick_network_scan()

if __name__ == "__main__":
    main()