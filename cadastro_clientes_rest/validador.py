# validador.py — Limpeza e validação dos registros antes de enviar à API

import re

UFS_VALIDAS = {
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
    "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
    "RO", "RR", "RS", "SC", "SE", "SP", "TO"
}


def limpar_digitos(valor: str) -> str:
    """Remove tudo que não for dígito numérico."""
    return re.sub(r"\D", "", str(valor or ""))


def validar_cnpj(cnpj: str) -> bool:
    """Valida CNPJ pelos dois dígitos verificadores."""
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False

    def calcular_digito(cnpj, pesos):
        soma = sum(int(cnpj[i]) * pesos[i] for i in range(len(pesos)))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    d1 = calcular_digito(cnpj[:12], pesos1)
    d2 = calcular_digito(cnpj[:13], pesos2)

    return cnpj[-2:] == f"{d1}{d2}"


def validar_cpf(cpf: str) -> bool:
    """Valida CPF pelos dois dígitos verificadores."""
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    def calcular_digito(cpf, n):
        soma = sum(int(cpf[i]) * (n - i) for i in range(n - 1))
        resto = (soma * 10) % 11
        return 0 if resto == 10 else resto

    d1 = calcular_digito(cpf, 10)
    d2 = calcular_digito(cpf, 11)

    return cpf[-2:] == f"{d1}{d2}"


def validar_email(email: str) -> bool:
    """Regex básico de e-mail. Retorna True se vazio ou se for inválido mas deve ser ignorado."""
    if not email or email.strip() == "@":
        return True  # campo vazio ou "@" é ignorado
    padrao = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(padrao, email.strip()))


def limpar_registro(linha: dict) -> dict:
    """Aplica todas as limpezas automáticas num registro bruto do Excel."""
    r = {k: str(v).strip() if v is not None else "" for k, v in linha.items()}

    # Remove máscaras de documentos e CEP
    r["A1_CGC"] = limpar_digitos(r.get("A1_CGC", ""))
    r["A1_CEP"] = limpar_digitos(r.get("A1_CEP", ""))

    # Texto em maiúsculas
    for campo in ("A1_NOME", "A1_NREDUZ", "A1_MUN", "A1_BAIRRO", "A1_END", "A1_CONTATO"):
        r[campo] = r.get(campo, "").upper()

    # UF: maiúscula e no máximo 2 chars
    r["A1_EST"] = r.get("A1_EST", "").upper().strip()[:2]

    # A1_PESSOA em maiúsculas
    r["A1_PESSOA"] = r.get("A1_PESSOA", "").upper().strip()

    # Gera nome reduzido automaticamente se não vier preenchido
    if not r.get("A1_NREDUZ"):
        r["A1_NREDUZ"] = r.get("A1_NOME", "")[:20]

    # E-mail: mantém original mas ignora "@" isolado
    if r.get("A1_EMAIL", "").strip() == "@":
        r["A1_EMAIL"] = ""

    return r


def validar_registro(r: dict, numero_linha: int) -> list[str]:
    """
    Valida um registro já limpo.
    Retorna lista de erros encontrados (vazia = válido).
    """
    erros = []

    # Campos obrigatórios
    obrigatorios = ["A1_NOME", "A1_PESSOA", "A1_CGC", "A1_END", "A1_BAIRRO", "A1_MUN", "A1_EST", "A1_CEP"]
    for campo in obrigatorios:
        if not r.get(campo):
            erros.append(f"{campo} obrigatório está vazio")

    # A1_PESSOA
    if r.get("A1_PESSOA") not in ("F", "J"):
        erros.append(f"A1_PESSOA inválido: '{r.get('A1_PESSOA')}' (esperado 'F' ou 'J')")

    # CPF / CNPJ
    cgc = r.get("A1_CGC", "")
    pessoa = r.get("A1_PESSOA", "")
    if pessoa == "J":
        if not validar_cnpj(cgc):
            erros.append(f"CNPJ inválido: '{cgc}'")
    elif pessoa == "F":
        if not validar_cpf(cgc):
            erros.append(f"CPF inválido: '{cgc}'")

    # UF
    if r.get("A1_EST") and r.get("A1_EST") not in UFS_VALIDAS:
        erros.append(f"UF inválida: '{r.get('A1_EST')}'")

    # CEP
    cep = r.get("A1_CEP", "")
    if cep and (len(cep) != 8 or not cep.isdigit()):
        erros.append(f"CEP inválido: '{cep}' (deve ter 8 dígitos)")

    # E-mail
    if r.get("A1_EMAIL") and not validar_email(r["A1_EMAIL"]):
        erros.append(f"E-mail inválido: '{r['A1_EMAIL']}'")

    # Tamanhos máximos
    limites = {
        "A1_NOME": 40,
        "A1_NREDUZ": 20,
        "A1_END": 40,
        "A1_BAIRRO": 20,
        "A1_MUN": 20,
    }
    for campo, limite in limites.items():
        valor = r.get(campo, "")
        if len(valor) > limite:
            erros.append(f"{campo} excede {limite} chars ({len(valor)} chars): '{valor[:30]}...'")

    return erros


def detectar_duplicatas(registros: list[dict]) -> dict[str, int]:
    """
    Identifica CPF/CNPJs duplicados dentro do arquivo.
    Retorna dict {cgc: numero_linha_do_primeiro} para as linhas duplicadas.
    """
    vistos = {}      # cgc -> número da primeira linha
    duplicatas = {}  # cgc -> número da primeira linha (para as linhas duplicadas)

    for r in registros:
        cgc = r.get("A1_CGC", "")
        linha = r.get("_linha", 0)
        if not cgc:
            continue
        if cgc in vistos:
            duplicatas[cgc] = vistos[cgc]
        else:
            vistos[cgc] = linha

    return duplicatas
