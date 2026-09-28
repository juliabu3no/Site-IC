from http.server import BaseHTTPRequestHandler
from pathlib import Path
import json
import math
import os
import re
import requests

BASE_DIR = Path(__file__).resolve().parents[1]
ARQUIVO_DADOS = BASE_DIR / "public" / "data" / "atendimento.json"
ORS_API_KEY = os.getenv("ORS_API_KEY")

PERFIS_ORS = {
    "carro": "driving-car",
    "bicicleta": "cycling-regular",
    "caminhando": "foot-walking",
}

SOROS = {
    ("serpente", "jararaca"): "Botrópico",
    ("serpente", "cascavel"): "Crotálico",
    ("serpente", "coral"): "Elapídico",
    ("serpente", "surucucu"): "Laquético",
    ("aranha", "marrom"): "Loxoscélico",
    ("aranha", "armadeira"): "Fonêutrico",
    ("escorpiao", "tityus"): "Escorpiônico",
    ("lagarta", "lonomia"): "Lonômico",
}

ROTULOS_SORO = {
    "Botrópico": "Soro antibotrópico",
    "Crotálico": "Soro anticrotálico",
    "Elapídico": "Soro antielapídico",
    "Laquético": "Soro antilaquético",
    "Loxoscélico": "Soro antiloxoscélico",
    "Fonêutrico": "Soro antifonêutrico",
    "Escorpiônico": "Soro antiescorpiônico",
    "Lonômico": "Soro antilonômico",
}

with open(ARQUIVO_DADOS, encoding="utf-8") as arquivo:
    DADOS = json.load(arquivo)

POSTOS = {int(posto["id"]): posto for posto in DADOS["postos"]}

def resposta(handler, status, dados):
    corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(corpo)))
    handler.end_headers()
    handler.wfile.write(corpo)

def normalizar_cep(valor):
    numeros = re.sub(r"\D", "", valor or "")
    return numeros if len(numeros) == 8 else None

def endereco_por_cep(cep):
    resposta_cep = requests.get(
        f"https://viacep.com.br/ws/{cep}/json/",
        timeout=8,
    )
    resposta_cep.raise_for_status()
    dados = resposta_cep.json()
    if dados.get("erro"):
        raise ValueError("CEP não encontrado.")

    partes = [
        dados.get("logradouro"),
        dados.get("bairro"),
        dados.get("localidade"),
        dados.get("uf"),
        "Brasil",
    ]
    return ", ".join(str(parte) for parte in partes if parte)

def geocodificar(localizacao):
    if not ORS_API_KEY:
        raise RuntimeError("ORS_API_KEY não configurada no servidor.")

    cep = normalizar_cep(localizacao)
    texto_busca = endereco_por_cep(cep) if cep and re.fullmatch(r"[\d\-\s]+", localizacao) else localizacao

    resposta_geo = requests.get(
        "https://api.openrouteservice.org/geocode/search",
        params={
            "api_key": ORS_API_KEY,
            "text": texto_busca,
            "boundary.country": "BR",
            "size": 1,
        },
        timeout=12,
    )
    resposta_geo.raise_for_status()
    dados = resposta_geo.json()

    if not dados.get("features"):
        raise ValueError("Endereço não encontrado.")

    feature = dados["features"][0]
    longitude, latitude = feature["geometry"]["coordinates"]
    rotulo = feature.get("properties", {}).get("label") or texto_busca

    if not (-25.6 <= latitude <= -19.5 and -53.2 <= longitude <= -44.0):
        raise ValueError("O endereço encontrado parece estar fora do estado de São Paulo.")

    return {
        "latitude": float(latitude),
        "longitude": float(longitude),
        "rotulo": rotulo,
    }

def haversine(lat1, lon1, lat2, lon2):
    raio = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    )
    return 2 * raio * math.asin(math.sqrt(a))

def municipio_mais_proximo(latitude, longitude):
    return min(
        DADOS["municipios"],
        key=lambda municipio: haversine(
            latitude,
            longitude,
            municipio["latitude"],
            municipio["longitude"],
        ),
    )

def calcular_rotas(origem, candidatos, perfil):
    locations = [[origem["longitude"], origem["latitude"]]]

    postos_candidatos = []
    for id_posto in candidatos:
        posto = POSTOS.get(int(id_posto))
        if not posto:
            continue
        postos_candidatos.append(posto)
        locations.append([posto["longitude"], posto["latitude"]])

    if not postos_candidatos:
        return []

    resposta_matriz = requests.post(
        f"https://api.openrouteservice.org/v2/matrix/{perfil}",
        headers={
            "Authorization": ORS_API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "locations": locations,
            "metrics": ["distance", "duration"],
            "units": "km",
            "sources": [0],
            "destinations": list(range(1, len(locations))),
        },
        timeout=20,
    )
    resposta_matriz.raise_for_status()
    matriz = resposta_matriz.json()

    distancias = matriz.get("distances", [[]])[0]
    duracoes = matriz.get("durations", [[]])[0]

    resultados = []
    for i, posto in enumerate(postos_candidatos):
        if i >= len(distancias) or distancias[i] is None:
            continue

        resultado = dict(posto)
        resultado["distancia_km"] = round(float(distancias[i]), 2)
        resultado["tempo_min"] = (
            round(float(duracoes[i]) / 60, 1)
            if i < len(duracoes) and duracoes[i] is not None
            else None
        )
        resultados.append(resultado)

    # Mantém a lógica do notebook: o recomendado é o de menor distância real.
    resultados.sort(key=lambda item: item["distancia_km"])
    return resultados

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_POST(self):
        try:
            tamanho = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(tamanho) or b"{}")

            localizacao = str(payload.get("localizacao", "")).strip()
            animal = str(payload.get("animal", "")).strip()
            especie = str(payload.get("especie", "")).strip()
            transporte = str(payload.get("transporte", "carro")).strip()

            if not localizacao:
                return resposta(self, 400, {"erro": "Informe um endereço ou CEP."})

            if transporte not in PERFIS_ORS:
                return resposta(self, 400, {"erro": "Modo de transporte inválido."})

            origem = geocodificar(localizacao)
            municipio = municipio_mais_proximo(
                origem["latitude"],
                origem["longitude"],
            )

            soro = SOROS.get((animal, especie))
            especie_desconhecida = especie in {"", "nao_sei"}

            if animal == "aranha" and especie == "viuva_negra":
                return resposta(self, 200, {
                    "status": "soro_nao_modelado",
                    "origem": origem,
                    "municipio_referencia": municipio["municipio"],
                    "mensagem": (
                        "A opção viúva-negra não está representada pelos oito tipos "
                        "de soro modelados nesta base. Procure atendimento de urgência."
                    ),
                })

            if soro:
                candidatos = municipio["candidatos_por_soro"].get(soro, [])
                soro_rotulo = ROTULOS_SORO[soro]
                status = "soro_definido"
            elif especie_desconhecida:
                candidatos = municipio["candidatos_geral"]
                soro_rotulo = None
                status = "especie_desconhecida"
            else:
                return resposta(self, 400, {
                    "erro": "Não foi possível relacionar a seleção a um soro modelado."
                })

            resultados = calcular_rotas(
                origem,
                candidatos,
                PERFIS_ORS[transporte],
            )

            if not resultados:
                return resposta(self, 404, {
                    "erro": "Nenhuma unidade com rota válida foi encontrada."
                })

            return resposta(self, 200, {
                "status": status,
                "origem": origem,
                "municipio_referencia": municipio["municipio"],
                "soro": soro,
                "soro_rotulo": soro_rotulo,
                "transporte": transporte,
                "recomendado": resultados[0],
                "postos": resultados[:10],
                "aviso": (
                    "A indicação definitiva do soro e a conduta clínica dependem "
                    "da avaliação da equipe de saúde."
                ),
            })

        except ValueError as erro:
            return resposta(self, 400, {"erro": str(erro)})
        except requests.RequestException:
            return resposta(self, 502, {
                "erro": "Não foi possível consultar o serviço de rotas neste momento."
            })
        except Exception as erro:
            print("Erro em encontrar_atendimento:", repr(erro))
            return resposta(self, 500, {
                "erro": "Ocorreu um erro ao buscar a unidade de atendimento."
            })
