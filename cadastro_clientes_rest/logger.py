# logger.py — Registro em arquivo de log e geração do Excel de erros

import os
import logging
from datetime import datetime
import pandas as pd


def criar_logger(log_dir: str) -> tuple[logging.Logger, str, str]:
    """
    Cria o arquivo de log com timestamp e retorna (logger, caminho_log, caminho_xlsx_erros).
    """
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho_log = os.path.join(log_dir, f"cadastro_{timestamp}.log")
    caminho_erros = os.path.join(log_dir, f"erros_{datetime.now().strftime('%Y%m%d')}.xlsx")

    logger = logging.getLogger("cadastro_protheus")
    logger.setLevel(logging.DEBUG)

    # Handler para arquivo
    fh = logging.FileHandler(caminho_log, encoding="utf-8")
    fh.setLevel(logging.DEBUG)

    # Handler para console
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formato = logging.Formatter("%(message)s")
    fh.setFormatter(formato)
    ch.setFormatter(formato)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger, caminho_log, caminho_erros


def registrar_sucesso(logger: logging.Logger, linha: int, codigo: str, nome: str, cgc: str):
    logger.info(
        f"[{_agora()}] ✅ SUCESSO  | Linha {linha:3d} | Cod: {codigo:<12} | {nome[:40]}\n"
        f"{'':>32}| CPF/CNPJ: {cgc}"
    )


def registrar_erro_api(logger: logging.Logger, linha: int, nome: str, http_status, mensagem: str):
    logger.error(
        f"[{_agora()}] ❌ ERRO API | Linha {linha:3d} | {nome[:40]}\n"
        f"{'':>32}| HTTP {http_status}: \"{mensagem}\""
    )


def registrar_invalido(logger: logging.Logger, linha: int, nome: str, motivos: list[str]):
    for motivo in motivos:
        logger.warning(
            f"[{_agora()}] ⚠️ INVÁLIDO | Linha {linha:3d} | {nome[:40]}\n"
            f"{'':>32}| {motivo} — não enviado à API"
        )


def registrar_duplicata(logger: logging.Logger, linha: int, nome: str, cgc: str, linha_original: int):
    logger.warning(
        f"[{_agora()}] ⚠️ DUPLICATA| Linha {linha:3d} | {nome[:40]}\n"
        f"{'':>32}| CPF/CNPJ {cgc} já aparece na linha {linha_original} — ignorado"
    )


def registrar_dry_run(logger: logging.Logger, linha: int, nome: str, cgc: str):
    logger.info(
        f"[{_agora()}] 🔵 DRY RUN  | Linha {linha:3d} | {nome[:40]}\n"
        f"{'':>32}| CPF/CNPJ: {cgc} — não enviado (modo simulação)"
    )


def imprimir_resumo(logger: logging.Logger, total: int, invalidos: int, enviados: int, sucessos: int, erros_api: int, caminho_erros: str):
    linha_sep = "=" * 55
    logger.info(f"\n{linha_sep}")
    logger.info("  RESUMO FINAL")
    logger.info(linha_sep)
    logger.info(f"  Total no arquivo   : {total:4d}")
    logger.info(f"  Inválidos (Python) : {invalidos:4d}")
    logger.info(f"  Enviados à API     : {enviados:4d}")
    logger.info(f"    ✅ Sucesso        : {sucessos:4d}")
    logger.info(f"    ❌ Erro API       : {erros_api:4d}")
    if erros_api > 0:
        logger.info(f"  Arquivo de erros   : {caminho_erros}")
    logger.info(linha_sep)


def gerar_excel_erros(registros_erro: list[dict], caminho: str):
    """Salva Excel de reprocessamento com os registros que falharam."""
    if not registros_erro:
        return
    df = pd.DataFrame(registros_erro)
    df.to_excel(caminho, index=False)


def _agora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
