# api_protheus.py — Autenticação e chamadas REST ao FWModel do Protheus

import base64
import time
import requests
import urllib3

# Suprime aviso de SSL auto-assinado — esperado neste ambiente
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def montar_cabecalhos(usuario: str, senha: str) -> dict:
    """Gera cabeçalho Authorization com Basic Auth em Base64."""
    credencial = f"{usuario}:{senha}"
    token = base64.b64encode(credencial.encode("utf-8")).decode("utf-8")
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
    }


def montar_payload(registro: dict, filial: str) -> dict:
    """Monta o envelope JSON no formato FWModel para inclusão (operation=3)."""
    campos = [
        {"id": "A1_FILIAL",  "value": filial},
        {"id": "A1_COD",     "value": ""},          # auto-gerado pelo Protheus
        {"id": "A1_LOJA",    "value": "0001"},
        {"id": "A1_NOME",    "value": registro.get("A1_NOME", "")},
        {"id": "A1_NREDUZ",  "value": registro.get("A1_NREDUZ", "")},
        {"id": "A1_PESSOA",  "value": registro.get("A1_PESSOA", "")},
        {"id": "A1_TIPO",    "value": registro.get("A1_TIPO", "F")},
        {"id": "A1_CGC",     "value": registro.get("A1_CGC", "")},
        {"id": "A1_END",     "value": registro.get("A1_END", "")},
        {"id": "A1_BAIRRO",  "value": registro.get("A1_BAIRRO", "")},
        {"id": "A1_MUN",     "value": registro.get("A1_MUN", "")},
        {"id": "A1_EST",     "value": registro.get("A1_EST", "")},
        {"id": "A1_CEP",     "value": registro.get("A1_CEP", "")},
        {"id": "A1_PAIS",    "value": "105"},
        {"id": "A1_DDD",     "value": registro.get("A1_DDD", "")},
        {"id": "A1_TEL",     "value": registro.get("A1_TEL", "")},
        {"id": "A1_EMAIL",   "value": registro.get("A1_EMAIL", "")},
        {"id": "A1_CONTATO", "value": registro.get("A1_CONTATO", "")},
        {"id": "A1_TPESSOA", "value": "CI" if registro.get("A1_PESSOA") == "J" else "PF"},
        {"id": "A1_CODPAIS", "value": "01058"},
        {"id": "A1_TIPCLI",  "value": "1"},
        {"id": "A1_XCONCEI", "value": "LIBERADO"},   # campo customizado Green Máquinas
        {"id": "A1_XFGNFS",  "value": "2"},           # campo customizado Green Máquinas
    ]

    return {
        "id": "MATA030",
        "operation": 3,  # 3 = inclusão
        "models": [
            {
                "id": "MATA030_SA1",
                "modeltype": "FIELDS",
                "fields": campos,
            }
        ],
    }


def enviar_cliente(url: str, cabecalhos: dict, payload: dict, timeout: int, verify_ssl: bool, max_retries: int) -> dict:
    """
    Faz o POST ao endpoint FWModel.
    Retorna dict com 'sucesso', 'codigo', 'mensagem', 'http_status'.
    Tenta novamente até max_retries em caso de timeout ou erro 500.
    """
    tentativa = 0

    while tentativa <= max_retries:
        tentativa += 1
        try:
            resposta = requests.post(
                url,
                json=payload,
                headers=cabecalhos,
                timeout=timeout,
                verify=verify_ssl,
            )

            status = resposta.status_code

            # Credencial inválida — interrompe tudo
            if status == 401:
                return {
                    "sucesso": False,
                    "codigo": None,
                    "mensagem": "Credencial inválida (HTTP 401) — verifique usuário/senha no config.yaml",
                    "http_status": status,
                    "fatal": True,
                }

            # Endpoint não encontrado — interrompe tudo
            if status == 404:
                return {
                    "sucesso": False,
                    "codigo": None,
                    "mensagem": "Endpoint não encontrado (HTTP 404) — verifique a URL no config.yaml",
                    "http_status": status,
                    "fatal": True,
                }

            if status in (200, 201):
                codigo = _extrair_codigo(resposta.json())
                return {
                    "sucesso": True,
                    "codigo": codigo,
                    "mensagem": "Cadastrado com sucesso",
                    "http_status": status,
                    "fatal": False,
                }

            # Erro de validação do Protheus (400)
            if status == 400:
                mensagem = _extrair_erro(resposta)
                return {
                    "sucesso": False,
                    "codigo": None,
                    "mensagem": mensagem,
                    "http_status": status,
                    "fatal": False,
                }

            # Erro interno (500) — tenta novamente
            if status == 500 and tentativa <= max_retries:
                time.sleep(2)
                continue

            mensagem = _extrair_erro(resposta)
            return {
                "sucesso": False,
                "codigo": None,
                "mensagem": mensagem,
                "http_status": status,
                "fatal": False,
            }

        except requests.exceptions.Timeout:
            if tentativa <= max_retries:
                time.sleep(2)
                continue
            return {
                "sucesso": False,
                "codigo": None,
                "mensagem": "Timeout — sem resposta do servidor",
                "http_status": "TIMEOUT",
                "fatal": False,
            }

        except requests.exceptions.ConnectionError as e:
            return {
                "sucesso": False,
                "codigo": None,
                "mensagem": f"Erro de conexão: {e}",
                "http_status": "CONN_ERROR",
                "fatal": True,
            }

    return {
        "sucesso": False,
        "codigo": None,
        "mensagem": f"Falhou após {max_retries} tentativas",
        "http_status": "MAX_RETRIES",
        "fatal": False,
    }


def _extrair_codigo(json_resp: dict) -> str:
    """Tenta extrair o A1_COD gerado pelo Protheus na resposta de sucesso."""
    try:
        modelos = json_resp.get("models", [])
        for modelo in modelos:
            for campo in modelo.get("fields", []):
                if campo.get("id") == "A1_COD":
                    loja = ""
                    for c in modelo.get("fields", []):
                        if c.get("id") == "A1_LOJA":
                            loja = c.get("value", "").strip()
                    return f"{campo.get('value', '').strip()}-{loja}"
    except Exception:
        pass
    return "N/D"


def _extrair_erro(resposta) -> str:
    """Extrai a mensagem de erro do padrão {'errorCode': ..., 'errorMessage': ...}."""
    try:
        dados = resposta.json()
        return dados.get("errorMessage", resposta.text[:200])
    except Exception:
        return resposta.text[:200]
