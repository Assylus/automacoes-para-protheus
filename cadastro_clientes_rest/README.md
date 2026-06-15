# Cadastro de Clientes no Protheus via API REST

Script Python para cadastrar clientes em massa no **TOTVS Protheus** da Green Máquinas
utilizando o endpoint REST `FWModel/MATA030`.

## Pré-requisitos

- Python 3.11+
- Acesso à VPN da Green Máquinas (se necessário)
- Credenciais de acesso ao Protheus

## Instalação

```bash
pip install -r requirements.txt
```

## Configuração

Edite o arquivo `config.yaml` com suas credenciais:

```yaml
protheus:
  usuario: "seu.usuario"
  senha: "SUA_SENHA"
```

## Preparar a planilha de entrada

1. Gere a planilha modelo com exemplos:
   ```bash
   python gerar_modelo.py
   ```
2. Copie `modelo_entrada.xlsx` para `clientes_importar.xlsx`
3. Preencha com os clientes reais

### Colunas obrigatórias

| Coluna | Descrição | Exemplo |
|--------|-----------|---------|
| A1_NOME | Razão social / Nome completo | EMPRESA LTDA |
| A1_PESSOA | J = Jurídica / F = Física | J |
| A1_CGC | CNPJ (14 dígitos) ou CPF (11 dígitos) com ou sem máscara | 12.345.678/0001-99 |
| A1_END | Endereço | RUA DAS FLORES 100 |
| A1_BAIRRO | Bairro | CENTRO |
| A1_MUN | Município | BOA VISTA |
| A1_EST | UF (2 letras) | RR |
| A1_CEP | CEP com ou sem máscara | 69301-000 |

### Colunas opcionais

| Coluna | Descrição |
|--------|-----------|
| A1_DDD | DDD do telefone |
| A1_TEL | Número do telefone |
| A1_EMAIL | E-mail (ignorado se vazio ou "@") |
| A1_CONTATO | Nome do contato |
| A1_TIPO | Tipo de cliente (padrão: F) |

## Execução

### Modo simulação (recomendado para teste)

```bash
# Defina dry_run: true no config.yaml, depois:
python main.py
```

O modo dry_run valida todos os registros e simula o log sem fazer nenhuma chamada HTTP.

### Execução real

```bash
# Defina dry_run: false no config.yaml, depois:
python main.py
```

O script exibe um resumo antes de enviar e pede confirmação.

## Saídas

| Arquivo | Descrição |
|---------|-----------|
| `logs/cadastro_YYYYMMDD_HHMMSS.log` | Log completo da execução |
| `logs/erros_YYYYMMDD.xlsx` | Clientes com erro para reprocessamento |

## Regras de validação

- CNPJ e CPF são validados pelos dois dígitos verificadores
- Campos de texto são convertidos para maiúsculas automaticamente
- Máscaras de CNPJ, CPF e CEP são removidas automaticamente
- Registros duplicados no arquivo (mesmo CNPJ/CPF) são detectados — apenas o primeiro é enviado
- Clientes inválidos são logados e descartados antes de qualquer chamada à API

## Endpoint

```
POST https://northgreen119546.protheus.cloudtotvs.com.br:4050/rest/fwmodel/MATA030
Auth: Basic Auth
```
