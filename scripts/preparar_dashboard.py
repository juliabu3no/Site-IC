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

# -------------------------
# DASHBOARD COMPACTO
# -------------------------

df_dashboard = df.dropna(
    subset=["NU_ANO", "NOME_MUNICIP"]
).copy()

# Garante tipos numéricos
df_dashboard["NU_ANO"] = pd.to_numeric(
    df_dashboard["NU_ANO"],
    errors="coerce"
).astype(int)

df_dashboard["TRA_CLASSI"] = (
    pd.to_numeric(
        df_dashboard["TRA_CLASSI"],
        errors="coerce"
    )
    .fillna(9)
    .astype(int)
)

df_dashboard["DOENCA_TRA"] = (
    pd.to_numeric(
        df_dashboard["DOENCA_TRA"],
        errors="coerce"
    )
    .fillna(9)
    .astype(int)
)

df_dashboard["ANT_TEMPO_"] = (
    pd.to_numeric(
        df_dashboard["ANT_TEMPO_"],
        errors="coerce"
    )
    .fillna(9)
    .astype(int)
)

# Mês da notificação
df_dashboard["MES"] = (
    pd.to_datetime(
        df_dashboard["DT_NOTIFIC"],
        errors="coerce"
    )
    .dt.month
    .fillna(0)
    .astype(int)
)

# Óbito
df_dashboard["OBITO"] = (
    pd.to_numeric(
        df_dashboard["EVOLUCAO"],
        errors="coerce"
    ) == 2
).astype(int)


# -------------------------
# TRANSFORMA NOMES EM ÍNDICES
# -------------------------

mapa_anos = {
    ano: i
    for i, ano in enumerate(filtros["anos"])
}

mapa_animais = {
    animal: i
    for i, animal in enumerate(filtros["animais"])
}

mapa_municipios = {
    municipio: i
    for i, municipio in enumerate(filtros["municipios"])
}

df_dashboard["y"] = (
    df_dashboard["NU_ANO"]
    .map(mapa_anos)
    .astype(int)
)

df_dashboard["a"] = (
    df_dashboard["TP_ACIDENT"]
    .map(mapa_animais)
    .astype(int)
)

df_dashboard["m"] = (
    df_dashboard["NOME_MUNICIP"]
    .map(mapa_municipios)
    .astype(int)
)


# -------------------------
# CASOS E ÓBITOS
# -------------------------

base = (
    df_dashboard
    .groupby(["y", "a", "m"])
    .agg(
        casos=("NU_ANO", "size"),
        obitos=("OBITO", "sum")
    )
    .reset_index()
)

dados_base = [
    [
        int(r.y),
        int(r.a),
        int(r.m),
        int(r.casos),
        int(r.obitos)
    ]
    for r in base.itertuples()
]


# -------------------------
# GRAVIDADE
# -------------------------

gravidade = (
    df_dashboard
    .groupby(["y", "a", "m", "TRA_CLASSI"])
    .size()
    .reset_index(name="casos")
)

dados_gravidade = [
    [
        int(r.y),
        int(r.a),
        int(r.m),
        int(r.TRA_CLASSI),
        int(r.casos)
    ]
    for r in gravidade.itertuples()
]


# -------------------------
# ACIDENTE DE TRABALHO
# -------------------------

trabalho = (
    df_dashboard
    .groupby(["y", "a", "m", "DOENCA_TRA"])
    .size()
    .reset_index(name="casos")
)

dados_trabalho = [
    [
        int(r.y),
        int(r.a),
        int(r.m),
        int(r.DOENCA_TRA),
        int(r.casos)
    ]
    for r in trabalho.itertuples()
]


# -------------------------
# CASOS POR MÊS
# -------------------------

mes = (
    df_dashboard
    .groupby(["y", "a", "m", "MES"])
    .size()
    .reset_index(name="casos")
)

dados_mes = [
    [
        int(r.y),
        int(r.a),
        int(r.m),
        int(r.MES),
        int(r.casos)
    ]
    for r in mes.itertuples()
]


# -------------------------
# TEMPO DE ATENDIMENTO
# -------------------------

tempo = (
    df_dashboard
    .groupby(["y", "a", "m", "ANT_TEMPO_"])
    .size()
    .reset_index(name="casos")
)

dados_tempo = [
    [
        int(r.y),
        int(r.a),
        int(r.m),
        int(r.ANT_TEMPO_),
        int(r.casos)
    ]
    for r in tempo.itertuples()
]


# -------------------------
# SALVA ARQUIVOS DO DASHBOARD
# -------------------------

arquivos_dashboard = {
    "base.json": dados_base,
    "gravidade.json": dados_gravidade,
    "trabalho.json": dados_trabalho,
    "mes.json": dados_mes,
    "tempo.json": dados_tempo,
}

for nome_arquivo, dados in arquivos_dashboard.items():

    caminho = PASTA_DATA / nome_arquivo

    with open(
        caminho,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            dados,
            arquivo,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    print(f"Arquivo criado: {caminho}")