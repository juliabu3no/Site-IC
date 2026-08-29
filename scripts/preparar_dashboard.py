from pathlib import Path
import json
import pandas as pd

# =========================
# CAMINHOS
# =========================
RAIZ = Path(__file__).resolve().parent.parent
PASTA_DADOS = RAIZ / "dados_local"
PASTA_DATA = RAIZ / "public" / "data"
PASTA_DATA.mkdir(parents=True, exist_ok=True)

ARQUIVO_ENTRADA = PASTA_DADOS / "sinan_sp_tratado.csv"

# =========================
# LEITURA DA BASE TRATADA
# =========================
print("======================================")
print("PREPARAÇÃO DOS DADOS DO DASHBOARD")
print("======================================")
print("\n[1/7] Lendo base tratada...")

df = pd.read_csv(ARQUIVO_ENTRADA, low_memory=False)

print(
    f"Base carregada: {len(df):,} registros e "
    f"{len(df.columns)} colunas."
    .replace(",", ".")
)

# =========================
# VALIDAÇÃO DAS COLUNAS
# =========================
print("\n[2/7] Validando colunas necessárias...")

colunas_necessarias = [
    "ano_notificacao",
    "tipo_acidente",
    "municipio_ocorrencia",
    "gravidade",
    "acidente_trabalho",
    "mes_acidente",
    "tempo_atendimento",
    "soroterapia",
    "evolucao",
]

colunas_ausentes = [
    coluna
    for coluna in colunas_necessarias
    if coluna not in df.columns
]

if colunas_ausentes:
    raise ValueError(
        "Colunas necessárias ausentes na base tratada: "
        + ", ".join(colunas_ausentes)
    )

print("Colunas necessárias encontradas.")

# =========================
# PREPARAÇÃO DAS VARIÁVEIS
# =========================
print("\n[3/7] Preparando variáveis utilizadas pelo dashboard...")

df_dashboard = df.dropna(
    subset=[
        "ano_notificacao",
        "tipo_acidente",
        "municipio_ocorrencia",
    ]
).copy()

df_dashboard["ano_notificacao"] = pd.to_numeric(
    df_dashboard["ano_notificacao"],
    errors="coerce"
).astype("Int64")

mapa_gravidade = {
    "Leve": 1,
    "Moderado": 2,
    "Grave": 3,
    "Ignorado": 9,
}

mapa_trabalho = {
    "Sim": 1,
    "Não": 2,
    "Ignorado": 9,
}

mapa_tempo = {
    "0 a 1 hora": 1,
    "1 a 3 horas": 2,
    "3 a 6 horas": 3,
    "6 a 12 horas": 4,
    "12 a 24 horas": 5,
    "24 horas ou mais": 6,
    "Ignorado": 9,
}

mapa_meses = {
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

df_dashboard["gravidade_codigo"] = (
    df_dashboard["gravidade"]
    .map(mapa_gravidade)
    .fillna(9)
    .astype(int)
)

df_dashboard["trabalho_codigo"] = (
    df_dashboard["acidente_trabalho"]
    .map(mapa_trabalho)
    .fillna(9)
    .astype(int)
)

df_dashboard["tempo_codigo"] = (
    df_dashboard["tempo_atendimento"]
    .map(mapa_tempo)
    .fillna(9)
    .astype(int)
)

df_dashboard["mes_codigo"] = (
    df_dashboard["mes_acidente"]
    .map(mapa_meses)
    .fillna(0)
    .astype(int)
)

df_dashboard["obito"] = (
    df_dashboard["evolucao"]
    == "Óbito por acidente por animais peçonhentos"
).astype(int)

# Variáveis auxiliares dos cards.
# Percentuais usam apenas registros com informação conhecida no denominador.
df_dashboard["soroterapia_sim"] = (
    df_dashboard["soroterapia"] == "Sim"
).astype(int)

df_dashboard["soroterapia_conhecida"] = (
    df_dashboard["soroterapia"].isin(["Sim", "Não"])
).astype(int)

categorias_tempo_conhecido = [
    "0 a 1 hora",
    "1 a 3 horas",
    "3 a 6 horas",
    "6 a 12 horas",
    "12 a 24 horas",
    "24 horas ou mais",
]

df_dashboard["atendimento_ate_3h"] = (
    df_dashboard["tempo_atendimento"].isin(
        ["0 a 1 hora", "1 a 3 horas"]
    )
).astype(int)

df_dashboard["tempo_conhecido"] = (
    df_dashboard["tempo_atendimento"].isin(
        categorias_tempo_conhecido
    )
).astype(int)

# Conferências opcionais:
# print(df_dashboard["gravidade_codigo"].value_counts(dropna=False).sort_index())
# print(df_dashboard["trabalho_codigo"].value_counts(dropna=False).sort_index())
# print(df_dashboard["tempo_codigo"].value_counts(dropna=False).sort_index())
# print(df_dashboard["mes_codigo"].value_counts(dropna=False).sort_index())

# =========================
# FILTROS E ÍNDICES
# =========================
print("\n[4/7] Criando filtros e índices compactos...")

anos = sorted(
    df_dashboard["ano_notificacao"]
    .dropna()
    .astype(int)
    .unique()
    .tolist()
)

animais = sorted(
    df_dashboard["tipo_acidente"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

municipios = sorted(
    df_dashboard["municipio_ocorrencia"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

filtros = {
    "anos": anos,
    "animais": animais,
    "municipios": municipios,
}

# Variáveis territoriais adicionais já disponíveis para futuras
# expansões dos filtros do dashboard.
for chave, coluna in {
    "regioes_saude": "regiao_saude_ocorrencia",
    "rras": "rras_ocorrencia",
    "drs": "drs_ocorrencia",
    "gve": "gve_ocorrencia",
}.items():
    if coluna in df_dashboard.columns:
        filtros[chave] = sorted(
            df_dashboard[coluna]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

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
    df_dashboard["ano_notificacao"]
    .astype(int)
    .map(mapa_anos)
)

df_dashboard["a"] = (
    df_dashboard["tipo_acidente"]
    .map(mapa_animais)
)

df_dashboard["m"] = (
    df_dashboard["municipio_ocorrencia"]
    .map(mapa_municipios)
)

df_dashboard = df_dashboard.dropna(
    subset=["y", "a", "m"]
).copy()

df_dashboard[["y", "a", "m"]] = (
    df_dashboard[["y", "a", "m"]]
    .astype(int)
)

print(
    f"Filtros preparados: {len(anos)} anos | "
    f"{len(animais)} animais | "
    f"{len(municipios)} municípios."
)

# =========================
# AGREGAÇÕES
# =========================
print("\n[5/7] Agregando indicadores do dashboard...")

base = (
    df_dashboard
    .groupby(["y", "a", "m"], observed=True)
    .agg(
        casos=("ano_notificacao", "size"),
        obitos=("obito", "sum"),
    )
    .reset_index()
)

cards = (
    df_dashboard
    .groupby(["y", "a", "m"], observed=True)
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

gravidade = (
    df_dashboard
    .groupby(
        ["y", "a", "m", "gravidade_codigo"],
        observed=True
    )
    .size()
    .reset_index(name="casos")
)

trabalho = (
    df_dashboard
    .groupby(
        ["y", "a", "m", "trabalho_codigo"],
        observed=True
    )
    .size()
    .reset_index(name="casos")
)

mes = (
    df_dashboard
    .groupby(
        ["y", "a", "m", "mes_codigo"],
        observed=True
    )
    .size()
    .reset_index(name="casos")
)

tempo = (
    df_dashboard
    .groupby(
        ["y", "a", "m", "tempo_codigo"],
        observed=True
    )
    .size()
    .reset_index(name="casos")
)

dados_base = [
    [
        int(r.y),
        int(r.a),
        int(r.m),
        int(r.casos),
        int(r.obitos),
    ]
    for r in base.itertuples()
]

# cards.json:
# [ano_idx, animal_idx, municipio_idx, casos, obitos,
#  soroterapia_sim, soroterapia_conhecida,
#  atendimento_ate_3h, tempo_conhecido]
dados_cards = [
    [
        int(r.y),
        int(r.a),
        int(r.m),
        int(r.casos),
        int(r.obitos),
        int(r.soroterapia_sim),
        int(r.soroterapia_conhecida),
        int(r.atendimento_ate_3h),
        int(r.tempo_conhecido),
    ]
    for r in cards.itertuples()
]

dados_gravidade = [
    [
        int(r.y),
        int(r.a),
        int(r.m),
        int(r.gravidade_codigo),
        int(r.casos),
    ]
    for r in gravidade.itertuples()
]

dados_trabalho = [
    [
        int(r.y),
        int(r.a),
        int(r.m),
        int(r.trabalho_codigo),
        int(r.casos),
    ]
    for r in trabalho.itertuples()
]

dados_mes = [
    [
        int(r.y),
        int(r.a),
        int(r.m),
        int(r.mes_codigo),
        int(r.casos),
    ]
    for r in mes.itertuples()
]

dados_tempo = [
    [
        int(r.y),
        int(r.a),
        int(r.m),
        int(r.tempo_codigo),
        int(r.casos),
    ]
    for r in tempo.itertuples()
]

print(
    f"Agregações concluídas: "
    f"{len(dados_base):,} combinações principais."
    .replace(",", ".")
)

# =========================
# GERAÇÃO DOS JSON
# =========================
print("\n[6/7] Gerando arquivos JSON...")

arquivos_dashboard = {
    "filtros.json": filtros,
    "base.json": dados_base,
    "cards.json": dados_cards,
    "gravidade.json": dados_gravidade,
    "trabalho.json": dados_trabalho,
    "mes.json": dados_mes,
    "tempo.json": dados_tempo,
}

for nome_arquivo, conteudo in arquivos_dashboard.items():
    caminho = PASTA_DATA / nome_arquivo

    with open(
        caminho,
        "w",
        encoding="utf-8"
    ) as arquivo:
        json.dump(
            conteudo,
            arquivo,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    print(f"Arquivo criado: {nome_arquivo}")

# =========================
# FINALIZAÇÃO
# =========================
print("\n[7/7] Finalizando preparação do dashboard...")

print(
    f"Preparação concluída com sucesso. "
    f"{len(arquivos_dashboard)} arquivos foram gerados em "
    f"{PASTA_DATA}."
)
