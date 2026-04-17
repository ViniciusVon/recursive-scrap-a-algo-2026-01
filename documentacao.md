# Documentação — Monitor de Preços via Selenium

Assistente de lances para sites de leilão. Monitora um valor numérico específico dentro de uma página web escolhido pelo usuário, registra alterações em um Google Form e envia um resumo por e-mail ao encerrar.

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Requisitos](#2-requisitos)
3. [Instalação](#3-instalação)
4. [Configuração](#4-configuração)
5. [Como Executar](#5-como-executar)
6. [Estrutura do Projeto](#6-estrutura-do-projeto)
7. [Fluxo da Aplicação](#7-fluxo-da-aplicação)
8. [Módulos](#8-módulos)
9. [Banco de Dados](#9-banco-de-dados)
10. [Análise de Complexidade (Big O)](#10-análise-de-complexidade-big-o)
11. [Logs e Observabilidade](#11-logs-e-observabilidade)

---

## 1. Visão Geral

O sistema é um monitor de preços que:

- **Identifica o usuário** via cadastro persistido em SQLite (nome + e-mail).
- **Abre uma página web** definida pelo usuário via Selenium WebDriver (Chrome).
- **Lista todos os valores numéricos** da página e pede ao usuário que escolha qual monitorar (armazenando o XPath do elemento).
- **Monitora periodicamente** (a cada 15 segundos) o valor selecionado, detectando mudanças.
- **Registra as alterações em uma segunda aba** (Google Form público), preenchendo os campos e clicando no botão "Enviar".
- **Envia um e-mail de resumo** via Gmail SMTP ao final do monitoramento (quando o usuário pressiona `Ctrl+C`).

---

## 2. Requisitos

- **Python 3.9+**
- **Google Chrome** (ou Chromium) instalado
- **ChromeDriver** compatível com a versão do Chrome no PATH
- Biblioteca **Selenium** (`pip install selenium`)
- Conta Gmail com **senha de app** configurada (para notificações por e-mail — opcional)

---

## 3. Instalação

```bash
git clone https://github.com/ViniciusVon/recursive-scrap-a-algo-2026-01.git
cd recursive-scrap-a-algo-2026-01
pip install selenium
```

---

## 4. Configuração

### 4.1 Arquivo `.env` (opcional — para notificações por e-mail)

Crie na raiz do projeto:

```
GMAIL_APP_PASSWORD=sua senha de app do gmail aqui
```

> O arquivo está no `.gitignore` e não deve ser commitado.

### 4.2 Google Form

A URL do Google Form de registro está fixa em `src/constants.py`:

```python
FORM_URL = "https://forms.gle/9qC2PVjEdfA3QQ7E9"
```

O formulário deve ter **5 campos de texto** (nessa ordem):

1. URL monitorada
2. Valor antigo
3. Valor novo
4. Timestamp
5. Usuário

---

## 5. Como Executar

Na raiz do projeto:

```bash
python3 app.py
```

O sistema irá, em ordem:

1. Pedir identificação do usuário (escolher existente ou cadastrar novo).
2. Pedir a URL a monitorar.
3. Tentar carregar a senha de app do `.env` (se existir).
4. Perguntar se deseja rodar em modo headless (sem interface gráfica).
5. Abrir a página, listar valores numéricos e pedir escolha do índice.
6. Entrar no loop de monitoramento.
7. A cada alteração detectada: registra no Google Form e loga no console.
8. Ao pressionar `Ctrl+C`: encerra e envia e-mail de resumo (se configurado).

---

## 6. Estrutura do Projeto

```
recursive-scrap-a-algo-2026-01/
├── app.py                      # Entry point — orquestra o fluxo completo
├── documentacao.md             # Este arquivo
├── README.md                   # Especificação do trabalho
├── dados.db                    # SQLite com usuários (ignorado pelo git)
├── .env                        # Senha de app do Gmail (ignorado pelo git)
├── .gitignore
└── src/
    ├── constants.py            # Constantes centralizadas (URLs, timeouts, SMTP)
    ├── db.py                   # Persistência SQLite (CRUD de usuários)
    ├── form_recorder.py        # Registra alterações no Google Form
    ├── notifier.py             # Envio de e-mail via Gmail SMTP
    ├── search_numbers.py       # Regex para encontrar números no texto
    ├── utils.py                # WebDriver + validação de URL
    ├── validators.py           # Validação de nome e e-mail
    ├── value_selector.py       # Seleção do valor específico a monitorar
    └── js/
        └── list_values.js      # Script JS para varredura do DOM
```

---

## 7. Fluxo da Aplicação

```
┌──────────────────┐
│ Inicializa banco │
│    SQLite        │
└────────┬─────────┘
         │
         ▼
┌───────────────────┐
│ Identifica usuário│  ← pergunta nome + e-mail, persiste no DB
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Coleta URL        │  ← URL a monitorar
└────────┬──────────┘
         │
         ▼
┌────────────────────┐
│ Carrega .env       │  ← senha de app do Gmail
│ (opcional)         │
└────────┬───────────┘
         │
         ▼
┌──────────────────┐
│ Abre WebDriver   │
│ e acessa URL     │
└────────┬─────────┘
         │
         ▼
┌────────────────────────────┐
│ Lista valores numéricos    │  ← varre o DOM (JavaScript)
│ com XPath                  │
└────────┬───────────────────┘
         │
         ▼
┌────────────────────────────┐
│ Usuário escolhe qual       │  ← input do índice
│ valor monitorar            │
└────────┬───────────────────┘
         │
         ▼
┌────────────────────────────┐
│ Abre 2ª aba com Google Form│
└────────┬───────────────────┘
         │
         ▼
┌────────────────────────────┐
│ LOOP:                      │
│  - sleep 15s               │
│  - refresh da aba 1        │
│  - lê valor por XPath      │
│  - se mudou: registra      │
│    no form (aba 2)         │
└────────┬───────────────────┘
         │ Ctrl+C
         ▼
┌────────────────────────────┐
│ Envia e-mail de resumo     │  ← extra, se .env configurado
└────────────────────────────┘
```

---

## 8. Módulos

### 8.1 `app.py`

Entry point. Orquestra todo o fluxo: identificação do usuário, coleta de URL, seleção de valor, monitoramento e resumo final por e-mail.

| Função | Descrição | Complexidade |
|--------|-----------|--------------|
| `monitorar_preco(driver, url, usuario)` | Loop de monitoramento do valor selecionado | O(1) por ciclo |
| `identificar_usuario()` | Lista usuários existentes ou cadastra novo | O(n) |
| `coletar_entradas()` | Coleta URL e configurações | O(1) |
| `main()` | Ponto de entrada principal | — |

### 8.2 `src/constants.py`

Constantes globais da aplicação — centraliza todos os valores fixos.

| Constante | Valor | Uso |
|-----------|-------|-----|
| `FORM_URL` | `https://forms.gle/9qC2PVjEdfA3QQ7E9` | URL fixa do Google Form |
| `INTERVALO_SEGUNDOS` | `15` | Intervalo entre ciclos de monitoramento |
| `TIMEOUT_SEGUNDOS` | `10` | Timeout de esperas do Selenium (form) |
| `SMTP_HOST` | `smtp.gmail.com` | Servidor SMTP do Gmail |
| `SMTP_PORT` | `587` | Porta SMTP (TLS) |

### 8.3 `src/db.py`

Persistência SQLite com tabela `usuarios (id, nome, email)`.

| Função | Descrição | Complexidade |
|--------|-----------|--------------|
| `inicializar_banco()` | Cria a tabela se não existir | O(1) |
| `cadastrar_usuario(nome, email)` | Insere usuário, retorna id | O(1) |
| `listar_usuarios()` | Retorna todos os usuários | O(n) |
| `buscar_usuario_por_id(id)` | Busca usuário pelo id | O(1) |

### 8.4 `src/validators.py`

| Função | Descrição | Complexidade |
|--------|-----------|--------------|
| `validar_nome_usuario(nome)` | Valida nome (3+ letras, só caracteres) | O(n) |
| `validar_email(email)` | Valida formato de e-mail | O(1) |

### 8.5 `src/utils.py`

| Função | Descrição | Complexidade |
|--------|-----------|--------------|
| `validar_url(url)` | Regex para validar URL | O(1) |
| `criar_driver(headless)` | Instancia ChromeDriver com opções | O(1) |

### 8.6 `src/search_numbers.py`

| Função | Descrição | Complexidade |
|--------|-----------|--------------|
| `encontrar_numeros(texto)` | Regex para extrair números (inteiros, decimais, datas, horários) | O(n) |
| `buscar_numeros_na_pagina(url, headless)` | Abre URL e extrai números (função utilitária) | O(n) |

### 8.7 `src/value_selector.py` + `src/js/list_values.js`

Seleção do valor específico a monitorar via DOM + XPath. O script JavaScript
que varre o DOM (função `listarValores`) fica em arquivo `.js` separado para
manter o código organizado e com syntax highlighting apropriado.

| Função | Descrição | Complexidade |
|--------|-----------|--------------|
| `_carregar_script_js()` | Lê o conteúdo de `src/js/list_values.js` | O(1) |
| `listar_valores_com_xpath(driver)` | Executa o JS no navegador e retorna [{text, xpath}, ...] | O(n) |
| `selecionar_valor(driver)` | Mostra lista enumerada e pede escolha do usuário | O(n) |
| `ler_valor_por_xpath(driver, xpath)` | Lê texto atual do elemento identificado | O(1) |

### 8.8 `src/form_recorder.py`

Integração com Google Forms.

| Função | Descrição | Complexidade |
|--------|-----------|--------------|
| `abrir_aba_form(driver, form_url)` | Abre segunda aba via `window.open` | O(1) |
| `registrar_alteracao(driver, aba_monitor, aba_form, form_url, dados)` | Preenche form e clica em Enviar | O(k), k = nº campos |

### 8.9 `src/notifier.py`

Notificação por e-mail via Gmail SMTP.

| Função | Descrição | Complexidade |
|--------|-----------|--------------|
| `carregar_senha_app()` | Lê `GMAIL_APP_PASSWORD` do `.env` | O(1) |
| `enviar_email(destinatario, senha_app, assunto, corpo)` | Envia e-mail via SMTP com TLS | O(1) |
| `montar_corpo_alteracao(url, antes, depois)` | Monta corpo do e-mail com diff | O(n) |

---

## 9. Banco de Dados

SQLite (arquivo `dados.db` na raiz). Criado automaticamente na primeira execução.

### Tabela `usuarios`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | Identificador único |
| `nome` | TEXT NOT NULL | Nome do usuário (mín. 3 caracteres, só letras) |
| `email` | TEXT NOT NULL | E-mail do usuário |

---

## 10. Análise de Complexidade (Big O)

### Onde `n` é:

- **Texto**: tamanho do texto da página em caracteres.
- **DOM**: número de elementos HTML na página.
- **Usuários**: quantidade de usuários cadastrados.

### Resumo por operação:

| Operação | Complexidade | Observação |
|----------|--------------|------------|
| Validação de URL (regex) | O(1) | Regex com tamanho fixo |
| Validação de nome (split + isalpha) | O(n) | n = tamanho do nome |
| Validação de e-mail (regex) | O(1) | — |
| Inserir usuário | O(1) | SQLite index implícito |
| Buscar usuário por ID | O(1) | Índice primário |
| Listar usuários | O(n) | n = usuários cadastrados |
| Varrer DOM | O(n) | n = elementos do DOM |
| Ler valor por XPath | **O(1)** | Query única |
| Ciclo de monitoramento | **O(1)** | Ler apenas 1 elemento |
| Registrar no Google Form | O(k) | k = número de campos |
| Enviar e-mail SMTP | O(1) | — |

### Complexidade geral do monitoramento:

- **Setup inicial**: O(n) para varrer o DOM e identificar valores numéricos.
- **Loop de monitoramento**: **O(1) por ciclo**, pois lê apenas um elemento pelo XPath já conhecido.
- **Total**: O(n) no setup + O(c) para c ciclos de monitoramento.

---

## 11. Logs e Observabilidade

Todos os eventos importantes são logados no console com o prefixo `LOG |`:

- Cadastro e identificação de usuários
- URL informada e modo de execução
- XPath do valor selecionado
- Cada ciclo de monitoramento (com ou sem alteração)
- Detecção de alteração (valor antes/depois)
- Registro no Google Form (sucesso/falha)
- Envio de e-mail (sucesso/falha)

Exemplo de log:

```
2026-04-17 18:32:05 [INFO] LOG | Novo usuário cadastrado: 'Gabriel' (gabriel@...) [ID: 1]
2026-04-17 18:32:10 [INFO] LOG | URL informada: https://www.horariodebrasilia.org
2026-04-17 18:32:18 [INFO] LOG | Valor selecionado: '18:32:18'
2026-04-17 18:32:18 [INFO] LOG | XPath monitorado: /html/body/div[1]/div[2]/span[1]
2026-04-17 18:32:33 [INFO] LOG | ALTERAÇÃO DETECTADA no ciclo 1!
2026-04-17 18:32:33 [INFO] LOG | Antes: '18:32:18'
2026-04-17 18:32:33 [INFO] LOG | Depois: '18:32:33'
2026-04-17 18:32:35 [INFO] LOG | Formulário enviado — alteração registrada!
```
