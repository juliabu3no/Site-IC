from pathlib import Path
import json
import numpy as np
import pandas as pd
import geopandas as gpd

# ============================================================
# CONFIGURAÇÃO
# ============================================================
BASE_DIR = Path(__file__).resolve().parents[1]
PASTA_DADOS = BASE_DIR / "dados_local"
ARQUIVO_SAIDA = BASE_DIR / "api" / "data" / "atendimento.json"
MAX_CANDIDATOS = 25

TIPOS_SORO = [
    "Botrópico",
    "Crotálico",
    "Elapídico",
    "Laquético",
    "Loxoscélico",
    "Fonêutrico",
    "Escorpiônico",
    "Lonômico",
]

def nome_coluna(df, opcoes, obrigatoria=False):
    for coluna in opcoes:
        if coluna in df.columns:
            return coluna
    if obrigatoria:
        raise KeyError(f"Nenhuma destas colunas foi encontrada: {opcoes}")
    return None

def texto(valor):
    if pd.isna(valor):
        return None
    valor = str(valor).strip()
    return valor if valor else None

# ============================================================
# 1. LEITURA
# ============================================================
print("[1/6] Lendo bases...")
gdf_munic = gpd.read_file(PASTA_DADOS / "divisoes.gpkg")
gdf_postos = gpd.read_file(PASTA_DADOS / "postos_atualizados.gpkg")
df_dist = pd.read_csv(PASTA_DADOS / "distancias_atualizadas.csv", index_col=0)

# ============================================================
# 2. VALIDAÇÃO
# ============================================================
print("[2/6] Validando dados...")
for coluna in ["Codigo Municipio", "Municipio"]:
    if coluna not in gdf_munic.columns:
        raise ValueError(f"Coluna ausente em divisoes.gpkg: {coluna}")

for coluna in ["Codigo Municipio", "Tem Soro", *TIPOS_SORO]:
    if coluna not in gdf_postos.columns:
        raise ValueError(f"Coluna ausente em postos_atualizados.gpkg: {coluna}")

gdf_postos[TIPOS_SORO] = gdf_postos[TIPOS_SORO].fillna(0).astype(int)
df_dist = df_dist.apply(pd.to_numeric, errors="coerce")
distancias = df_dist.to_numpy(dtype=float)

if distancias.shape[0] != len(gdf_munic):
    raise ValueError(
        f"A matriz tem {distancias.shape[0]} linhas, mas divisoes.gpkg tem "
        f"{len(gdf_munic)} municípios."
    )

if distancias.shape[1] != len(gdf_postos):
    raise ValueError(
        f"A matriz tem {distancias.shape[1]} colunas, mas postos_atualizados.gpkg "
        f"tem {len(gdf_postos)} postos."
    )

postos_ativos = gdf_postos[gdf_postos["Tem Soro"].eq(1)].copy()
indices_originais = postos_ativos.index.to_numpy()

# ============================================================
# 3. COLUNAS DOS POSTOS
# ============================================================
print("[3/6] Preparando postos...")
col_nome = nome_coluna(
    postos_ativos,
    ["Nome Posto", "Nome", "Estabelecimento", "Unidade de Saúde", "Unidade"],
)
col_endereco = nome_coluna(
    postos_ativos,
    ["Endereço", "Endereco", "endereco"],
)
col_logradouro = nome_coluna(
    postos_ativos,
    ["Logradouro", "logradouro", "Rua"],
)
col_numero = nome_coluna(
    postos_ativos,
    ["Número", "Numero", "numero"],
)
col_bairro = nome_coluna(
    postos_ativos,
    ["Bairro", "bairro"],
)
col_telefone = nome_coluna(
    postos_ativos,
    ["Telefone", "telefone", "Fone", "fone"],
)
col_lat = nome_coluna(
    postos_ativos,
    ["Latitude", "latitude", "LATITUDE"],
)
col_lon = nome_coluna(
    postos_ativos,
    ["Longitude", "longitude", "LONGITUDE"],
)

postos_wgs84 = None
if (
    col_lat is None
    or col_lon is None
    or postos_ativos[col_lat].isna().any()
    or postos_ativos[col_lon].isna().any()
):
    if postos_ativos.crs is None:
        raise ValueError(
            "Há postos sem latitude/longitude e postos_atualizados.gpkg não possui CRS."
        )
    postos_wgs84 = postos_ativos.to_crs(epsg=4326)

postos = []
indice_original_para_id = {}

for id_local, (indice_original, posto) in enumerate(postos_ativos.iterrows()):
    if (
        col_lat is not None
        and col_lon is not None
        and pd.notna(posto[col_lat])
        and pd.notna(posto[col_lon])
    ):
        latitude = float(posto[col_lat])
        longitude = float(posto[col_lon])
    else:
        geometria = postos_wgs84.loc[indice_original].geometry
        if geometria is None or geometria.is_empty:
            continue
        ponto = geometria if geometria.geom_type == "Point" else geometria.centroid
        latitude = float(ponto.y)
        longitude = float(ponto.x)

    endereco = texto(posto[col_endereco]) if col_endereco else None
    if not endereco:
        partes = []
        for coluna in [col_logradouro, col_numero, col_bairro]:
            if coluna:
                valor = texto(posto[coluna])
                if valor:
                    partes.append(valor)
        endereco = ", ".join(partes) if partes else None

    indice_original_para_id[int(indice_original)] = id_local
    postos.append({
        "id": id_local,
        "indice_original": int(indice_original),
        "nome": texto(posto[col_nome]) if col_nome else "PESA",
        "codigo_municipio": int(posto["Codigo Municipio"]),
        "municipio": texto(posto["Municipio"]) if "Municipio" in postos_ativos.columns else None,
        "endereco": endereco,
        "telefone": texto(posto[col_telefone]) if col_telefone else None,
        "latitude": latitude,
        "longitude": longitude,
        "soros": [soro for soro in TIPOS_SORO if int(posto[soro]) == 1],
    })

ids_validos = {posto["id"] for posto in postos}

# ============================================================
# 4. MUNICÍPIOS E CENTROIDES
# ============================================================
print("[4/6] Preparando municípios...")
if gdf_munic.crs is None:
    raise ValueError("divisoes.gpkg não possui CRS.")

gdf_centroides = gdf_munic.to_crs(epsg=31983).copy()
gdf_centroides["geometry"] = gdf_centroides.geometry.centroid
gdf_centroides = gdf_centroides.to_crs(epsg=4326)

municipios = []

for i, municipio in gdf_munic.iterrows():
    centroide = gdf_centroides.iloc[i].geometry
    linha = distancias[i]

    candidatos_geral = []
    for indice_original in indices_originais[np.argsort(linha[indices_originais])]:
        id_local = indice_original_para_id.get(int(indice_original))
        if id_local in ids_validos:
            candidatos_geral.append(id_local)
        if len(candidatos_geral) >= MAX_CANDIDATOS:
            break

    candidatos_por_soro = {}
    for soro in TIPOS_SORO:
        indices_soro = postos_ativos[postos_ativos[soro].eq(1)].index.to_numpy()
        ordenados = indices_soro[np.argsort(linha[indices_soro])]
        candidatos = []
        for indice_original in ordenados:
            id_local = indice_original_para_id.get(int(indice_original))
            if id_local in ids_validos:
                candidatos.append(id_local)
            if len(candidatos) >= MAX_CANDIDATOS:
                break
        candidatos_por_soro[soro] = candidatos

    municipios.append({
        "codigo_municipio": int(municipio["Codigo Municipio"]),
        "municipio": str(municipio["Municipio"]),
        "latitude": float(centroide.y),
        "longitude": float(centroide.x),
        "candidatos_geral": candidatos_geral,
        "candidatos_por_soro": candidatos_por_soro,
    })

# ============================================================
# 5. JSON
# ============================================================
print("[5/6] Montando JSON...")
dados = {
    "tipos_soro": TIPOS_SORO,
    "max_candidatos": MAX_CANDIDATOS,
    "postos": postos,
    "municipios": municipios,
}

# ============================================================
# 6. SALVAMENTO
# ============================================================
print("[6/6] Salvando...")
ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)
with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as arquivo:
    json.dump(dados, arquivo, ensure_ascii=False, separators=(",", ":"))

tamanho_mb = ARQUIVO_SAIDA.stat().st_size / (1024 * 1024)
print(f"Concluído: {ARQUIVO_SAIDA}")
print(f"PESAs: {len(postos)}")
print(f"Municípios: {len(municipios)}")
print(f"Tamanho: {tamanho_mb:.2f} MB")
