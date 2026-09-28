from pathlib import Path
from datetime import date
import json
import math
import numpy as np
import pandas as pd
import geopandas as gpd

# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
PASTA_DADOS = BASE_DIR / "dados_local"
ARQUIVO_SAIDA = BASE_DIR / "public" / "data" / "otimizacao.json"
TEMPO_MAXIMO_MINUTOS = 50
TEMPO_MAXIMO_SEGUNDOS = TEMPO_MAXIMO_MINUTOS * 60
PERIODO_DEMANDA = "2019–2025"

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

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def num(valor, casas=2):
    if pd.isna(valor):
        return None
    return round(float(valor), casas)

def minutos_texto(segundos):
    if pd.isna(segundos):
        return None
    return round(float(segundos) / 60, 2)

def nome_coluna(df, opcoes, obrigatoria=True):
    for coluna in opcoes:
        if coluna in df.columns:
            return coluna

    if obrigatoria:
        raise KeyError(
            f"Não encontrei nenhuma destas colunas: {opcoes}. "
            f"Colunas disponíveis: {list(df.columns)}"
        )
    return None

# ============================================================
# 1. LEITURA DAS BASES
# ============================================================

print("[1/9] Lendo arquivos...")

gdf_munic = gpd.read_file(PASTA_DADOS / "divisoes.gpkg")
gdf_postos = gpd.read_file(PASTA_DADOS / "postos_atualizados.gpkg")
df_dist = pd.read_csv(PASTA_DADOS / "distancias_atualizadas.csv", index_col=0,)
demandas = pd.read_csv(PASTA_DADOS / "DemandasMunicipais.csv")

# ============================================================
# 2. VALIDAÇÃO E PREPARAÇÃO
# ============================================================

print("[2/9] Validando e preparando bases...")

for coluna in ["Codigo Municipio", "Municipio"]:
    if coluna not in gdf_munic.columns:
        raise ValueError(
            f"Coluna ausente em divisoes.gpkg: {coluna}"
        )

for coluna in ["Codigo Municipio", "Tem Soro", *TIPOS_SORO]:
    if coluna not in gdf_postos.columns:
        raise ValueError(
            f"Coluna ausente em postos_atualizados.gpkg: {coluna}"
        )

# Na disponibilidade dos soros, NaN significa que o PESA não possui o soro.
gdf_postos[TIPOS_SORO] = (
    gdf_postos[TIPOS_SORO]
    .fillna(0)
    .astype(int)
)

postos_ativos = (
    gdf_postos[gdf_postos["Tem Soro"].eq(1)]
    .copy()
)

indices_postos_ativos = postos_ativos.index.to_numpy()

# Garante matriz numérica
df_dist = df_dist.apply(pd.to_numeric, errors="coerce")
distancias = df_dist.to_numpy(dtype=float)

if distancias.shape[0] != len(gdf_munic):
    raise ValueError(
        f"A matriz possui {distancias.shape[0]} linhas, "
        f"mas há {len(gdf_munic)} municípios."
    )

if distancias.shape[1] != len(gdf_postos):
    raise ValueError(
        f"A matriz possui {distancias.shape[1]} colunas, "
        f"mas há {len(gdf_postos)} postos."
    )

tempos_postos_ativos = distancias[:, indices_postos_ativos]

if np.isnan(tempos_postos_ativos).all(axis=1).any():
    linhas = np.where(np.isnan(tempos_postos_ativos).all(axis=1))[0]

    municipios_problema = (gdf_munic.iloc[linhas]["Municipio"].astype(str).tolist())

    raise ValueError(
        "Há municípios sem nenhum tempo válido na matriz para os "
        f"PESA ativos: {municipios_problema}"
    )

# ============================================================
# 3. COBERTURA ESTRUTURAL DA REDE
# ============================================================

print("[3/9] Calculando cobertura estrutural da rede...")

# "Estrutural" = existe qualquer PESA ativo alcançável no limite, independentemente do tipo de soro disponível.

cobertura_estrutural = (
    tempos_postos_ativos <= TEMPO_MAXIMO_SEGUNDOS
).any(axis=1)

indices_descobertos = np.where(~cobertura_estrutural)[0]

col_nome_posto = nome_coluna(
    postos_ativos,
    ["Nome Posto", "Nome", "Estabelecimento"],
    obrigatoria=False,
)

detalhes_descobertos = []

for m in indices_descobertos:
    linha_tempos = tempos_postos_ativos[m]
    posicao_local = int(np.nanargmin(linha_tempos))
    tempo_min_seg = float(linha_tempos[posicao_local])
    posto_mais_proximo = postos_ativos.iloc[posicao_local]

    detalhes_descobertos.append({
        "codigo_municipio": int(
            gdf_munic.iloc[m]["Codigo Municipio"]
        ),

        "municipio": str(
            gdf_munic.iloc[m]["Municipio"]
        ),

        "tempo_minimo_minutos": minutos_texto(
            tempo_min_seg
        ),

        "tempo_minimo_inteiro_minutos": math.ceil(
            tempo_min_seg / 60
        ),

        "pesa_mais_proximo": (
            str(posto_mais_proximo[col_nome_posto])

            if col_nome_posto
            and pd.notna(posto_mais_proximo[col_nome_posto])
            else None
        ),

        "municipio_pesa_mais_proximo": str(
            posto_mais_proximo["Municipio"]
        ) if "Municipio" in postos_ativos.columns else None,
    })

# Tempo mínimo necessário para que TODOS os municípios tenham ao menos um PESA ativo alcançável.

tempo_mais_proximo_por_municipio = np.nanmin(
    tempos_postos_ativos,
    axis=1,
)

tempo_minimo_rede_seg = float(
    np.nanmax(tempo_mais_proximo_por_municipio)
)

indice_limitante = int(
    np.nanargmax(tempo_mais_proximo_por_municipio)
)

tempo_minimo_rede_min = tempo_minimo_rede_seg / 60

tempo_minimo_rede_inteiro = math.ceil(
    tempo_minimo_rede_min
)

municipio_limitante = {
    "codigo_municipio": int(gdf_munic.iloc[indice_limitante]["Codigo Municipio"]),
    "municipio": str(gdf_munic.iloc[indice_limitante]["Municipio"]),
    "tempo_minimo_minutos": round(tempo_minimo_rede_min, 2,),
    "tempo_minimo_inteiro_minutos": (tempo_minimo_rede_inteiro),
}

# ============================================================
# 4. PREPARAÇÃO DA DEMANDA
# ============================================================

print("[4/9] Preparando demanda...")

if "Codigo Municipio" not in demandas.columns:
    raise ValueError(
        "DemandasMunicipais.csv precisa da coluna "
        "'Codigo Municipio'."
    )

demandas = (
    demandas
    .set_index("Codigo Municipio")
    .reindex(gdf_munic["Codigo Municipio"])
    .fillna(0)
)

colunas_demanda = {}

for soro in TIPOS_SORO:
    bruta = f"Casos {soro}"
    normalizada = f"Casos {soro} Normalizado"

    if bruta in demandas.columns:
        colunas_demanda[soro] = bruta

    elif normalizada in demandas.columns:
        colunas_demanda[soro] = normalizada

        print(
            f"  Atenção: usando '{normalizada}' para {soro}."
        )

    else:
        raise KeyError(
            f"Não encontrei demanda para {soro}."

        )

# ============================================================

# 5. COBERTURA ATUAL POR SORO

# ============================================================

print("[5/9] Calculando cobertura atual por soro...")

resultados_por_soro = []

cobertura_por_soro = {}

total_municipios_soro_cobertos = 0

demanda_total_global = 0.0

demanda_coberta_global = 0.0

for soro in TIPOS_SORO:

    # Índices no DataFrame completo de postos.
    indices_postos_soro = (
        postos_ativos[
            postos_ativos[soro].eq(1)
        ]
        .index
        .to_numpy()
    )

    if len(indices_postos_soro) == 0:
        coberto = np.zeros(
            len(gdf_munic),
            dtype=bool,
        )

    else:
        tempos_soro = distancias[
            :,
            indices_postos_soro,
        ]

        coberto = (
            tempos_soro <= TEMPO_MAXIMO_SEGUNDOS
        ).any(axis=1)

    # Guarda a cobertura deste soro para uso no mapa.
    cobertura_por_soro[soro] = coberto.copy()
    coluna_demanda = colunas_demanda[soro]
    vetor_demanda = (
        demandas[coluna_demanda]
        .astype(float)
        .to_numpy()
    )

    demanda_total = float(vetor_demanda.sum())
    demanda_coberta = float(vetor_demanda[coberto].sum())
    municipios_cobertos = int(coberto.sum())
    total_municipios_soro_cobertos += (municipios_cobertos)
    demanda_total_global += demanda_total
    demanda_coberta_global += demanda_coberta

    resultados_por_soro.append({
        "soro": soro,
        "postos": int(postos_ativos[soro].eq(1).sum()),
        "municipios_cobertos": municipios_cobertos,
        "municipios_descobertos": int(len(gdf_munic) - municipios_cobertos),
        "cobertura_municipio_soro": num(100 * municipios_cobertos / len(gdf_munic)),
        "cobertura_demanda": num(100 * demanda_coberta / demanda_total
                                 if demanda_total
                                 else np.nan),
    })

# ============================================================
# 6. MÉTRICAS GLOBAIS
# ============================================================

print("[6/9] Calculando métricas globais...")

total_combinacoes = len(gdf_munic) * len(TIPOS_SORO)
cobertura_municipio_soro_global = 100 * total_municipios_soro_cobertos / total_combinacoes
cobertura_demanda_global = (

    100

    * demanda_coberta_global

    / demanda_total_global

    if demanda_total_global

    else np.nan

)

cobertura_estrutural_percentual = (

    100

    * cobertura_estrutural.sum()

    / len(gdf_munic)

)

# ============================================================

# 7. DEMANDA POR TIPO DE SORO PARA VISUALIZAÇÃO

# ============================================================

print("[7/9] Organizando demanda por tipo de soro...")

demanda_municipios = []

for i, municipio in gdf_munic.iterrows():

    item = {

        "codigo_municipio": int(

            municipio["Codigo Municipio"]

        ),

        "municipio": str(

            municipio["Municipio"]

        ),

    }

    total = 0.0

    for soro in TIPOS_SORO:

        valor = float(

            demandas.iloc[i][

                colunas_demanda[soro]

            ]

        )

        item[soro] = num(valor)

        total += valor

    item["total"] = num(total)

    demanda_municipios.append(item)

# ============================================================
# 8. DADOS GEOGRÁFICOS PARA OS MAPAS
# ============================================================
print("[8/9] Preparando dados dos mapas...")

if gdf_munic.crs is None:
    raise ValueError(
        "divisoes.gpkg não possui sistema de referência (CRS)."
    )

gdf_mapa = gdf_munic.to_crs(epsg=4326).copy()

# GeoJSON dos 645 municípios.
geojson_municipios = json.loads(
    gdf_mapa[
        ["Codigo Municipio", "Municipio", "geometry"]
    ].to_json()
)

for i, feature in enumerate(geojson_municipios["features"]):
    feature["properties"] = {
        "codigo_municipio": int(
            gdf_mapa.iloc[i]["Codigo Municipio"]
        ),
        "municipio": str(
            gdf_mapa.iloc[i]["Municipio"]
        ),
        "cobertura_estrutural": bool(
            cobertura_estrutural[i]
        ),
        "cobertura_soros": {
            soro: bool(
                cobertura_por_soro[soro][i]
            )
            for soro in TIPOS_SORO
        },
    }

# Pontos dos PESAs.
postos_mapa = []

col_lat = nome_coluna(
    postos_ativos,
    ["Latitude", "LATITUDE", "latitude"],
    obrigatoria=False,
)
col_lon = nome_coluna(
    postos_ativos,
    ["Longitude", "LONGITUDE", "longitude"],
    obrigatoria=False,
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
            "postos_atualizados.gpkg não possui CRS e há PESAs "
            "sem Latitude/Longitude válidas."
        )

    postos_wgs84 = postos_ativos.to_crs(
        epsg=4326
    )

for posicao, (_, posto) in enumerate(
    postos_ativos.iterrows()
):
    latitude = None
    longitude = None

    if (
        col_lat is not None
        and col_lon is not None
        and pd.notna(posto[col_lat])
        and pd.notna(posto[col_lon])
    ):
        latitude = float(posto[col_lat])
        longitude = float(posto[col_lon])
    else:
        geometria = (
            postos_wgs84.iloc[posicao].geometry
        )

        if (
            geometria is not None
            and not geometria.is_empty
        ):
            ponto = (
                geometria
                if geometria.geom_type == "Point"
                else geometria.centroid
            )

            latitude = float(ponto.y)
            longitude = float(ponto.x)

    if latitude is None or longitude is None:
        continue

    nome_pesa = (
        str(posto[col_nome_posto])
        if col_nome_posto
        and pd.notna(
            posto[col_nome_posto]
        )
        else "PESA"
    )

    municipio_pesa = (
        str(posto["Municipio"])
        if "Municipio" in postos_ativos.columns
        and pd.notna(posto["Municipio"])
        else None
    )

    postos_mapa.append({
        "codigo_municipio": (
            int(posto["Codigo Municipio"])
            if pd.notna(
                posto["Codigo Municipio"]
            )
            else None
        ),
        "municipio": municipio_pesa,
        "latitude": latitude,
        "longitude": longitude,
        "soros": [
            soro
            for soro in TIPOS_SORO
            if int(posto[soro]) == 1
        ],
        "nome": nome_pesa,
    })

mapa = {
    "municipios": geojson_municipios,
    "postos": postos_mapa,
}

# ============================================================
# 9. JSON FINAL
# ============================================================
print("[9/9] Gerando JSON...")

dados_json = {

    "metadados": {

        "gerado_em": date.today().isoformat(),

        "tempo_maximo_minutos": TEMPO_MAXIMO_MINUTOS,

        "municipios": len(gdf_munic),

        "pesa": len(postos_ativos),

        "municipios_com_pesa": int(

            postos_ativos[

                "Codigo Municipio"

            ].nunique()

        ),

        "periodo_demanda": PERIODO_DEMANDA,

        "tipos_soro": TIPOS_SORO,

    },

    "rede_atual": {

        "cobertura_estrutural": {

            "municipios_cobertos": int(

                cobertura_estrutural.sum()

            ),

            "municipios_descobertos": int(

                len(indices_descobertos)

            ),

            "percentual": num(

                cobertura_estrutural_percentual

            ),

            "municipios_descobertos_detalhes": (

                detalhes_descobertos

            ),

            "tempo_minimo_para_cobrir_todos": {

                "minutos_exatos": round(

                    tempo_minimo_rede_min,

                    2,

                ),

                "minutos_inteiros": (

                    tempo_minimo_rede_inteiro

                ),

                "municipio_limitante": (

                    municipio_limitante

                ),

            },

        },

        "metricas_globais": {

            "cobertura_municipio_soro": num(

                cobertura_municipio_soro_global

            ),

            "cobertura_demanda": num(

                cobertura_demanda_global

            ),

            "total_combinacoes_municipio_soro": (

                total_combinacoes

            ),

        },

        "resultados_por_soro": (

            resultados_por_soro

        ),

    },

    "demanda_municipios": demanda_municipios,

    "mapa": mapa,

}

ARQUIVO_SAIDA.parent.mkdir(

    parents=True,

    exist_ok=True,

)

with open(

    ARQUIVO_SAIDA,

    "w",

    encoding="utf-8",

) as arquivo:

    json.dump(

        dados_json,

        arquivo,

        ensure_ascii=False,

        indent=2,

    )

print()

print("Concluído.")

print(f"JSON: {ARQUIVO_SAIDA}")
print(
    f"Mapa: {len(geojson_municipios['features'])} municípios e "
    f"{len(postos_mapa)} PESAs."
)

print(

    f"Cobertura estrutural em "

    f"{TEMPO_MAXIMO_MINUTOS} min: "

    f"{int(cobertura_estrutural.sum())}/"

    f"{len(gdf_munic)} municípios "

    f"({cobertura_estrutural_percentual:.2f}%)"

)

if detalhes_descobertos:

    print()

    print(

        f"Municípios sem nenhum PESA em até "

        f"{TEMPO_MAXIMO_MINUTOS} min:"

    )

    for item in detalhes_descobertos:

        print(

            f"- {item['municipio']}: "

            f"PESA mais próximo em "

            f"{item['tempo_minimo_minutos']:.2f} min"

        )

print()

print(

    "Tempo mínimo para que todos os municípios "

    "tenham algum PESA alcançável:"

)

print(

    f"{tempo_minimo_rede_min:.2f} min "

    f"(ou {tempo_minimo_rede_inteiro} min "

    "se o limite for inteiro)"

)

print(

    f"Município limitante: "

    f"{municipio_limitante['municipio']}"

)

print()

print(

    "Cobertura município–soro: "

    f"{cobertura_municipio_soro_global:.2f}%"

)

print(

    "Cobertura da demanda: "

    f"{cobertura_demanda_global:.2f}%"

)
