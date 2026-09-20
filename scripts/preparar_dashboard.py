from pathlib import Path
import json
import pandas as pd
import geopandas as gpd

# =========================
# CONFIGURAÇÃO
# =========================
RAIZ = Path(__file__).resolve().parent.parent
PASTA_DADOS = RAIZ / "dados_local"
PASTA_DATA = RAIZ / "public" / "data"
ARQUIVO_ENTRADA = PASTA_DADOS / "sinan_sp_tratado.csv"
ARQUIVO_DIVISOES = PASTA_DADOS / "divisoes.gpkg"

PASTA_DATA.mkdir(parents=True, exist_ok=True)

# Prefixo comum dos JSONs agregados:
# [ano, animal, municipio, gravidade, evolucao, ...]
CHAVES_FILTRO = ["y", "a", "m", "g", "e"]

# Cada coluna representa a quantidade de ampolas de um tipo de soro.
COLUNAS_SOROS = {
    "ampolas_antiaracnidico": "Antiaracnídico",
    "ampolas_antibotropico": "Antibotrópico",
    "ampolas_antibotropico_crotalico": "Antibotrópico-crotálico",
    "ampolas_antibotropico_laquetico": "Antibotrópico-laquético",
    "ampolas_anticrotalico": "Anticrotálico",
    "ampolas_antielapidico": "Antielapídico",
    "ampolas_antiescorpionico": "Antiescorpiônico",
    "ampolas_antilonomico": "Antilonômico",
    "ampolas_antiloxoscelico": "Antiloxoscélico",
}

COLUNAS_NECESSARIAS = [
    "ano_notificacao",
    "semana_epidemiologica",
    "tipo_acidente",
    "municipio_ocorrencia",
    "gravidade",
    "mes_acidente",
    "tempo_atendimento",
    "idade_anos",
    "sexo",
    "local_picada",
    "acidente_trabalho",
    "raca_cor",
    "escolaridade",
    "tipo_serpente",
    "tipo_aranha",
    "tipo_lagarta",
    "soroterapia",
    "evolucao",
    *COLUNAS_SOROS.keys(),
]

MAPA_TEMPO = {
    "0 a 1 hora": 1,
    "1 a 3 horas": 2,
    "3 a 6 horas": 3,
    "6 a 12 horas": 4,
    "12 a 24 horas": 5,
    "24 horas ou mais": 6,
    "Ignorado": 9,
}

MAPA_MESES = {
    "Janeiro": 1,
    "Fevereiro": 2,
    "Março": 3,
    "Abril": 4,
    "Maio": 5,
    "Junho": 6,
    "Julho": 7,
    "Agosto": 8,
    "Setembro": 9,
    "Outubro": 10,
    "Novembro": 11,
    "Dezembro": 12,
    "Ignorado": 0,
}

ORDEM_GRAVIDADE = ["Leve", "Moderado", "Grave", "Ignorado"]

ORDEM_EVOLUCAO = [
    "Cura",
    "Óbito por acidente por animais peçonhentos",
    "Óbito por outras causas",
    "Ignorado",
    "Sem informação",
]

FAIXAS_ETARIAS = [
    "0–9",
    "10–19",
    "20–29",
    "30–39",
    "40–49",
    "50–59",
    "60–69",
    "70–79",
    "80–89",
    "90–99",
    "100+",
    "Ignorado",
]

ORDEM_SEXO = [
    "Masculino",
    "Feminino",
    "Ignorado",
]

ORDEM_LOCAL_PICADA = [
    "Cabeça",
    "Braço",
    "Antebraço",
    "Mão",
    "Dedo da mão",
    "Tronco",
    "Coxa",
    "Perna",
    "Pé",
    "Dedo do pé",
    "Ignorado",
]

ORDEM_ACIDENTE_TRABALHO = [
    "Sim",
    "Não",
    "Ignorado",
]

ORDEM_RACA_COR = [
    "Branca",
    "Preta",
    "Amarela",
    "Parda",
    "Indígena",
    "Ignorado",
]

ORDEM_ESCOLARIDADE = [
    "Analfabeto",
    "1ª a 4ª série incompleta do EF",
    "4ª série completa do EF",
    "5ª a 8ª série incompleta do EF",
    "Ensino fundamental completo",
    "Ensino médio incompleto",
    "Ensino médio completo",
    "Educação superior incompleta",
    "Educação superior completa",
    "Ignorado",
    "Não se aplica",
]

ORDEM_SUBTIPOS_ANIMAIS = [
    "Serpente — Botrópico",
    "Serpente — Crotálico",
    "Serpente — Elapídico",
    "Serpente — Laquético",
    "Serpente — Serpente não peçonhenta",
    "Serpente — Ignorado",
    "Aranha — Foneutrismo",
    "Aranha — Loxoscelismo",
    "Aranha — Latrodectismo",
    "Aranha — Outra aranha",
    "Aranha — Ignorado",
    "Lagarta — Lonomia",
    "Lagarta — Outra lagarta",
    "Lagarta — Ignorado",
]

TEMPOS_CONHECIDOS = [
    "0 a 1 hora",
    "1 a 3 horas",
    "3 a 6 horas",
    "6 a 12 horas",
    "12 a 24 horas",
    "24 horas ou mais",
]

FAIXAS_AMPOLAS = [
    "1–2",
    "3–4",
    "5–6",
    "7–8",
    "9–12",
    "13 ou mais",
]

LIMITES_AMPOLAS = [0, 2, 4, 6, 8, 12, float("inf")]


# =========================
# FUNÇÕES AUXILIARES
# =========================
def valores_ordenados(serie):
    """Retorna valores únicos, sem nulos, em ordem."""
    return sorted(serie.dropna().unique().tolist())


def criar_mapa_indices(valores):
    """Cria índices compactos usados nos JSONs."""
    return {valor: indice for indice, valor in enumerate(valores)}


def indices_filtro(registro):
    """Retorna os índices compactos dos filtros na ordem padrão."""
    return [int(getattr(registro, chave)) for chave in CHAVES_FILTRO]


def agregar_categoria(df, coluna):
    """Conta casos por filtros + categoria."""
    return (
        df.groupby(CHAVES_FILTRO + [coluna], observed=True)
        .size()
        .reset_index(name="casos")
    )


def para_json_categoria(df_agregado, coluna):
    """Converte para [filtros..., categoria, casos]."""
    return [
        [
            *indices_filtro(r),
            int(getattr(r, coluna)),
            int(r.casos),
        ]
        for r in df_agregado.itertuples()
    ]


def preparar_uso_soros(df):
    """Conta casos com uso registrado de cada tipo de soro."""
    dados = []

    for indice_soro, coluna in enumerate(COLUNAS_SOROS):
        agregado = (
            df.loc[df[coluna].gt(0)]
            .groupby(CHAVES_FILTRO, observed=True)
            .size()
            .reset_index(name="casos")
        )

        dados.extend(
            [
                [
                    *indices_filtro(r),
                    indice_soro,
                    int(r.casos),
                ]
                for r in agregado.itertuples()
            ]
        )

    return dados


def preparar_total_ampolas(df):
    """Soma ampolas registradas e conta casos com uso de cada soro."""
    dados = []

    for indice_soro, coluna in enumerate(COLUNAS_SOROS):
        agregado = (
            df.loc[df[coluna].gt(0)]
            .groupby(CHAVES_FILTRO, observed=True)
            .agg(
                ampolas=(coluna, "sum"),
                casos=(coluna, "size"),
            )
            .reset_index()
        )

        dados.extend(
            [
                [
                    *indices_filtro(r),
                    indice_soro,
                    int(r.ampolas),
                    int(r.casos),
                ]
                for r in agregado.itertuples()
            ]
        )

    return dados


def preparar_distribuicao_ampolas(df):
    """Conta casos por tipo de soro e faixa de ampolas administradas."""
    dados = []

    for indice_soro, coluna in enumerate(COLUNAS_SOROS):
        base_soro = df.loc[
            df[coluna].gt(0),
            CHAVES_FILTRO + [coluna],
        ].copy()

        if base_soro.empty:
            continue

        base_soro["faixa_ampolas"] = pd.cut(
            base_soro[coluna],
            bins=LIMITES_AMPOLAS,
            labels=False,
            include_lowest=False,
            right=True,
        ).astype("Int64")

        agregado = (
            base_soro
            .dropna(subset=["faixa_ampolas"])
            .groupby(
                CHAVES_FILTRO + ["faixa_ampolas"],
                observed=True,
            )
            .size()
            .reset_index(name="casos")
        )

        dados.extend(
            [
                [
                    *indices_filtro(r),
                    indice_soro,
                    int(r.faixa_ampolas),
                    int(r.casos),
                ]
                for r in agregado.itertuples()
            ]
        )

    return dados


def salvar_json(nome, conteudo):
    """Salva JSON compacto em public/data."""
    caminho = PASTA_DATA / nome

    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(
            conteudo,
            arquivo,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    print(f"Arquivo criado: {nome}")


# =========================
# 1. LEITURA
# =========================
print("======================================")
print("PREPARAÇÃO DOS DADOS DO DASHBOARD")
print("======================================")
print("\n[1/7] Lendo base tratada...")

df = pd.read_csv(ARQUIVO_ENTRADA, low_memory=False)

if not ARQUIVO_DIVISOES.exists():
    raise FileNotFoundError(
        f"Base territorial não encontrada: {ARQUIVO_DIVISOES}"
    )

divisoes = gpd.read_file(ARQUIVO_DIVISOES)

colunas_territoriais_necessarias = [
    "Municipio",
    "Populacao Estimada IBGE 2022",
    "geometry",
]

colunas_territoriais_ausentes = [
    coluna
    for coluna in colunas_territoriais_necessarias
    if coluna not in divisoes.columns
]

if colunas_territoriais_ausentes:
    raise ValueError(
        "Colunas ausentes em divisoes.gpkg: "
        + ", ".join(colunas_territoriais_ausentes)
    )

divisoes["Populacao Estimada IBGE 2022"] = pd.to_numeric(
    divisoes["Populacao Estimada IBGE 2022"],
    errors="coerce",
)

print(
    (
        f"Base carregada: {len(df):,} registros e "
        f"{len(df.columns)} colunas."
    ).replace(",", ".")
)


# =========================
# 2. VALIDAÇÃO
# =========================
print("\n[2/7] Validando colunas necessárias...")

colunas_ausentes = [
    coluna
    for coluna in COLUNAS_NECESSARIAS
    if coluna not in df.columns
]

if colunas_ausentes:
    raise ValueError(
        "Colunas necessárias ausentes na base tratada: "
        + ", ".join(colunas_ausentes)
    )

print("Colunas necessárias encontradas.")


# =========================
# 3. PREPARAÇÃO
# =========================
print("\n[3/7] Preparando variáveis utilizadas pelo dashboard...")

df_dashboard = df.copy()

# Conversões numéricas antes da filtragem evitam falhas com valores inválidos.
df_dashboard["ano_notificacao"] = pd.to_numeric(
    df_dashboard["ano_notificacao"],
    errors="coerce",
).astype("Int64")

df_dashboard["semana_codigo"] = pd.to_numeric(
    df_dashboard["semana_epidemiologica"],
    errors="coerce",
).astype("Int64")

for coluna in COLUNAS_SOROS:
    df_dashboard[coluna] = pd.to_numeric(
        df_dashboard[coluna],
        errors="coerce",
    )

# Mantém registros sem desfecho explícito disponíveis no filtro.
df_dashboard["evolucao_filtro"] = (
    df_dashboard["evolucao"]
    .fillna("Sem informação")
    .astype(str)
    .str.strip()
    .replace("", "Sem informação")
)

# Estes campos são necessários para todos os filtros do dashboard.
df_dashboard = df_dashboard.dropna(
    subset=[
        "ano_notificacao",
        "tipo_acidente",
        "municipio_ocorrencia",
        "gravidade",
    ]
).copy()

# A base tratada deve conter apenas semanas epidemiológicas de 1 a 53.
semanas_invalidas = (
    df_dashboard["semana_codigo"].notna()
    & ~df_dashboard["semana_codigo"].between(1, 53)
)

if semanas_invalidas.any():
    raise ValueError(
        f"Foram encontradas {int(semanas_invalidas.sum())} "
        "semanas epidemiológicas fora do intervalo 1–53."
    )

# Variáveis do perfil epidemiológico.
df_dashboard["idade_anos"] = pd.to_numeric(
    df_dashboard["idade_anos"],
    errors="coerce",
)

# Faixas etárias: valores ausentes ficam em "Ignorado".
df_dashboard["faixa_etaria_codigo"] = pd.cut(
    df_dashboard["idade_anos"],
    bins=[-1, 9, 19, 29, 39, 49, 59, 69, 79, 89, 99, float("inf")],
    labels=False,
    include_lowest=True,
).astype("Int64")
df_dashboard["faixa_etaria_codigo"] = (
    df_dashboard["faixa_etaria_codigo"]
    .fillna(len(FAIXAS_ETARIAS) - 1)
    .astype(int)
)

mapa_sexo = {
    valor: indice
    for indice, valor in enumerate(ORDEM_SEXO)
}
mapa_local_picada = {
    valor: indice
    for indice, valor in enumerate(ORDEM_LOCAL_PICADA)
}
mapa_acidente_trabalho = {
    valor: indice
    for indice, valor in enumerate(ORDEM_ACIDENTE_TRABALHO)
}

df_dashboard["sexo_codigo_dashboard"] = (
    df_dashboard["sexo"]
    .map(mapa_sexo)
    .fillna(mapa_sexo["Ignorado"])
    .astype(int)
)

df_dashboard["local_picada_codigo_dashboard"] = (
    df_dashboard["local_picada"]
    .map(mapa_local_picada)
    .fillna(mapa_local_picada["Ignorado"])
    .astype(int)
)

df_dashboard["acidente_trabalho_codigo_dashboard"] = (
    df_dashboard["acidente_trabalho"]
    .map(mapa_acidente_trabalho)
    .fillna(mapa_acidente_trabalho["Ignorado"])
    .astype(int)
)

# Variáveis sociais usadas no perfil das vítimas.
mapa_raca_cor = criar_mapa_indices(ORDEM_RACA_COR)
mapa_escolaridade = criar_mapa_indices(ORDEM_ESCOLARIDADE)
mapa_subtipos = criar_mapa_indices(ORDEM_SUBTIPOS_ANIMAIS)

# Valores inesperados são tratados como ignorados apenas no dashboard.
df_dashboard["raca_cor_codigo_dashboard"] = (
    df_dashboard["raca_cor"]
    .map(mapa_raca_cor)
    .fillna(mapa_raca_cor["Ignorado"])
    .astype(int)
)

df_dashboard["escolaridade_codigo_dashboard"] = (
    df_dashboard["escolaridade"]
    .map(mapa_escolaridade)
    .fillna(mapa_escolaridade["Ignorado"])
    .astype(int)
)

# Os campos de subtipo só são aplicáveis a serpentes, aranhas e lagartas.
df_dashboard["subtipo_animal"] = pd.Series(
    pd.NA,
    index=df_dashboard.index,
    dtype="string",
)

for animal, coluna in {
    "Serpente": "tipo_serpente",
    "Aranha": "tipo_aranha",
    "Lagarta": "tipo_lagarta",
}.items():
    mascara = df_dashboard["tipo_acidente"].eq(animal)
    df_dashboard.loc[mascara, "subtipo_animal"] = (
        animal
        + " — "
        + df_dashboard.loc[mascara, coluna].astype("string")
    )

df_dashboard["subtipo_animal_codigo_dashboard"] = (
    df_dashboard["subtipo_animal"]
    .map(mapa_subtipos)
    .astype("Int64")
)

# Códigos compactos usados nas séries específicas.
df_dashboard["tempo_codigo"] = (
    df_dashboard["tempo_atendimento"]
    .map(MAPA_TEMPO)
    .astype("Int64")
)

df_dashboard["mes_codigo"] = (
    df_dashboard["mes_acidente"]
    .map(MAPA_MESES)
    .astype("Int64")
)

# Variáveis auxiliares dos indicadores.
df_dashboard["obito"] = (
    df_dashboard["evolucao"]
    == "Óbito por acidente por animais peçonhentos"
).astype(int)

df_dashboard["soroterapia_sim"] = (
    df_dashboard["soroterapia"] == "Sim"
).astype(int)

# "Ignorado" não entra no denominador do percentual.
df_dashboard["soroterapia_conhecida"] = (
    df_dashboard["soroterapia"].isin(["Sim", "Não"])
).astype(int)

df_dashboard["atendimento_ate_3h"] = (
    df_dashboard["tempo_atendimento"].isin(
        ["0 a 1 hora", "1 a 3 horas"]
    )
).astype(int)

# "Ignorado" não entra no denominador do percentual.
df_dashboard["tempo_conhecido"] = (
    df_dashboard["tempo_atendimento"].isin(TEMPOS_CONHECIDOS)
).astype(int)


# =========================
# 4. FILTROS E ÍNDICES
# =========================
print("\n[4/7] Criando filtros e índices compactos...")

anos = valores_ordenados(
    df_dashboard["ano_notificacao"].astype(int)
)

animais = valores_ordenados(
    df_dashboard["tipo_acidente"].astype(str)
)

municipios = valores_ordenados(
    df_dashboard["municipio_ocorrencia"].astype(str)
)

gravidades_presentes = set(
    df_dashboard["gravidade"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

gravidades = [
    gravidade
    for gravidade in ORDEM_GRAVIDADE
    if gravidade in gravidades_presentes
]

evolucoes_presentes = set(
    df_dashboard["evolucao_filtro"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

# Mantém uma ordem legível e acrescenta categorias inesperadas ao final.
evolucoes = [
    evolucao
    for evolucao in ORDEM_EVOLUCAO
    if evolucao in evolucoes_presentes
]
evolucoes += sorted(evolucoes_presentes - set(evolucoes))

populacao_por_municipio = (
    divisoes
    .drop_duplicates(subset=["Municipio"])
    .set_index("Municipio")["Populacao Estimada IBGE 2022"]
)

populacoes_municipios = [
    (
        int(populacao_por_municipio.get(municipio))
        if pd.notna(populacao_por_municipio.get(municipio))
        else 0
    )
    for municipio in municipios
]

filtros = {
    "anos": anos,
    "animais": animais,
    "municipios": municipios,
    "populacoes_municipios": populacoes_municipios,
    "gravidades": gravidades,
    "evolucoes": evolucoes,
    "soros": list(COLUNAS_SOROS.values()),
    "faixas_ampolas": FAIXAS_AMPOLAS,
    "faixas_etarias": FAIXAS_ETARIAS,
    "sexos": ORDEM_SEXO,
    "locais_picada": ORDEM_LOCAL_PICADA,
    "acidente_trabalho": ORDEM_ACIDENTE_TRABALHO,
    "racas_cores": ORDEM_RACA_COR,
    "escolaridades": ORDEM_ESCOLARIDADE,
    "subtipos_animais": ORDEM_SUBTIPOS_ANIMAIS,
}

# Metadados territoriais disponíveis para filtros futuros.
for chave, coluna in {
    "regioes_saude": "regiao_saude_ocorrencia",
    "rras": "rras_ocorrencia",
    "drs": "drs_ocorrencia",
    "gve": "gve_ocorrencia",
}.items():
    if coluna in df_dashboard.columns:
        filtros[chave] = valores_ordenados(
            df_dashboard[coluna].astype(str)
        )

mapas_indices = {
    "y": criar_mapa_indices(anos),
    "a": criar_mapa_indices(animais),
    "m": criar_mapa_indices(municipios),
    "g": criar_mapa_indices(gravidades),
    "e": criar_mapa_indices(evolucoes),
}

# Mapeamentos do município para os recortes territoriais.
# Eles permitem reaproveitar cards.json sem criar novas agregações.
territorio_municipal = (
    divisoes
    .drop_duplicates(subset=["Municipio"])
    .set_index("Municipio")
)

mapa_regiao_saude = criar_mapa_indices(
    filtros.get("regioes_saude", [])
)
mapa_drs = criar_mapa_indices(filtros.get("drs", []))
mapa_rras = criar_mapa_indices(filtros.get("rras", []))

filtros["municipio_para_regiao_saude"] = [
    (
        mapa_regiao_saude.get(
            str(
                territorio_municipal.loc[
                    municipio,
                    "Regiao de Saude",
                ]
            )
        )
        if municipio in territorio_municipal.index
        else None
    )
    for municipio in municipios
]

filtros["municipio_para_drs"] = [
    (
        mapa_drs.get(
            str(
                territorio_municipal.loc[
                    municipio,
                    "Departamento Regional de Saude",
                ]
            )
        )
        if municipio in territorio_municipal.index
        else None
    )
    for municipio in municipios
]

filtros["municipio_para_rras"] = [
    (
        mapa_rras.get(
            str(
                territorio_municipal.loc[
                    municipio,
                    "Macrorregiao de Saude",
                ]
            )
        )
        if municipio in territorio_municipal.index
        else None
    )
    for municipio in municipios
]


def preparar_geojson_territorial(
    gdf,
    coluna_nome,
    mapa_indices_nivel,
    dissolver=False,
):
    """Gera GeoJSON enxuto com índice territorial padronizado em `u`."""
    geo = gdf[[coluna_nome, "geometry"]].dropna().copy()
    geo[coluna_nome] = geo[coluna_nome].astype(str)

    if dissolver:
        geo = geo.dissolve(
            by=coluna_nome,
            as_index=False,
        )

    geo["u"] = geo[coluna_nome].map(mapa_indices_nivel)

    geo = geo.dropna(
        subset=["u", "geometry"]
    ).copy()

    geo["u"] = geo["u"].astype(int)

    if geo.crs is None:
        raise ValueError("O arquivo divisoes.gpkg não possui CRS definido.")

    # Simplificação em metros para reduzir o tamanho enviado ao navegador.
    geo = geo.to_crs(epsg=3857)
    geo["geometry"] = geo.geometry.simplify(
        200,
        preserve_topology=True,
    )
    geo = geo.to_crs(epsg=4326)

    return json.loads(
        geo[["u", "geometry"]].to_json(
            drop_id=True
        )
    )


municipios_geojson = preparar_geojson_territorial(
    divisoes,
    "Municipio",
    mapas_indices["m"],
    dissolver=False,
)

regioes_saude_geojson = preparar_geojson_territorial(
    divisoes,
    "Regiao de Saude",
    mapa_regiao_saude,
    dissolver=True,
)

drs_geojson = preparar_geojson_territorial(
    divisoes,
    "Departamento Regional de Saude",
    mapa_drs,
    dissolver=True,
)

rras_geojson = preparar_geojson_territorial(
    divisoes,
    "Macrorregiao de Saude",
    mapa_rras,
    dissolver=True,
)

colunas_origem = {
    "y": "ano_notificacao",
    "a": "tipo_acidente",
    "m": "municipio_ocorrencia",
    "g": "gravidade",
    "e": "evolucao_filtro",
}

for codigo, coluna in colunas_origem.items():
    df_dashboard[codigo] = (
        df_dashboard[coluna]
        .map(mapas_indices[codigo])
    )

df_dashboard = df_dashboard.dropna(
    subset=CHAVES_FILTRO
).copy()

df_dashboard[CHAVES_FILTRO] = (
    df_dashboard[CHAVES_FILTRO]
    .astype(int)
)

print(
    f"Filtros preparados: {len(anos)} anos | "
    f"{len(animais)} animais | "
    f"{len(municipios)} municípios | "
    f"{len(gravidades)} gravidades."
)


# =========================
# 5. AGREGAÇÕES
# =========================
print("\n[5/7] Agregando indicadores do dashboard...")

# cards.json concentra indicadores e gráficos gerais.
cards = (
    df_dashboard
    .groupby(CHAVES_FILTRO, observed=True)
    .agg(
        casos=("ano_notificacao", "size"),
        obitos=("obito", "sum"),
        soroterapia_sim=("soroterapia_sim", "sum"),
        soroterapia_conhecida=("soroterapia_conhecida", "sum"),
        atendimento_ate_3h=("atendimento_ate_3h", "sum"),
        tempo_conhecido=("tempo_conhecido", "sum"),
    )
    .reset_index()
)

dados_cards = [
    [
        *indices_filtro(r),
        int(r.casos),
        int(r.obitos),
        int(r.soroterapia_sim),
        int(r.soroterapia_conhecida),
        int(r.atendimento_ate_3h),
        int(r.tempo_conhecido),
    ]
    for r in cards.itertuples()
]

# Séries específicas mantêm o mesmo prefixo [y, a, m, g, e].
dados_mes = para_json_categoria(
    agregar_categoria(df_dashboard, "mes_codigo"),
    "mes_codigo",
)

dados_tempo = para_json_categoria(
    agregar_categoria(df_dashboard, "tempo_codigo"),
    "tempo_codigo",
)

dados_semana = para_json_categoria(
    agregar_categoria(df_dashboard, "semana_codigo"),
    "semana_codigo",
)

dados_faixa_etaria = para_json_categoria(
    agregar_categoria(df_dashboard, "faixa_etaria_codigo"),
    "faixa_etaria_codigo",
)

dados_sexo = para_json_categoria(
    agregar_categoria(df_dashboard, "sexo_codigo_dashboard"),
    "sexo_codigo_dashboard",
)

dados_local_picada = para_json_categoria(
    agregar_categoria(df_dashboard, "local_picada_codigo_dashboard"),
    "local_picada_codigo_dashboard",
)

dados_acidente_trabalho = para_json_categoria(
    agregar_categoria(df_dashboard, "acidente_trabalho_codigo_dashboard"),
    "acidente_trabalho_codigo_dashboard",
)

dados_raca_cor = para_json_categoria(
    agregar_categoria(df_dashboard, "raca_cor_codigo_dashboard"),
    "raca_cor_codigo_dashboard",
)

dados_escolaridade = para_json_categoria(
    agregar_categoria(df_dashboard, "escolaridade_codigo_dashboard"),
    "escolaridade_codigo_dashboard",
)

dados_subtipo_animal = para_json_categoria(
    agregar_categoria(df_dashboard, "subtipo_animal_codigo_dashboard"),
    "subtipo_animal_codigo_dashboard",
)

# Um caso pode aparecer em mais de um tipo de soro se houver uso combinado.
dados_soros = preparar_uso_soros(df_dashboard)

# Total e distribuição da quantidade de ampolas por caso.
dados_ampolas_totais = preparar_total_ampolas(df_dashboard)
dados_ampolas = preparar_distribuicao_ampolas(df_dashboard)

print(
    (
        f"Agregações concluídas: "
        f"{len(dados_cards):,} combinações de filtros."
    ).replace(",", ".")
)


# =========================
# 6. GERAÇÃO DOS JSON
# =========================
print("\n[6/7] Gerando arquivos JSON...")

arquivos_dashboard = {
    "filtros.json": filtros,
    "municipios_sp.geojson": municipios_geojson,
    "regioes_saude_sp.geojson": regioes_saude_geojson,
    "drs_sp.geojson": drs_geojson,
    "rras_sp.geojson": rras_geojson,
    "cards.json": dados_cards,
    "mes.json": dados_mes,
    "tempo.json": dados_tempo,
    "semana.json": dados_semana,
    "faixa_etaria.json": dados_faixa_etaria,
    "sexo.json": dados_sexo,
    "local_picada.json": dados_local_picada,
    "acidente_trabalho.json": dados_acidente_trabalho,
    "raca_cor.json": dados_raca_cor,
    "escolaridade.json": dados_escolaridade,
    "subtipo_animal.json": dados_subtipo_animal,
    "soros.json": dados_soros,
    "ampolas_totais.json": dados_ampolas_totais,
    "ampolas.json": dados_ampolas,
}

for nome_arquivo, conteudo in arquivos_dashboard.items():
    salvar_json(nome_arquivo, conteudo)


# =========================
# 7. FINALIZAÇÃO
# =========================
print("\n[7/7] Finalizando preparação do dashboard...")

print(
    f"Preparação concluída com sucesso. "
    f"{len(arquivos_dashboard)} arquivos foram gerados em "
    f"{PASTA_DATA}."
)
