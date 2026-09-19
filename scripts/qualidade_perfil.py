from pathlib import Path
import pandas as pd

# ============================================================
# CONFIGURAÇÃO
# ============================================================
RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO = RAIZ / "dados_local" / "sinan_sp_tratado.csv"
PASTA_SAIDA = RAIZ / "dados_local"

COLUNAS_NECESSARIAS = [
    "idade_anos",
    "tipo_acidente",
    "raca_cor",
    "escolaridade",
    "tipo_serpente",
    "tipo_aranha",
    "tipo_lagarta",
]

CATEGORIAS_ESPERADAS = {
    "raca_cor": [
        "Branca",
        "Preta",
        "Amarela",
        "Parda",
        "Indígena",
        "Ignorado",
    ],
    "escolaridade": [
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
    ],
    "tipo_serpente": [
        "Botrópico",
        "Crotálico",
        "Elapídico",
        "Laquético",
        "Serpente não peçonhenta",
        "Ignorado",
    ],
    "tipo_aranha": [
        "Foneutrismo",
        "Loxoscelismo",
        "Latrodectismo",
        "Outra aranha",
        "Ignorado",
    ],
    "tipo_lagarta": [
        "Lonomia",
        "Outra lagarta",
        "Ignorado",
    ],
}

SUBTIPOS = {
    "Serpente": "tipo_serpente",
    "Aranha": "tipo_aranha",
    "Lagarta": "tipo_lagarta",
}


# ============================================================
# FUNÇÕES
# ============================================================
def percentual(parte, total):
    return 100 * parte / total if total else 0


def imprimir_titulo(titulo):
    print(f"\n{'=' * 64}")
    print(titulo)
    print("=" * 64)


def tabela_frequencia(serie, total_referencia=None):
    """Conta categorias mantendo ausentes separados."""
    serie_exibicao = serie.astype("string").fillna("Ausente")
    frequencia = (
        serie_exibicao
        .value_counts(dropna=False)
        .rename_axis("categoria")
        .reset_index(name="casos")
    )

    total = total_referencia if total_referencia is not None else len(serie)

    frequencia["percentual"] = (
        frequencia["casos"] / total * 100
    ).round(2)

    return frequencia


def resumo_qualidade(df, coluna, considerar_nao_se_aplica=False):
    total = len(df)
    ausentes = int(df[coluna].isna().sum())
    ignorados = int(df[coluna].eq("Ignorado").sum())
    nao_se_aplica = (
        int(df[coluna].eq("Não se aplica").sum())
        if considerar_nao_se_aplica
        else 0
    )

    informativos = total - ausentes - ignorados - nao_se_aplica

    return {
        "variavel": coluna,
        "total": total,
        "informativos": informativos,
        "pct_informativos": round(percentual(informativos, total), 2),
        "ignorados": ignorados,
        "pct_ignorados": round(percentual(ignorados, total), 2),
        "ausentes": ausentes,
        "pct_ausentes": round(percentual(ausentes, total), 2),
        "nao_se_aplica": nao_se_aplica,
        "pct_nao_se_aplica": round(percentual(nao_se_aplica, total), 2),
    }


# ============================================================
# 1. LEITURA E VALIDAÇÃO
# ============================================================
print("==============================================")
print("CONFERÊNCIA DE QUALIDADE — PERFIL E SUBTIPOS")
print("==============================================")
print("\n[1/5] Lendo base tratada...")

df = pd.read_csv(ARQUIVO, low_memory=False)

ausentes = [
    coluna
    for coluna in COLUNAS_NECESSARIAS
    if coluna not in df.columns
]

if ausentes:
    raise ValueError(
        "Colunas ausentes na base tratada: "
        + ", ".join(ausentes)
    )

print(f"Base carregada: {len(df):,} registros.".replace(",", "."))


# ============================================================
# 2. RAÇA/COR
# ============================================================
print("\n[2/5] Conferindo raça/cor...")

resumos = []
distribuicoes = []
inconsistencias = []

resumos.append(resumo_qualidade(df, "raca_cor"))

imprimir_titulo("RAÇA/COR")
freq = tabela_frequencia(df["raca_cor"])

for linha in freq.itertuples():
    print(
        f"{linha.categoria}: "
        f"{linha.casos:,} ({linha.percentual:.2f}%)"
        .replace(",", ".")
    )

freq.insert(0, "variavel", "raca_cor")
distribuicoes.append(freq)

valores_raca = set(df["raca_cor"].dropna().astype(str).unique())
inesperados_raca = valores_raca - set(CATEGORIAS_ESPERADAS["raca_cor"])

print(
    "\nCategorias inesperadas: "
    + (", ".join(sorted(inesperados_raca)) if inesperados_raca else "nenhuma")
)


# ============================================================
# 3. ESCOLARIDADE
# ============================================================
print("\n[3/5] Conferindo escolaridade...")

resumos.append(
    resumo_qualidade(
        df,
        "escolaridade",
        considerar_nao_se_aplica=True,
    )
)

imprimir_titulo("ESCOLARIDADE")
freq = tabela_frequencia(df["escolaridade"])

for linha in freq.itertuples():
    print(
        f"{linha.categoria}: "
        f"{linha.casos:,} ({linha.percentual:.2f}%)"
        .replace(",", ".")
    )

freq.insert(0, "variavel", "escolaridade")
distribuicoes.append(freq)

valores_escolaridade = set(
    df["escolaridade"].dropna().astype(str).unique()
)
inesperados_escolaridade = (
    valores_escolaridade
    - set(CATEGORIAS_ESPERADAS["escolaridade"])
)

print(
    "\nCategorias inesperadas: "
    + (
        ", ".join(sorted(inesperados_escolaridade))
        if inesperados_escolaridade
        else "nenhuma"
    )
)

idade = pd.to_numeric(df["idade_anos"], errors="coerce")

# Regra explícita do dicionário: acima de 7 anos não deve ser "Não se aplica".
escolaridade_nao_aplica_maior_7 = (
    idade.gt(7)
    & df["escolaridade"].eq("Não se aplica")
)

# Para menores de 7, a documentação informa preenchimento automático com 10.
menor_7_sem_nao_aplica = (
    idade.lt(7)
    & df["escolaridade"].notna()
    & ~df["escolaridade"].eq("Não se aplica")
)

print("\nConferências idade × escolaridade:")
print(
    "Idade > 7 com 'Não se aplica': "
    f"{int(escolaridade_nao_aplica_maior_7.sum()):,}"
    .replace(",", ".")
)
print(
    "Idade < 7 com outra categoria preenchida: "
    f"{int(menor_7_sem_nao_aplica.sum()):,}"
    .replace(",", ".")
)

inconsistencias.extend([
    {
        "verificacao": "escolaridade_nao_se_aplica_com_idade_maior_7",
        "casos": int(escolaridade_nao_aplica_maior_7.sum()),
    },
    {
        "verificacao": "idade_menor_7_com_escolaridade_diferente_nao_se_aplica",
        "casos": int(menor_7_sem_nao_aplica.sum()),
    },
])


# ============================================================
# 4. SUBTIPOS / ESPÉCIES
# ============================================================
print("\n[4/5] Conferindo subtipos dos animais...")

for animal, coluna in SUBTIPOS.items():
    base_animal = df.loc[df["tipo_acidente"].eq(animal)].copy()
    total_animal = len(base_animal)

    imprimir_titulo(f"{animal.upper()} — {coluna}")

    ausentes_subtipo = int(base_animal[coluna].isna().sum())
    ignorados_subtipo = int(base_animal[coluna].eq("Ignorado").sum())
    informativos_subtipo = (
        total_animal - ausentes_subtipo - ignorados_subtipo
    )

    print(
        f"Total de acidentes por {animal.lower()}: "
        f"{total_animal:,}".replace(",", ".")
    )
    print(
        f"Subtipo informativo: {informativos_subtipo:,} "
        f"({percentual(informativos_subtipo, total_animal):.2f}%)"
        .replace(",", ".")
    )
    print(
        f"Ignorado: {ignorados_subtipo:,} "
        f"({percentual(ignorados_subtipo, total_animal):.2f}%)"
        .replace(",", ".")
    )
    print(
        f"Ausente: {ausentes_subtipo:,} "
        f"({percentual(ausentes_subtipo, total_animal):.2f}%)"
        .replace(",", ".")
    )

    freq = tabela_frequencia(
        base_animal[coluna],
        total_referencia=total_animal,
    )

    print("\nDistribuição:")
    for linha in freq.itertuples():
        print(
            f"{linha.categoria}: "
            f"{linha.casos:,} ({linha.percentual:.2f}%)"
            .replace(",", ".")
        )

    freq.insert(0, "variavel", coluna)
    distribuicoes.append(freq)

    resumos.append({
        "variavel": coluna,
        "total": total_animal,
        "informativos": informativos_subtipo,
        "pct_informativos": round(
            percentual(informativos_subtipo, total_animal), 2
        ),
        "ignorados": ignorados_subtipo,
        "pct_ignorados": round(
            percentual(ignorados_subtipo, total_animal), 2
        ),
        "ausentes": ausentes_subtipo,
        "pct_ausentes": round(
            percentual(ausentes_subtipo, total_animal), 2
        ),
        "nao_se_aplica": 0,
        "pct_nao_se_aplica": 0,
    })

    valores_subtipo = set(
        base_animal[coluna].dropna().astype(str).unique()
    )
    inesperados = (
        valores_subtipo
        - set(CATEGORIAS_ESPERADAS[coluna])
    )

    print(
        "\nCategorias inesperadas: "
        + (", ".join(sorted(inesperados)) if inesperados else "nenhuma")
    )

    # O campo de subtipo não deveria estar preenchido para outro tipo de acidente.
    preenchido_fora_tipo = int(
        (
            ~df["tipo_acidente"].eq(animal)
            & df[coluna].notna()
            & ~df[coluna].eq("Ignorado")
        ).sum()
    )

    print(
        f"Campo preenchido fora de '{animal}': "
        f"{preenchido_fora_tipo:,}".replace(",", ".")
    )

    inconsistencias.append({
        "verificacao": f"{coluna}_preenchido_fora_de_{animal.lower()}",
        "casos": preenchido_fora_tipo,
    })


# ============================================================
# 5. SAÍDA
# ============================================================
print("\n[5/5] Salvando resultados...")

df_resumo = pd.DataFrame(resumos)
df_distribuicoes = pd.concat(distribuicoes, ignore_index=True)
df_inconsistencias = pd.DataFrame(inconsistencias)

arquivo_resumo = PASTA_SAIDA / "qualidade_perfil_resumo.csv"
arquivo_distribuicoes = (
    PASTA_SAIDA / "qualidade_perfil_distribuicoes.csv"
)
arquivo_inconsistencias = (
    PASTA_SAIDA / "qualidade_perfil_inconsistencias.csv"
)

df_resumo.to_csv(arquivo_resumo, index=False)
df_distribuicoes.to_csv(arquivo_distribuicoes, index=False)
df_inconsistencias.to_csv(arquivo_inconsistencias, index=False)

print("\nArquivos gerados:")
print(f"- {arquivo_resumo}")
print(f"- {arquivo_distribuicoes}")
print(f"- {arquivo_inconsistencias}")

print("\nConferência concluída.")
