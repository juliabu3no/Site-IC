from pathlib import Path
import json
import pandas as pd
import geopandas as gpd
import gdown


# -------------------------
# CAMINHOS
# -------------------------

RAIZ = Path(__file__).resolve().parent.parent
PASTA_DATA = RAIZ / "public" / "data"

PASTA_DATA.mkdir(parents=True, exist_ok=True)

arquivo_dados = RAIZ / "dados.csv"
arquivo_geojson = RAIZ / "geojson_sp.json"


# -------------------------
# DOWNLOAD DOS DADOS
# -------------------------

if not arquivo_dados.exists():
    print("Baixando dados...")
    gdown.download(
        "https://drive.google.com/uc?export=download&id=1UGrPGCw_wgOjoVPVHorx4KxumrCaD9UQ",
        str(arquivo_dados),
        quiet=False,
    )

if not arquivo_geojson.exists():
    print("Baixando municípios...")
    gdown.download(
        "https://drive.google.com/uc?export=download&id=1V6konvrDhrE02h8IPeOFVkItt6qJWphR",
        str(arquivo_geojson),
        quiet=False,
    )


# -------------------------
# LEITURA
# -------------------------

df = pd.read_csv(arquivo_dados)

gdf_municipios = gpd.read_file(arquivo_geojson)

gdf_municipios["id"] = (
    gdf_municipios["id"]
    .astype(str)
    .str[:-1]
)

mapa_municipios = (
    gdf_municipios
    .set_index("id")["name"]
    .to_dict()
)

df["NOME_MUNICIP"] = (
    df["ID_MUNICIP"]
    .astype(str)
    .map(mapa_municipios)
)


# -------------------------
# ANIMAIS
# -------------------------

mapa_acidente = {
    1: "Serpente",
    2: "Aranha",
    3: "Escorpião",
    4: "Lagarta",
    5: "Abelha",
    6: "Outros",
    9: "Ignorado",
}

df["TP_ACIDENT"] = (
    df["TP_ACIDENT"]
    .map(mapa_acidente)
    .fillna("Ignorado")
)


# -------------------------
# CRIA OS FILTROS
# -------------------------

filtros = {
    "anos": sorted(
        df["NU_ANO"]
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    ),

    "animais": sorted(
        df["TP_ACIDENT"]
        .dropna()
        .unique()
        .tolist()
    ),

    "municipios": sorted(
        df["NOME_MUNICIP"]
        .dropna()
        .unique()
        .tolist()
    ),
}


# -------------------------
# SALVA JSON
# -------------------------

saida = PASTA_DATA / "filtros.json"

with open(saida, "w", encoding="utf-8") as arquivo:
    json.dump(
        filtros,
        arquivo,
        ensure_ascii=False,
        separators=(",", ":"),
    )

print(f"Arquivo criado: {saida}")