#!/bin/bash
# ============================================================
# status.sh - Verifica o estado de todos os servicos GeoNode
# Uso: bash status.sh
# ============================================================

echo "============================================"
echo " Status do ambiente GeoNode"
echo " $(date)"
echo "============================================"
echo ""

echo "[Containers]"
docker ps --format "  {{.Names}}\t{{.Status}}" --filter "label=com.docker.compose.project=geonode" 2>/dev/null || echo "  Docker nao esta rodando"
echo ""

echo "[Conectividade]"
# GeoNode
if curl -sf "http://localhost/" > /dev/null 2>&1; then
    echo "  GeoNode (http://localhost/)          OK"
else
    echo "  GeoNode (http://localhost/)          FALHA"
fi

# GeoServer
if curl -sf "http://localhost:8080/geoserver/ows" > /dev/null 2>&1; then
    echo "  GeoServer (:8080/geoserver/ows)      OK"
else
    echo "  GeoServer (:8080/geoserver/ows)      FALHA"
fi

# DB local
if docker exec db4geonode pg_isready -U postgres > /dev/null 2>&1; then
    echo "  DB local (db4geonode)                OK"
else
    echo "  DB local (db4geonode)                FALHA"
fi

echo ""
echo "[Datastore externo]"
DS=$(docker exec geoserver4geonode curl -s -o /dev/null -w "%{http_code}" \
    -u "admin:geoserver" \
    "http://localhost:8080/geoserver/rest/workspaces/geonode/datastores/db_geo_prd.json" 2>/dev/null)
if [ "$DS" == "200" ]; then
    echo "  db_geo_prd no GeoServer              OK"
    LAYERS=$(docker exec geoserver4geonode curl -s -u "admin:geoserver" \
        "http://localhost:8080/geoserver/rest/workspaces/geonode/datastores/db_geo_prd/featuretypes.json" 2>/dev/null \
        | python3 -c "import sys,json; d=json.load(sys.stdin); ft=d.get('featureTypes',{}).get('featureType',[]); print(f'  Camadas publicadas: {len(ft)}')" 2>/dev/null)
    echo "$LAYERS"
else
    echo "  db_geo_prd no GeoServer              NAO CONFIGURADO"
fi

echo ""
echo "[Celery Beat]"
BEAT=$(docker exec celery4geonode python3 -c "
from geonode.settings import CELERY_BEAT_SCHEDULE
s = CELERY_BEAT_SCHEDULE.get('sync-geoserver-layers', {})
print(f\"  Task: {s.get('task','N/A')}\")
print(f\"  Intervalo: {s.get('schedule','N/A')}s\")
print(f\"  Store: {s.get('kwargs',{}).get('store','N/A')}\")
" 2>/dev/null)
if [ -n "$BEAT" ]; then
    echo "$BEAT"
else
    echo "  Celery Beat nao esta acessivel"
fi

echo ""
echo "============================================"
