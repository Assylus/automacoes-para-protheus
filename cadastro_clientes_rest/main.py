# main.py — Orquestrador principal do cadastro de clientes no Protheus

import sys
import time
import yaml
import pandas as pd

from validador import limpar_registro, validar_registro, detectar_duplicatas
from api_protheus import montar_cabecalhos, montar_payload, enviar_cliente
from logger import (
    criar_logger, registrar_sucesso, registrar_erro_api,
    registrar_invalido, registrar_duplicata, registrar_dry_run,
    imprimir_resumo, gerar_excel_erros,
)


def carregar_config(caminho: str = "config.yaml") -> dict:
    with open(caminho, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def carregar_excel(caminho: str) -> list[dict]:
    """Lê o arquivo Excel e retorna lista de dicts com número de linha original."""
    df = pd.read_excel(caminho, dtype=str)
    df = df.fillna("")
    registros = df.to_dict(orient="records")
    # Adiciona número da linha do Excel (começa em 2 pois linha 1 é o cabeçalho)
    for i, r in enumerate(registros, start=2):
        r["_linha"] = i
    return registros


def main():
    # ── Configuração ──────────────────────────────────────────────────────
    cfg = carregar_config()
    prot = cfg["protheus"]
    arqs = cfg["arquivos"]
    dry_run = cfg.get("modo", {}).get("dry_run", False)

    url = f"{prot['host']}:{prot['port']}{prot['endpoint']}"
    cabecalhos = montar_cabecalhos(prot["usuario"], prot["senha"])
    verify_ssl = prot.get("verify_ssl", False)
    timeout = prot.get("timeout", 30)
    delay = prot.get("delay_entre_registros", 1.0)
    max_retries = prot.get("max_retries", 2)
    filial = prot.get("filial", "  ")

    logger, caminho_log, caminho_erros = criar_logger(arqs["log_dir"])

    if dry_run:
        logger.info("⚠️  MODO DRY RUN ATIVO — nenhuma chamada HTTP será feita\n")

    # ── Leitura do Excel ──────────────────────────────────────────────────
    try:
        registros_brutos = carregar_excel(arqs["entrada"])
    except FileNotFoundError:
        logger.error(f"Arquivo não encontrado: {arqs['entrada']}")
        sys.exit(1)

    total = len(registros_brutos)

    # ── Limpeza ──────────────────────────────────────────────────────────
    registros = [limpar_registro(r) for r in registros_brutos]
    # Repassa o número de linha após limpeza
    for i, r in enumerate(registros):
        r["_linha"] = registros_brutos[i]["_linha"]

    # ── Detecção de duplicatas ────────────────────────────────────────────
    duplicatas = detectar_duplicatas(registros)

    # ── Validação completa ────────────────────────────────────────────────
    validos = []
    invalidos_count = 0

    for r in registros:
        linha = r["_linha"]
        nome = r.get("A1_NOME", f"Linha {linha}")
        cgc = r.get("A1_CGC", "")

        # Duplicata interna
        if cgc in duplicatas and duplicatas[cgc] != linha:
            registrar_duplicata(logger, linha, nome, cgc, duplicatas[cgc])
            invalidos_count += 1
            continue

        erros = validar_registro(r, linha)
        if erros:
            registrar_invalido(logger, linha, nome, erros)
            invalidos_count += 1
        else:
            validos.append(r)

    # ── Resumo pré-execução ───────────────────────────────────────────────
    print(f"\n{'=' * 45}")
    print(f"  Total no arquivo  : {total:4d}")
    print(f"  Válidos para envio: {len(validos):4d}")
    print(f"  Inválidos         : {invalidos_count:4d}")
    print(f"{'=' * 45}")

    if not validos:
        logger.info("Nenhum registro válido para enviar. Encerrando.")
        sys.exit(0)

    resposta = input("  Deseja continuar? [S/N]: ").strip().upper()
    if resposta != "S":
        logger.info("Execução cancelada pelo usuário.")
        sys.exit(0)

    print()

    # ── Envio ─────────────────────────────────────────────────────────────
    sucessos = 0
    erros_api = 0
    registros_erro = []

    for r in validos:
        linha = r["_linha"]
        nome = r.get("A1_NOME", "")
        cgc = r.get("A1_CGC", "")

        if dry_run:
            registrar_dry_run(logger, linha, nome, cgc)
            sucessos += 1
            time.sleep(0.05)
            continue

        payload = montar_payload(r, filial)
        resultado = enviar_cliente(url, cabecalhos, payload, timeout, verify_ssl, max_retries)

        if resultado["sucesso"]:
            registrar_sucesso(logger, linha, resultado["codigo"], nome, cgc)
            sucessos += 1
        else:
            registrar_erro_api(logger, linha, nome, resultado["http_status"], resultado["mensagem"])
            erros_api += 1

            # Guarda para o Excel de reprocessamento
            erro_entry = dict(r)
            erro_entry.pop("_linha", None)
            erro_entry["LINHA_ARQUIVO"] = linha
            erro_entry["TIPO_ERRO"] = "ERRO_API"
            erro_entry["DESCRICAO_ERRO"] = resultado["mensagem"]
            erro_entry["HTTP_STATUS"] = resultado["http_status"]
            registros_erro.append(erro_entry)

            # Erros fatais interrompem o processo
            if resultado.get("fatal"):
                logger.error("\n🛑 Erro fatal — execução interrompida.")
                break

        time.sleep(delay)

    # ── Relatório final ───────────────────────────────────────────────────
    imprimir_resumo(logger, total, invalidos_count, len(validos), sucessos, erros_api, caminho_erros)
    gerar_excel_erros(registros_erro, caminho_erros)
    logger.info(f"\nLog completo salvo em: {caminho_log}")


if __name__ == "__main__":
    main()
