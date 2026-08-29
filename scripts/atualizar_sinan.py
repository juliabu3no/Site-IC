from pathlib import Path
from datetime import datetime
import pandas as pd
from pysus import sinan


# =========================
# CONFIGURAÇÕES
# =========================

# Primeiro ano utilizado no projeto
ANO_INICIAL = 2007

# Tenta baixar dados até o ano atual
ANO_FINAL = datetime.now().year

# Código IBGE da UF de São Paulo
CODIGO_UF_SP = 35

# Código SINAN para acidentes por animais peçonhentos
AGRAVO = "ANIM"

# Tipos de acidente registrados no SINAN
TIPOS_ANIMAL = {
    1: "Serpente",
    2: "Aranha",
    3: "Escorpião",
    4: "Lagarta",
    5: "Abelha",
    6: "Outros",
    9: "Ignorado",
}

# Siglas das Unidades Federativas
UF_SIGLAS = {
    11: "RO",
    12: "AC",
    13: "AM",
    14: "RR",
    15: "PA",
    16: "AP",
    17: "TO",
    21: "MA",
    22: "PI",
    23: "CE",
    24: "RN",
    25: "PB",
    26: "PE",
    27: "AL",
    28: "SE",
    29: "BA",
    31: "MG",
    32: "ES",
    33: "RJ",
    35: "SP",
    41: "PR",
    42: "SC",
    43: "RS",
    50: "MS",
    51: "MT",
    52: "GO",
    53: "DF",
}


# =========================
# CAMINHOS
# =========================
RAIZ = Path(__file__).resolve().parent.parent
PASTA_DADOS = RAIZ / "dados_local"
PASTA_DADOS.mkdir(parents=True, exist_ok=True)

ARQUIVO_SAIDA = (PASTA_DADOS / "sinan_animais_peconhentos_sp.csv") # Base completa contendo apenas registros relacionados a SP
ARQUIVO_RESUMO = (PASTA_DADOS / "resumo_sinan_por_ano.csv") # Resumo Brasil x SP por ano
ARQUIVO_RESUMO_UF_ANIMAL = (PASTA_DADOS / "resumo_sinan_uf_ano_animal.csv") # Resumo nacional por ano, UF e tipo de animal

# =========================
# DOWNLOAD
# =========================
anos = list(range(ANO_INICIAL, ANO_FINAL + 1))

print("======================================")
print("ATUALIZAÇÃO DOS DADOS DO SINAN")
print("======================================")
print(f"Agravo: {AGRAVO}")
print("Filtro da base de SP: ANT_UF = 35 e SG_UF_NOT = 35")
print(f"Período: {ANO_INICIAL} a {ANO_FINAL}")
print()

bases = []
resumo_anos = []   # Resumo Brasil x SP
resumos_uf_animal = []  # Resumo nacional por UF e animal


for ano in anos:
    print(f"Baixando {ano}...")

    try:
        # O SINAN disponibiliza o arquivo nacional.
        # O filtro de São Paulo é realizado posteriormente.
        df_ano = sinan(
            disease=AGRAVO,
            year=ano,
            as_dataframe=True,
        )

        if df_ano is None or df_ano.empty:
            print(f"  Nenhum dado encontrado para {ano}.")
            continue

        # =========================
        # TOTAL DO BRASIL
        # =========================

        n_brasil = len(df_ano)
        print(f"  {n_brasil:,} registros encontrados no Brasil.".replace(",", "."))

        # =========================
        # VERIFICA COLUNAS
        # =========================
        colunas_necessarias = {
            "ANT_UF",
            "SG_UF_NOT",
            "TP_ACIDENT",
        }

        if not colunas_necessarias.issubset(df_ano.columns):
            faltantes = (colunas_necessarias - set(df_ano.columns))
            print(f"  Colunas ausentes em {ano}: " f"{', '.join(sorted(faltantes))}. " "Ano ignorado.")
            continue

        # =========================
        # PADRONIZA VARIÁVEIS
        # =========================

        df_ano["ANT_UF"] = pd.to_numeric(df_ano["ANT_UF"], errors="coerce", )
        df_ano["SG_UF_NOT"] = pd.to_numeric(df_ano["SG_UF_NOT"], errors="coerce",)
        df_ano["TP_ACIDENT"] = pd.to_numeric(df_ano["TP_ACIDENT"],errors="coerce",)

        # =========================
        # RESUMO NACIONAL: ANO × UF × ANIMAL
        # =========================
        resumo_aux = (
            df_ano
            .groupby(
                ["ANT_UF", "TP_ACIDENT"],
                dropna=False,
            )
            .size()
            .reset_index(name="registros")
        )

        resumo_aux.insert(
            0,
            "ano",
            ano,
        )

        # Nome da UF
        resumo_aux["uf"] = (
            resumo_aux["ANT_UF"]
            .map(UF_SIGLAS)
            .fillna("Não informado")
        )

        # Nome do animal
        resumo_aux["animal"] = (
            resumo_aux["TP_ACIDENT"]
            .map(TIPOS_ANIMAL)
            .fillna("Não informado")
        )

        # Renomeia códigos para deixar o CSV claro
        resumo_aux = resumo_aux.rename(
            columns={
                "ANT_UF": "codigo_uf",
                "TP_ACIDENT": "codigo_animal",
            }
        )

        # Ordem final das colunas
        resumo_aux = resumo_aux[
            [
                "ano",
                "codigo_uf",
                "uf",
                "codigo_animal",
                "animal",
                "registros",
            ]
        ]

        resumos_uf_animal.append(
            resumo_aux
        )

        # =========================
        # FILTRO DE SÃO PAULO
        # =========================

        # Mantém registros em que:
        # - o acidente ocorreu em SP
        # E
        # - a notificação foi realizada em SP

        df_sp = df_ano[
            (df_ano["ANT_UF"] == CODIGO_UF_SP)
            & (
                df_ano["SG_UF_NOT"]
                == CODIGO_UF_SP
            )
        ].copy()


        n_sp = len(df_sp)

        print(
            f"  {n_sp:,} registros mantidos após o filtro de SP."
            .replace(",", ".")
        )

        # =========================
        # RESUMO BRASIL × SP
        # =========================

        resumo_anos.append(
            {
                "ano": ano,
                "registros_brasil": n_brasil,
                "registros_sp": n_sp,
                "percentual_sp": round(
                    (n_sp / n_brasil) * 100,
                    2,
                ),
            }
        )

        if not df_sp.empty:
            bases.append(df_sp)

    except Exception as erro:
        print(f"  Erro ao baixar {ano}: {erro}")


# =========================
# VERIFICA RESULTADOS
# =========================

if not bases:
    raise RuntimeError("Nenhum dado de São Paulo foi obtido do SINAN.")


# =========================
# JUNTA BASE DE SP
# =========================

print()
print("Unindo os arquivos de São Paulo...")
df = pd.concat(bases, ignore_index=True, sort=False,)


# =========================
# SALVA CSV BRUTO DE SP
# =========================

print("Salvando CSV de São Paulo...")
df.to_csv(ARQUIVO_SAIDA, index=False, encoding="utf-8-sig",)


# =========================
# SALVA RESUMO POR ANO
# =========================

print("Salvando resumo Brasil x SP por ano...")

df_resumo = pd.DataFrame(resumo_anos)

df_resumo.to_csv(ARQUIVO_RESUMO, index=False, encoding="utf-8-sig",)


# =========================
# SALVA RESUMO: ANO × UF × ANIMAL
# =========================

print("Salvando resumo nacional por UF e animal...")

if resumos_uf_animal:
    df_resumo_uf_animal = pd.concat(
        resumos_uf_animal,
        ignore_index=True,
    )

    df_resumo_uf_animal.to_csv(
        ARQUIVO_RESUMO_UF_ANIMAL,
        index=False,
        encoding="utf-8-sig",
    )


# =========================
# RESUMO FINAL
# =========================

print()
print("======================================")
print("ATUALIZAÇÃO CONCLUÍDA")
print("======================================")

print("Total de registros de SP:", f"{len(df):,}".replace(",", "."),)
print("Total de colunas:", len(df.columns),)

print()
print("Base de SP:")
print(ARQUIVO_SAIDA)

print()
print("Resumo Brasil x SP:")
print(ARQUIVO_RESUMO)

print()
print("Resumo por UF, ano e animal:")
print(ARQUIVO_RESUMO_UF_ANIMAL)