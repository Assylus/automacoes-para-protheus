# gerar_modelo.py — Cria a planilha modelo com exemplos para teste
# Execute uma vez: python gerar_modelo.py

import pandas as pd

linhas = [
    {
        # PJ válida — CNPJ real da Petrobras S.A.
        "A1_NOME":    "PETROLEO BRASILEIRO SA PETROBRAS",
        "A1_PESSOA":  "J",
        "A1_CGC":     "33.000.167/0001-01",
        "A1_END":     "AV REPUBLICA DO CHILE 65",
        "A1_BAIRRO":  "CENTRO",
        "A1_MUN":     "RIO DE JANEIRO",
        "A1_EST":     "RJ",
        "A1_CEP":     "20031-170",
        "A1_DDD":     "21",
        "A1_TEL":     "38737100",
        "A1_EMAIL":   "contato@petrobras.com.br",
        "A1_CONTATO": "CENTRAL DE ATENDIMENTO",
        "A1_TIPO":    "F",
    },
    {
        # PF válida — CPF fictício matematicamente válido
        "A1_NOME":    "JOAO DA SILVA SANTOS",
        "A1_PESSOA":  "F",
        "A1_CGC":     "529.982.247-25",
        "A1_END":     "RUA DAS PALMEIRAS 200 APTO 3",
        "A1_BAIRRO":  "JARDIM AMERICA",
        "A1_MUN":     "BOA VISTA",
        "A1_EST":     "RR",
        "A1_CEP":     "69301-000",
        "A1_DDD":     "95",
        "A1_TEL":     "99123456",
        "A1_EMAIL":   "joao.silva@email.com",
        "A1_CONTATO": "JOAO DA SILVA",
        "A1_TIPO":    "F",
    },
    {
        # CNPJ inválido proposital — deve ser rejeitado pela validação
        "A1_NOME":    "EMPRESA COM CNPJ ERRADO LTDA",
        "A1_PESSOA":  "J",
        "A1_CGC":     "11.111.111/1111-11",   # CNPJ inválido
        "A1_END":     "RUA TESTE 999",
        "A1_BAIRRO":  "INDUSTRIAL",
        "A1_MUN":     "MANAUS",
        "A1_EST":     "AM",
        "A1_CEP":     "69000-000",
        "A1_DDD":     "92",
        "A1_TEL":     "33334444",
        "A1_EMAIL":   "",
        "A1_CONTATO": "",
        "A1_TIPO":    "F",
    },
]

df = pd.DataFrame(linhas)
df.to_excel("modelo_entrada.xlsx", index=False)
print("✅ Arquivo modelo_entrada.xlsx criado com sucesso.")
