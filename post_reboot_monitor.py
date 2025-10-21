#!/usr/bin/env python3
"""
Monitor específico para verificar mejoras post-reinicio del repetidor
"""

import subprocess
import time
from datetime import datetime

def test_stability(duration_minutes=5):
    """Test de estabilidad post-reinicio"""
    print(f"📊 Test de estabilidad post-reinicio ({duration_minutes} minutos)")
    print("Objetivo: Verificar si el reinicio solucionó los picos de latencia")
    print("-" * 70)
    
    results = []
    high_latency_count = 0
    
    tests = duration_minutes * 4  # Test cada 15 segundos
    
    for i in range(tests):
        try:
            # Test al router
            result = subprocess.run(['ping', '-c', '3', '192.168.0.1'], 
                                  capture_output=True, text=True, timeout=10)
            
            # Extraer latencia promedio
            for line in result.stdout.split('\n'):
                if 'round-trip' in line:
                    avg_ping = float(line.split('=')[1].split('/')[1])
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    
                    # Clasificar resultado
                    if avg_ping < 10:
                        status = "✅ EXCELENTE"
                    elif avg_ping < 25:
                        status = "✅ BUENO    "
                    elif avg_ping < 50:
                        status = "⚠️  REGULAR  "
                    else:
                        status = "❌ PROBLEMÁTICO"
                        high_latency_count += 1
                    
                    print(f"{timestamp} | Test {i+1:2d}/{tests} | {avg_ping:6.1f}ms | {status}")
                    
                    results.append({
                        'test': i+1,
                        'ping': avg_ping,
                        'timestamp': timestamp,
                        'status': status
                    })
                    break
        except:
            print(f"{datetime.now().strftime('%H:%M:%S')} | Test {i+1:2d}/{tests} | ERROR  | ❌ SIN RESPUESTA")
            high_latency_count += 1
        
        time.sleep(15)  # Test cada 15 segundos
    
    # Análisis final
    if results:
        pings = [r['ping'] for r in results]
        avg_ping = sum(pings) / len(pings)
        max_ping = max(pings)
        min_ping = min(pings)
        
        print("\n" + "="*70)
        print("📈 ANÁLISIS POST-REINICIO")
        print("="*70)
        print(f"Promedio: {avg_ping:.1f}ms")
        print(f"Mínimo:   {min_ping:.1f}ms")
        print(f"Máximo:   {max_ping:.1f}ms")
        print(f"Tests problemáticos: {high_latency_count}/{len(results)} ({high_latency_count/len(results)*100:.1f}%)")
        
        # Comparación con resultados anteriores
        print(f"\n📊 COMPARACIÓN:")
        print(f"ANTES del reinicio:")
        print(f"   - Promedio: 68.2ms")
        print(f"   - Máximo: 625.2ms")
        print(f"   - Estabilidad: 30%")
        print(f"\nDESPUÉS del reinicio:")
        print(f"   - Promedio: {avg_ping:.1f}ms")
        print(f"   - Máximo: {max_ping:.1f}ms")
        print(f"   - Estabilidad: {(1-high_latency_count/len(results))*100:.1f}%")
        
        # Evaluación de mejora
        if avg_ping < 20 and max_ping < 100:
            print(f"\n🎉 ¡MEJORA SIGNIFICATIVA! El reinicio funcionó.")
        elif avg_ping < 40:
            print(f"\n✅ Mejora moderada. Monitorea si se mantiene.")
        else:
            print(f"\n⚠️  Mejora mínima. El problema puede ser más profundo.")
            print("   Considera:")
            print("   - Verificar firmware del repetidor")
            print("   - Cambiar canal WiFi")
            print("   - Evaluar reemplazo del repetidor")

def quick_comparison():
    """Comparación rápida antes/después"""
    print("⚡ COMPARACIÓN RÁPIDA (30 segundos)")
    print("-" * 40)
    
    for i in range(6):
        try:
            result = subprocess.run(['ping', '-c', '2', '192.168.0.1'], 
                                  capture_output=True, text=True, timeout=8)
            
            for line in result.stdout.split('\n'):
                if 'round-trip' in line:
                    avg_ping = float(line.split('=')[1].split('/')[1])
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    
                    if avg_ping < 10:
                        emoji = "🟢"
                    elif avg_ping < 30:
                        emoji = "🟡"
                    else:
                        emoji = "🔴"
                    
                    print(f"{timestamp} | {avg_ping:5.1f}ms {emoji}")
                    break
        except:
            print(f"{datetime.now().strftime('%H:%M:%S')} | ERROR 🔴")
        
        time.sleep(5)

def main():
    print("🔄 Monitor Post-Reinicio del Repetidor")
    print("="*50)
    print("1. Test rápido (30 segundos)")
    print("2. Test completo (5 minutos)")
    print("3. Solo comparación")
    
    choice = input("\nElige opción (1-3): ").strip()
    
    if choice == "1":
        quick_comparison()
    elif choice == "2":
        test_stability(5)
    elif choice == "3":
        print("\n📊 RESUMEN DE TU SITUACIÓN ACTUAL:")
        print("ANTES del diagnóstico:")
        print("   - Variabilidad extrema: 5ms → 625ms")
        print("   - Solo 30% del tiempo estable")
        print("   - Picos cada ~3 minutos")
        print("\nRECOMENDACIÓN: Reinicia el repetidor y ejecuta test completo")
    else:
        print("Ejecutando test rápido por defecto...")
        quick_comparison()

if __name__ == "__main__":
    main()
