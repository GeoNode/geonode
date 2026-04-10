#!/bin/bash
# ============================================================
# start_local.sh
#
# Script de inicializacao do ambiente local GeoNode
# Sobe toda a stack e configura o datastore externo
#
# Uso: bash start_local.sh
# ============================================================

set -e

echo "============================================"
echo " Iniciando stack GeoNode local"
echo "============================================"
echo ""

# 1. Subir a stack com docker compose
echo "[1/2] Subindo containers..."
docker compose -f docker-compose-local.yml up -d --build

echo ""
echo "  Aguardando servicos ficarem healthy..."
echo "  (isso pode levar alguns minutos na primeira vez)"
echo ""

# Aguardar GeoServer ficar pronto
echo "  Aguardando GeoServer..."
until curl -sf "http://localhost:8080/geoserver/web/" > /dev/null 2>&1; do
    sleep 10
    echo "    ..."
done
echo "  GeoServer: OK"

# Aguardar GeoNode/Nginx ficar pronto
echo "  Aguardando GeoNode..."
until curl -sf "http://localhost/" > /dev/null 2>&1; do
    sleep 10
    echo "    ..."
done
echo "  GeoNode: OK"

# 2. Configurar datastore externo
echo ""
echo "[2/2] Configurando datastore externo (db_geo_prd)..."
bash setup_external_datastore.sh

echo ""
echo "============================================"
echo " Ambiente pronto!"
echo ""
echo " GeoNode:    http://localhost/"
echo "   Admin:    admin / admin"
echo ""
echo " GeoServer:  http://localhost/geoserver/web/"
echo "   Login:    via OAuth2 (loga pelo GeoNode)"
echo ""
echo " DB local:   localhost:5434"
echo "   User:     postgres / postgres"
echo ""
echo " DB externo: 172.20.30.31:5432"
echo "   Database: db_geo_prd (schema: geonode)"
echo ""
echo " Sync automatico: a cada 120s (Celery Beat)"
echo "   Ajustar: GEOSERVER_SYNC_INTERVAL no .env"
echo ""
echo " Docs: ver SETUP_REFERENCE.txt"
echo "============================================"
