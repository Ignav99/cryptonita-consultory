#!/bin/bash
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
