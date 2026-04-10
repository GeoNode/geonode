#!/bin/bash
# ============================================================
# setup_external_datastore.sh
#
# Configura o GeoServer para conectar ao banco externo db_geo_prd
# Executa APOS o docker compose estar rodando e o GeoServer healthy
#
# Uso: bash setup_external_datastore.sh
#
# As credenciais sao lidas de variaveis de ambiente ou do arquivo
# .env_external (nao versionado). Veja .env_external.sample
# ============================================================

set -e

# Carregar credenciais do arquivo .env_external se existir
if [ -f ".env_external" ]; then
    set -a
    source .env_external
    set +a
fi

GEOSERVER_URL="${GEOSERVER_URL:-http://localhost:8080/geoserver}"
GS_USER="${GS_USER:-admin}"
GS_PASS="${GS_PASS:-geoserver}"

# Dados do banco externo
DB_HOST="${EXT_DB_HOST:?Variavel EXT_DB_HOST nao definida. Crie .env_external a partir de .env_external.sample}"
DB_PORT="${EXT_DB_PORT:-5432}"
DB_NAME="${EXT_DB_NAME:?Variavel EXT_DB_NAME nao definida}"
DB_SCHEMA="${EXT_DB_SCHEMA:-public}"
DB_USER="${EXT_DB_USER:?Variavel EXT_DB_USER nao definida}"
DB_PASS="${EXT_DB_PASS:?Variavel EXT_DB_PASS nao definida}"

WORKSPACE="${GS_WORKSPACE:-geonode}"
DATASTORE_NAME="${GS_DATASTORE_NAME:-${DB_NAME}}"

echo "============================================"
echo " Configurando datastore externo no GeoServer"
echo "============================================"

# 1. Verificar se o GeoServer esta acessivel
echo "[1/3] Verificando GeoServer..."
until curl -sf "${GEOSERVER_URL}/web/" > /dev/null 2>&1; do
    echo "  Aguardando GeoServer ficar disponivel..."
    sleep 5
done
echo "  GeoServer acessivel em ${GEOSERVER_URL}"

# 2. Verificar se o workspace 'geonode' existe (criado automaticamente pelo GeoNode)
echo "[2/3] Verificando workspace '${WORKSPACE}'..."
WS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -u "${GS_USER}:${GS_PASS}" \
    "${GEOSERVER_URL}/rest/workspaces/${WORKSPACE}.json")

if [ "$WS_STATUS" != "200" ]; then
    echo "  Workspace '${WORKSPACE}' nao encontrado. Criando..."
    curl -s -u "${GS_USER}:${GS_PASS}" \
        -XPOST "${GEOSERVER_URL}/rest/workspaces" \
        -H "Content-Type: application/json" \
        -d "{\"workspace\":{\"name\":\"${WORKSPACE}\"}}"
    echo "  Workspace criado."
else
    echo "  Workspace '${WORKSPACE}' ja existe."
fi

# 3. Criar datastore apontando para o banco externo
echo "[3/3] Criando datastore '${DATASTORE_NAME}'..."
DS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -u "${GS_USER}:${GS_PASS}" \
    "${GEOSERVER_URL}/rest/workspaces/${WORKSPACE}/datastores/${DATASTORE_NAME}.json")

if [ "$DS_STATUS" == "200" ]; then
    echo "  Datastore '${DATASTORE_NAME}' ja existe. Pulando criacao."
else
    curl -s -u "${GS_USER}:${GS_PASS}" \
        -XPOST "${GEOSERVER_URL}/rest/workspaces/${WORKSPACE}/datastores" \
        -H "Content-Type: application/json" \
        -d "{
            \"dataStore\": {
                \"name\": \"${DATASTORE_NAME}\",
                \"type\": \"PostGIS\",
                \"enabled\": true,
                \"connectionParameters\": {
                    \"entry\": [
                        {\"@key\": \"host\", \"\$\": \"${DB_HOST}\"},
                        {\"@key\": \"port\", \"\$\": \"${DB_PORT}\"},
                        {\"@key\": \"database\", \"\$\": \"${DB_NAME}\"},
                        {\"@key\": \"schema\", \"\$\": \"${DB_SCHEMA}\"},
                        {\"@key\": \"user\", \"\$\": \"${DB_USER}\"},
                        {\"@key\": \"passwd\", \"\$\": \"${DB_PASS}\"},
                        {\"@key\": \"dbtype\", \"\$\": \"postgis\"},
                        {\"@key\": \"Expose primary keys\", \"\$\": \"true\"},
                        {\"@key\": \"validate connections\", \"\$\": \"true\"},
                        {\"@key\": \"max connections\", \"\$\": \"10\"},
                        {\"@key\": \"min connections\", \"\$\": \"1\"}
                    ]
                }
            }
        }"
    echo ""
    echo "  Datastore '${DATASTORE_NAME}' criado com sucesso!"
fi

echo ""
echo "============================================"
echo " Configuracao concluida!"
echo ""
echo " GeoServer:  ${GEOSERVER_URL}/web/"
echo "   Login:    ${GS_USER} / ${GS_PASS}"
echo ""
echo " Datastore:  ${DATASTORE_NAME}"
echo "   Host:     ${DB_HOST}:${DB_PORT}"
echo "   Database: ${DB_NAME}"
echo "   Schema:   ${DB_SCHEMA}"
echo ""
echo " Proximo passo:"
echo "   1. Acesse ${GEOSERVER_URL}/web/"
echo "   2. Va em Layers > Add a new layer"
echo "   3. Selecione '${WORKSPACE}:${DATASTORE_NAME}'"
echo "   4. Publique as tabelas desejadas do db_geo_prd"
echo "   5. As camadas publicadas aparecerao no GeoNode"
echo "============================================"
