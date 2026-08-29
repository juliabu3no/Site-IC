from pathlib import Path
import pandas as pd
import numpy as np
import geopandas as gpd
import pyogrio
import gdown

# =========================
# CAMINHOS
# =========================
RAIZ = Path(__file__).resolve().parent.parent
PASTA_DADOS = RAIZ / "dados_local"
PASTA_DADOS.mkdir(parents=True, exist_ok=True)

ARQUIVO_ENTRADA = PASTA_DADOS / "sinan_animais_peconhentos_sp.csv"
ARQUIVO_SAIDA = PASTA_DADOS / "sinan_sp_tratado.csv"
ARQUIVO_DIAGNOSTICO = PASTA_DADOS / "diagnostico_colunas.csv"

# =========================
# LEITURA DOS DADOS
# =========================
print("======================================")
print("TRATAMENTO DOS DADOS DO SINAN")
print("======================================")
print("\n[1/11] Lendo base bruta...")

dados = pd.read_csv(ARQUIVO_ENTRADA, low_memory=False)

print(
    f"Base carregada: {len(dados):,} registros e "
    f"{len(dados.columns)} colunas".replace(",", ".")
)

# Verificação de duplicidades na base bruta
n_duplicados = int(dados.duplicated().sum())

print(
    f"Registros exatamente duplicados: "
    f"{n_duplicados:,}".replace(",", ".")
)

# dados = dados.drop_duplicates().copy()

# Conferência opcional:
# if n_duplicados > 0:
#     print(dados[dados.duplicated(keep=False)].head(20))

# =========================
# DIAGNÓSTICO DAS COLUNAS
# =========================
print("\n[2/11] Analisando qualidade e estrutura das colunas...")
n_total = len(dados)
diagnostico = []

for coluna in dados.columns:
    serie = dados[coluna]
    n_ausentes = serie.isna().sum()
    n_unicos = serie.nunique(dropna=True)

    diagnostico.append({
        "coluna": coluna,
        "tipo": str(serie.dtype),
        "preenchidos": n_total - n_ausentes,
        "ausentes": n_ausentes,
        "percentual_ausentes": round(n_ausentes / n_total * 100, 2),
        "valores_unicos": n_unicos,
        "constante": n_unicos <= 1,
    })

diagnostico = pd.DataFrame(diagnostico)
diagnostico.to_csv(ARQUIVO_DIAGNOSTICO, index=False, encoding="utf-8-sig")

colunas_constantes = diagnostico.loc[diagnostico["constante"], "coluna"].tolist()
print(f"Diagnóstico concluído: {len(colunas_constantes)} colunas constantes identificadas")

# Análises opcionais:
# print("\nColunas constantes:")
# print(diagnostico.loc[
#     diagnostico["constante"],
#     ["coluna", "valores_unicos"]
# ].to_string(index=False))
#
# print("\nColunas com 80% ou mais de valores ausentes:")
# print(diagnostico.loc[
#     diagnostico["percentual_ausentes"] >= 80,
#     ["coluna", "percentual_ausentes", "valores_unicos"]
# ].sort_values("percentual_ausentes", ascending=False).to_string(index=False))

# =========================
# REMOÇÃO DE COLUNAS
# =========================
print("\n[3/11] Removendo colunas fora do escopo da análise...")

# Critérios:
# 1. Variáveis constantes.
# 2. Dados de residência, pois a análise utiliza local do acidente
#    e local de notificação/atendimento.
# 3. Datas e variáveis temporais não utilizadas.
# 4. Manifestações e complicações clínicas específicas, sintetizadas
#    para o objetivo deste estudo por variáveis como gravidade.

colunas_residencia = [
    "SG_UF", "ID_MN_RESI", "ID_RG_RESI", "ID_PAIS",
]

colunas_temporais_remover = [
    "DT_NOTIFIC", "DT_SIN_PRI", "SEM_PRI", "DT_INVEST",
    "DT_OBITO", "DT_ENCERRA", "DT_DIGITA",
]

colunas_clinicas_remover = [
    "MCLI_LOCAL", "CLI_DOR", "CLI_EDEMA", "CLI_EQUIMO", "CLI_NECROS",
    "CLI_LOCAL_", "CLI_LOCA_1", "MCLI_SIST", "CLI_NEURO", "CLI_HEMORR",
    "CLI_VAGAIS", "CLI_MIOLIT", "CLI_RENAL", "CLI_OUTR_2", "CLI_OUTR_3",
    "CLI_TEMPO_", "COM_LOC", "COM_SECUND", "COM_NECROS", "COM_COMPOR",
    "COM_DEFICT", "COM_APUTAC", "COM_SISTEM", "COM_RENAL", "COM_EDEMA",
    "COM_SEPTIC", "COM_CHOQUE",
]

colunas_remover = sorted(set(
    colunas_constantes
    + colunas_residencia
    + colunas_temporais_remover
    + colunas_clinicas_remover
))

dados = dados.drop(columns=colunas_remover)
print(f"Remoção concluída: {len(colunas_remover)} colunas removidas; {len(dados.columns)} mantidas")

# Lista opcional das colunas removidas:
# for coluna in colunas_remover:
#     print(f"  - {coluna}")

# =========================
# RENOMEAÇÃO
# =========================
print("\n[4/11] Renomeando colunas e padronizando códigos...")

renomear_colunas = {
    "NU_ANO": "ano_notificacao",
    "SEM_NOT": "ano_semana_notificacao",
    "ID_MUNICIP": "municipio_notificacao_codigo",
    "ID_REGIONA": "regional_notificacao_codigo",
    "ANO_NASC": "ano_nascimento",
    "NU_IDADE_N": "idade_codigo",
    "CS_SEXO": "sexo_codigo",
    "CS_GESTANT": "gestacao_codigo",
    "CS_RACA": "raca_cor_codigo",
    "CS_ESCOL_N": "escolaridade_codigo",
    "ID_OCUPA_N": "ocupacao_cbo",
    "ANT_DT_ACI": "data_acidente",
    "ANT_MUNIC_": "municipio_ocorrencia_codigo",
    "ANT_TEMPO_": "tempo_atendimento_codigo",
    "ANT_LOCA_1": "local_picada_codigo",
    "TP_ACIDENT": "tipo_acidente_codigo",
    "ANI_TIPO_1": "outro_animal_descricao",
    "ANI_SERPEN": "tipo_serpente_codigo",
    "ANI_ARANHA": "tipo_aranha_codigo",
    "ANI_LAGART": "tipo_lagarta_codigo",
    "TRA_CLASSI": "gravidade_codigo",
    "CON_SOROTE": "soroterapia_codigo",
    "NU_AMPOLAS": "ampolas_antibotropico",
    "NU_AMPOL_1": "ampolas_anticrotalico",
    "NU_AMPOL_8": "ampolas_antiaracnidico",
    "NU_AMPOL_6": "ampolas_antibotropico_laquetico",
    "NU_AMPOL_4": "ampolas_antielapidico",
    "NU_AMPO_7": "ampolas_antiloxoscelico",
    "NU_AMPO_5": "ampolas_antibotropico_crotalico",
    "NU_AMPOL_9": "ampolas_antiescorpionico",
    "NU_AMPOL_3": "ampolas_antilonomico",
    "DOENCA_TRA": "acidente_trabalho_codigo",
    "EVOLUCAO": "evolucao_codigo",
}

dados = dados.rename(columns=renomear_colunas)

# =========================
# PADRONIZAÇÃO DOS CÓDIGOS
# =========================
colunas_codigos_numericos = [
    "tipo_acidente_codigo", "tipo_serpente_codigo", "tipo_aranha_codigo",
    "tipo_lagarta_codigo", "gravidade_codigo", "soroterapia_codigo",
    "gestacao_codigo", "raca_cor_codigo", "escolaridade_codigo",
    "acidente_trabalho_codigo", "evolucao_codigo",
    "tempo_atendimento_codigo", "local_picada_codigo",
]

for coluna in colunas_codigos_numericos:
    dados[coluna] = pd.to_numeric(dados[coluna], errors="coerce").astype("Int64")

colunas_ampolas = [
    "ampolas_antibotropico",
    "ampolas_anticrotalico",
    "ampolas_antiaracnidico",
    "ampolas_antibotropico_laquetico",
    "ampolas_antielapidico",
    "ampolas_antiloxoscelico",
    "ampolas_antibotropico_crotalico",
    "ampolas_antiescorpionico",
    "ampolas_antilonomico",
]

for coluna in colunas_ampolas:
    dados[coluna] = pd.to_numeric(
        dados[coluna],
        errors="coerce"
    )

# =========================
# DICIONÁRIOS DE DECODIFICAÇÃO
# =========================
mapa_tipo_acidente = {
    1: "Serpente", 2: "Aranha", 3: "Escorpião", 4: "Lagarta",
    5: "Abelha", 6: "Outros", 9: "Ignorado",
}
mapa_tipo_serpente = {
    1: "Botrópico", 2: "Crotálico", 3: "Elapídico", 4: "Laquético",
    5: "Serpente não peçonhenta", 9: "Ignorado",
}
mapa_tipo_aranha = {
    1: "Foneutrismo", 2: "Loxoscelismo", 3: "Latrodectismo",
    4: "Outra aranha", 9: "Ignorado",
}
mapa_tipo_lagarta = {
    1: "Lonomia", 2: "Outra lagarta", 9: "Ignorado",
}
mapa_gravidade = {
    1: "Leve", 2: "Moderado", 3: "Grave", 9: "Ignorado",
}
mapa_sim_nao = {
    1: "Sim", 2: "Não", 9: "Ignorado",
}
mapa_evolucao = {
    1: "Cura",
    2: "Óbito por acidente por animais peçonhentos",
    3: "Óbito por outras causas",
    9: "Ignorado",
}
mapa_sexo = {
    "M": "Masculino", "F": "Feminino", "I": "Ignorado",
}
mapa_gestacao = {
    1: "1º trimestre", 2: "2º trimestre", 3: "3º trimestre",
    4: "Idade gestacional ignorada", 5: "Não",
    6: "Não se aplica", 9: "Ignorado",
}
mapa_raca_cor = {
    1: "Branca", 2: "Preta", 3: "Amarela",
    4: "Parda", 5: "Indígena", 9: "Ignorado",
}
mapa_escolaridade = {
    0: "Analfabeto",
    1: "1ª a 4ª série incompleta do EF",
    2: "4ª série completa do EF",
    3: "5ª a 8ª série incompleta do EF",
    4: "Ensino fundamental completo",
    5: "Ensino médio incompleto",
    6: "Ensino médio completo",
    7: "Educação superior incompleta",
    8: "Educação superior completa",
    9: "Ignorado",
    10: "Não se aplica",
}
mapa_tempo_atendimento = {
    1: "0 a 1 hora", 2: "1 a 3 horas", 3: "3 a 6 horas",
    4: "6 a 12 horas", 5: "12 a 24 horas",
    6: "24 horas ou mais", 9: "Ignorado",
}
mapa_local_picada = {
    1: "Cabeça", 2: "Braço", 3: "Antebraço", 4: "Mão",
    5: "Dedo da mão", 6: "Tronco", 7: "Coxa", 8: "Perna",
    9: "Pé", 10: "Dedo do pé", 99: "Ignorado",
}

# =========================
# DECODIFICAÇÃO
# =========================
print("\n[5/11] Decodificando variáveis categóricas...")

dados["tipo_acidente"] = dados["tipo_acidente_codigo"].map(mapa_tipo_acidente)
dados["tipo_serpente"] = dados["tipo_serpente_codigo"].map(mapa_tipo_serpente)
dados["tipo_aranha"] = dados["tipo_aranha_codigo"].map(mapa_tipo_aranha)
dados["tipo_lagarta"] = dados["tipo_lagarta_codigo"].map(mapa_tipo_lagarta)
dados["gravidade"] = dados["gravidade_codigo"].map(mapa_gravidade)
dados["soroterapia"] = dados["soroterapia_codigo"].map(mapa_sim_nao)
dados["acidente_trabalho"] = dados["acidente_trabalho_codigo"].map(mapa_sim_nao)
dados["evolucao"] = dados["evolucao_codigo"].map(mapa_evolucao)
dados["sexo"] = dados["sexo_codigo"].map(mapa_sexo)
dados["gestacao"] = dados["gestacao_codigo"].map(mapa_gestacao)
dados["raca_cor"] = dados["raca_cor_codigo"].map(mapa_raca_cor)
dados["escolaridade"] = dados["escolaridade_codigo"].map(mapa_escolaridade)
dados["tempo_atendimento"] = dados["tempo_atendimento_codigo"].map(mapa_tempo_atendimento)
dados["local_picada"] = dados["local_picada_codigo"].map(mapa_local_picada)

# Convenção deste estudo: NaN das variáveis categóricas é tratado como "Ignorado".
# Os campos *_codigo permanecem preservados em `dados` para rastreabilidade.
colunas_decodificadas = [
    "tipo_acidente", "tipo_serpente", "tipo_aranha", "tipo_lagarta",
    "gravidade", "soroterapia", "evolucao", "sexo", "gestacao",
    "raca_cor", "escolaridade", "acidente_trabalho",
    "tempo_atendimento", "local_picada",
]
dados[colunas_decodificadas] = dados[colunas_decodificadas].fillna("Ignorado")

# Conferência opcional das categorias decodificadas:
# for coluna in colunas_decodificadas:
#     print(f"\n{coluna}:")
#     print(dados[coluna].value_counts(dropna=False))

# =========================
# CONSISTÊNCIA DA SOROTERAPIA
# =========================

dados["total_ampolas"] = (
    dados[colunas_ampolas]
    .sum(axis=1, min_count=1)
)

erro_soroterapia = (
    (dados["soroterapia"] == "Não")
    & (dados["total_ampolas"] > 0)
)

n_erro_soroterapia = int(erro_soroterapia.sum())

print(
    f"Casos sem soroterapia, mas com ampolas registradas: "
    f"{n_erro_soroterapia:,}".replace(",", ".")
)

dados = dados.loc[~erro_soroterapia].copy()

# Conferência opcional:
# if inconsistencia_soro > 0:
#     print(
#         dados.loc[
#             (dados["soroterapia"] == "Não")
#             & (dados["total_ampolas"] > 0),
#             ["soroterapia", "total_ampolas"] + colunas_ampolas
#         ].head(20)
#     )

# =========================
# TRATAMENTO DA IDADE
# =========================
print("\n[6/11] Tratando idade e variáveis temporais...")

# NU_IDADE_N: 1º dígito = unidade (1 horas, 2 dias, 3 meses, 4 anos);
# três últimos dígitos = valor. Ex.: 3009 = 9 meses; 4018 = 18 anos.

dados["idade_codigo"] = pd.to_numeric(dados["idade_codigo"], errors="coerce").astype("Int64")
idade_str = dados["idade_codigo"].astype("string").str.zfill(4)

dados["idade_unidade_codigo"] = pd.to_numeric(
    idade_str.str[0], errors="coerce"
).astype("Int64")

dados["idade_valor"] = pd.to_numeric(
    idade_str.str[1:], errors="coerce"
).astype("Int64")

mapa_unidade_idade = {
    1: "Horas", 2: "Dias", 3: "Meses", 4: "Anos",
}
dados["idade_unidade"] = (
    dados["idade_unidade_codigo"]
    .map(mapa_unidade_idade)
    .fillna("Ignorado")
)

fatores_idade = {
    1: 1 / (24 * 365.25),
    2: 1 / 365.25,
    3: 1 / 12,
    4: 1,
}
dados["idade_anos"] = (
    dados["idade_valor"]
    * dados["idade_unidade_codigo"].map(fatores_idade)
)

erro_idade = (
    dados["idade_anos"].notna()
    & (
        (dados["idade_anos"] < 0)
        | (dados["idade_anos"] > 120)
    )
)

n_erro_idade = int(erro_idade.sum())

print(
    f"Registros com idade fora de 0–120 anos: "
    f"{n_erro_idade:,}".replace(",", ".")
)

dados = dados.loc[~erro_idade].copy()

# Conferência opcional da idade:
# print(dados[
#     ["idade_codigo", "idade_unidade", "idade_valor", "idade_anos"]
# ].drop_duplicates().head(20))

# =========================
# TRATAMENTO TEMPORAL
# =========================
# NU_ANO = ano da notificação.
# SEM_NOT = ano + semana epidemiológica (AAAASS).
# ANT_DT_ACI = data do acidente (AAAAMMDD), mantida apenas para obter o mês.

dados["ano_notificacao"] = pd.to_numeric(
    dados["ano_notificacao"], errors="coerce"
).astype("Int64")

dados["ano_semana_notificacao"] = pd.to_numeric(
    dados["ano_semana_notificacao"], errors="coerce"
).astype("Int64")

dados["semana_epidemiologica"] = (
    dados["ano_semana_notificacao"] % 100
).astype("Int64")

dados["data_acidente"] = (
    pd.to_numeric(dados["data_acidente"], errors="coerce")
    .astype("Int64")
    .astype("string")
)

dados["mes_acidente_codigo"] = pd.to_numeric(
    dados["data_acidente"].str[4:6], errors="coerce"
).astype("Int64")

mapa_meses = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}

dados["mes_acidente"] = (
    dados["mes_acidente_codigo"]
    .map(mapa_meses)
    .fillna("Ignorado")
)

erro_semana = (
    dados["semana_epidemiologica"].notna()
    & ~dados["semana_epidemiologica"].between(1, 53)
)

erro_mes = (
    dados["mes_acidente"] == "Ignorado"
)

erro_temporal = erro_semana | erro_mes

n_erro_semana = int(erro_semana.sum())
n_erro_mes = int(erro_mes.sum())
n_erro_temporal = int(erro_temporal.sum())

print(
    f"Semanas inválidas: {n_erro_semana:,} | "
    f"Meses ignorados: {n_erro_mes:,} | "
    f"Total excluído: {n_erro_temporal:,}"
    .replace(",", ".")
)

dados = dados.loc[~erro_temporal].copy()

# Conferência opcional do tratamento temporal:
# print(dados[
#     ["data_acidente", "mes_acidente_codigo", "mes_acidente"]
# ].drop_duplicates().head(20))

# =========================
# BASE TRATADA PARA ANÁLISE E GEOGRAFIA
# =========================
print("\n[7/11] Montando base final para análise e enriquecimento geográfico...")

# Nesta etapa são mantidas apenas variáveis já interpretáveis e as chaves
# territoriais necessárias para adicionar município, Região de Saúde,
# DRS, RRAS, GVE etc. Os códigos categóricos intermediários ficam apenas
# em `dados`, não na base final.

colunas_base_tratada = [
    # Chaves territoriais
    "municipio_notificacao_codigo",
    "municipio_ocorrencia_codigo",

    # Tempo
    "ano_notificacao",
    "semana_epidemiologica",
    "mes_acidente",

    # Perfil
    "idade_anos",
    "idade_unidade",
    "idade_valor",
    "sexo",
    "gestacao",
    "raca_cor",
    "escolaridade",
    "ocupacao_cbo",

    # Acidente
    "tipo_acidente",
    "outro_animal_descricao",
    "tipo_serpente",
    "tipo_aranha",
    "tipo_lagarta",
    "tempo_atendimento",
    "local_picada",

    # Gravidade, tratamento e desfecho
    "gravidade",
    "soroterapia",
    "total_ampolas",
    "ampolas_antibotropico",
    "ampolas_anticrotalico",
    "ampolas_antiaracnidico",
    "ampolas_antibotropico_laquetico",
    "ampolas_antielapidico",
    "ampolas_antiloxoscelico",
    "ampolas_antibotropico_crotalico",
    "ampolas_antiescorpionico",
    "ampolas_antilonomico",
    "acidente_trabalho",
    "evolucao",
]

dados_tratados = dados[colunas_base_tratada].copy()

print(
    f"Base tratada pronta: {len(dados_tratados):,} registros e "
    f"{len(dados_tratados.columns)} colunas".replace(",", ".")
)
# =========================
# BASE TERRITORIAL
# =========================
print("\n[8/11] Carregando base territorial...")

ARQUIVO_DIVISOES = PASTA_DADOS / "divisoes.gpkg"
ID_DIVISOES = "1U94NZDIqgTXQPaBtmv7ZYxJNowN7XxQW"

if not ARQUIVO_DIVISOES.exists():
    print("Baixando divisoes.gpkg...")
    gdown.download(
        id=ID_DIVISOES,
        output=str(ARQUIVO_DIVISOES),
        quiet=False
    )

divisoes = gpd.read_file(ARQUIVO_DIVISOES)

print(f"Base territorial carregada: {len(divisoes)} municípios")

# Conferências opcionais:
# print(pyogrio.list_layers(ARQUIVO_DIVISOES))
# print(divisoes.columns.tolist())
# print(divisoes.drop(columns="geometry").head())

# =========================
# VALIDAÇÃO TERRITORIAL
# =========================
print("\n[9/11] Validando códigos municipais...")

def normalizar_codigo_municipio(coluna):
    codigo = (
        pd.to_numeric(coluna, errors="coerce")
        .astype("Int64")
        .astype("string")
    )

    # A base territorial utiliza o código municipal com 6 dígitos.
    # Caso o código possua 7 dígitos, remove o dígito verificador final.
    codigo = codigo.where(
        codigo.str.len() != 7,
        codigo.str[:6]
    )

    return pd.to_numeric(
        codigo,
        errors="coerce"
    ).astype("Int64")

divisoes["Codigo Municipio"] = normalizar_codigo_municipio(
    divisoes["Codigo Municipio"]
)

dados_tratados["municipio_ocorrencia_codigo"] = normalizar_codigo_municipio(
    dados_tratados["municipio_ocorrencia_codigo"]
)

dados_tratados["municipio_notificacao_codigo"] = normalizar_codigo_municipio(
    dados_tratados["municipio_notificacao_codigo"]
)

codigos_municipios = divisoes["Codigo Municipio"].dropna().unique()

erro_ocorrencia = ~dados_tratados[
    "municipio_ocorrencia_codigo"
].isin(codigos_municipios)

erro_notificacao = ~dados_tratados[
    "municipio_notificacao_codigo"
].isin(codigos_municipios)

erro_territorial = erro_ocorrencia | erro_notificacao

n_erro_ocorrencia = int(erro_ocorrencia.sum())
n_erro_notificacao = int(erro_notificacao.sum())
n_erro_total = int(erro_territorial.sum())

print(
    f"Ocorrência inválida: {n_erro_ocorrencia:,} | "
    f"Notificação inválida: {n_erro_notificacao:,} | "
    f"Total com erro: {n_erro_total:,}"
    .replace(",", ".")
)

# Conferência opcional dos códigos não encontrados:
# if n_erro_total > 0:
#     print("\nCódigos de ocorrência não encontrados:")
#     print(
#         dados_tratados.loc[
#             erro_ocorrencia,
#             "municipio_ocorrencia_codigo"
#         ].value_counts(dropna=False)
#     )
#
#     print("\nCódigos de notificação não encontrados:")
#     print(
#         dados_tratados.loc[
#             erro_notificacao,
#             "municipio_notificacao_codigo"
#         ].value_counts(dropna=False)
#     )

# print("\nExemplos de códigos:")
# print(
#     "Base territorial:",
#     divisoes["Codigo Municipio"].dropna().unique()[:5]
# )
# print(
#     "Ocorrência:",
#     dados_tratados["municipio_ocorrencia_codigo"].dropna().unique()[:5]
# )
# print(
#     "Notificação:",
#     dados_tratados["municipio_notificacao_codigo"].dropna().unique()[:5]
# )

dados_tratados = dados_tratados.loc[~erro_territorial].copy()

print(
    f"Registros válidos: "
    f"{len(dados_tratados):,}".replace(",", ".")
)

# =========================
# ENRIQUECIMENTO TERRITORIAL
# =========================
print("\n[10/11] Adicionando informações territoriais...")

territorio = divisoes.drop(columns="geometry").copy()

# -------------------------
# Município de ocorrência
# -------------------------
territorio_ocorrencia = territorio[[
    "Codigo Municipio",
    "Municipio",
    "Codigo Macrorregiao de Saude",
    "Macrorregiao de Saude",
    "Codigo Regiao de Saude",
    "Regiao de Saude",
    "Codigo Departamento Regional de Saude",
    "Departamento Regional de Saude",
    "Codigo Grupo de Vigilancia Epidemiologica",
    "Grupo de Vigilancia Epidemiologica",
    "Area km2",
    "Populacao Estimada IBGE 2022",
    "Latitude",
    "Longitude",
]].rename(columns={
    "Codigo Municipio": "municipio_ocorrencia_codigo",
    "Municipio": "municipio_ocorrencia",
    "Codigo Macrorregiao de Saude": "rras_ocorrencia_codigo",
    "Macrorregiao de Saude": "rras_ocorrencia",
    "Codigo Regiao de Saude": "regiao_saude_ocorrencia_codigo",
    "Regiao de Saude": "regiao_saude_ocorrencia",
    "Codigo Departamento Regional de Saude": "drs_ocorrencia_codigo",
    "Departamento Regional de Saude": "drs_ocorrencia",
    "Codigo Grupo de Vigilancia Epidemiologica": "gve_ocorrencia_codigo",
    "Grupo de Vigilancia Epidemiologica": "gve_ocorrencia",
    "Area km2": "area_ocorrencia_km2",
    "Populacao Estimada IBGE 2022": "populacao_ocorrencia",
    "Latitude": "latitude_ocorrencia",
    "Longitude": "longitude_ocorrencia",
})

dados_tratados = dados_tratados.merge(
    territorio_ocorrencia,
    on="municipio_ocorrencia_codigo",
    how="left",
    validate="many_to_one"
)

# -------------------------
# Município de notificação
# -------------------------
territorio_notificacao = territorio[[
    "Codigo Municipio",
    "Municipio",
    "Codigo Macrorregiao de Saude",
    "Macrorregiao de Saude",
    "Codigo Regiao de Saude",
    "Regiao de Saude",
    "Codigo Departamento Regional de Saude",
    "Departamento Regional de Saude",
    "Codigo Grupo de Vigilancia Epidemiologica",
    "Grupo de Vigilancia Epidemiologica",
    "Area km2",
    "Populacao Estimada IBGE 2022",
    "Latitude",
    "Longitude",
]].rename(columns={
    "Codigo Municipio": "municipio_notificacao_codigo",
    "Municipio": "municipio_notificacao",
    "Codigo Macrorregiao de Saude": "rras_notificacao_codigo",
    "Macrorregiao de Saude": "rras_notificacao",
    "Codigo Regiao de Saude": "regiao_saude_notificacao_codigo",
    "Regiao de Saude": "regiao_saude_notificacao",
    "Codigo Departamento Regional de Saude": "drs_notificacao_codigo",
    "Departamento Regional de Saude": "drs_notificacao",
    "Codigo Grupo de Vigilancia Epidemiologica": "gve_notificacao_codigo",
    "Grupo de Vigilancia Epidemiologica": "gve_notificacao",
    "Area km2": "area_notificacao_km2",
    "Populacao Estimada IBGE 2022": "populacao_notificacao",
    "Latitude": "latitude_notificacao",
    "Longitude": "longitude_notificacao",
})

dados_tratados = dados_tratados.merge(
    territorio_notificacao,
    on="municipio_notificacao_codigo",
    how="left",
    validate="many_to_one"
)

# =========================
# DISTÂNCIA ENTRE MUNICÍPIOS
# =========================
print("\n[11/11] Calculando distância entre ocorrência e notificação...")

# Distância em linha reta entre as coordenadas de referência dos municípios,
# calculada pela fórmula de Haversine. Não representa distância rodoviária.
lat_ocorrencia = np.radians(dados_tratados["latitude_ocorrencia"])
lon_ocorrencia = np.radians(dados_tratados["longitude_ocorrencia"])
lat_notificacao = np.radians(dados_tratados["latitude_notificacao"])
lon_notificacao = np.radians(dados_tratados["longitude_notificacao"])

delta_lat = lat_notificacao - lat_ocorrencia
delta_lon = lon_notificacao - lon_ocorrencia

a = (
    np.sin(delta_lat / 2) ** 2
    + np.cos(lat_ocorrencia)
    * np.cos(lat_notificacao)
    * np.sin(delta_lon / 2) ** 2
)

c = 2 * np.arctan2(
    np.sqrt(a),
    np.sqrt(1 - a)
)

RAIO_TERRA_KM = 6371.0088
dados_tratados["distancia_km"] = (RAIO_TERRA_KM * c).round(2)

print(
    f"Distâncias calculadas: "
    f"{dados_tratados['distancia_km'].notna().sum():,} registros."
    .replace(",", ".")
)

# Conferência opcional:
# print(dados_tratados[
#     ["municipio_ocorrencia", "municipio_notificacao", "distancia_km"]
# ].head(20))
#
# print("\nResumo das distâncias:")
# print(dados_tratados["distancia_km"].describe())

dados_tratados.to_csv(
    ARQUIVO_SAIDA,
    index=False,
    encoding="utf-8-sig"
)

print(
    f"Base final salva: "
    f"{len(dados_tratados):,} registros e "
    f"{len(dados_tratados.columns)} colunas"
    .replace(",", ".")
)

print(f"Arquivo: {ARQUIVO_SAIDA}")
print(
    f"\nTratamento concluído com sucesso. "
    f"A base de dados tratada contém {len(dados_tratados):,} registros "
    f"e {len(dados_tratados.columns)} colunas."
    .replace(",", ".")
)