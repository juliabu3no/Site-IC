from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO = RAIZ / "dados_local" / "sinan_sp_tratado.csv"

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

df = pd.read_csv(ARQUIVO, low_memory=False)
distribuicoes = []

for coluna, nome in COLUNAS_SOROS.items():
    valores = pd.to_numeric(df[coluna], errors="coerce")
    valores = valores[valores > 0]

    print(f"\n{'=' * 50}")
    print(nome)
    print(f"{'=' * 50}")

    if valores.empty:
        print("Nenhum uso registrado.")
        continue

    print(f"Casos com uso: {len(valores):,}".replace(",", "."))
    print(f"Mínimo: {valores.min():g}")
    print(f"Mediana: {valores.median():g}")
    print(f"Máximo: {valores.max():g}")
    print(f"Valores diferentes: {valores.nunique()}")

    frequencia = (
        valores.value_counts()
        .sort_index()
        .rename_axis("numero_ampolas")
        .reset_index(name="casos")
    )

    print("\nNúmero de ampolas | Casos")
    for linha in frequencia.itertuples():
        print(f"{linha.numero_ampolas:g} | {linha.casos}")

    frequencia.insert(0, "soro", nome)
    distribuicoes.append(frequencia)

resultado = pd.concat(distribuicoes, ignore_index=True)

saida = RAIZ / "dados_local" / "distribuicao_ampolas_soros.csv"
resultado.to_csv(saida, index=False)

print(f"\nArquivo salvo em: {saida}")