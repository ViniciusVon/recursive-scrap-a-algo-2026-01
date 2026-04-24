# Backend — Monitor de Preços

API FastAPI + Selenium que expõe o monitoramento de valores numéricos em páginas web,
persiste histórico em SQLite e envia resumo por e-mail via Gmail SMTP.

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Requisitos](#2-requisitos)
3. [Instalação](#3-instalação)
4. [Configuração](#4-configuração)
5. [Como Executar](#5-como-executar)
6. [Estrutura](#6-estrutura)
7. [Fluxo de uma sessão](#7-fluxo-de-uma-sessão)
8. [Módulos](#8-módulos)
9. [Banco de Dados](#9-banco-de-dados)
10. [Segurança & Observabilidade](#10-segurança--observabilidade)
11. [Análise de Complexidade](#11-análise-de-complexidade)

---

## 1. Visão Geral

- **Cadastra usuários** em SQLite (nome + e-mail validados via Pydantic strict).
- **Cria sessões** de monitoramento via `POST /sessoes` — cada sessão abre um ChromeDriver
  isolado e carrega a URL informada.
- **Lista valores numéricos** da página (`GET /sessoes/{id}/valores`) executando
  `src/js/list_values.js` que varre o DOM e retorna `{text, xpath}` pra cada folha com dígitos.
- **Inicia monitoramento** ao receber o XPath escolhido (`POST /sessoes/{id}/selecionar`) —
  dispara uma thread daemon que, a cada 15s, dá `driver.refresh()`, lê o valor pelo XPath e
  emite eventos via WebSocket.
- **Stream em tempo real** por WebSocket (`/ws/sessoes/{id}`): screenshots a cada 1s + ciclos
  a cada 15s + alterações quando o valor muda.
- **Persiste histórico** em SQLite no `DELETE /sessoes/{id}` (tabelas `sessoes_historicas` +
  `alteracoes_historicas`) e envia e-mail de resumo.

---

## 2. Requisitos

- **Python 3.12** (ou 3.9+)
- **Google Chrome / Chromium** + **ChromeDriver** no PATH (ou os envs `CHROME_BIN` e
  `CHROMEDRIVER_BIN` apontando pros binários — usado no container ARM64).
- Dependências em `requirements.txt` (`fastapi`, `uvicorn`, `selenium`, `pydantic[email]`,
  `pytest`, `httpx`).
- Conta Gmail com **senha de app** (para o e-mail de resumo — opcional).

---

## 3. Instalação

### Dev local (sem Docker)

```bash
git clone https://github.com/ViniciusVon/recursive-scrap-a-algo-2026-01.git
cd recursive-scrap-a-algo-2026-01
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

### Docker Compose (recomendado)

```bash
docker compose up --build
```

Sobe backend em `:8000` + frontend em `:5173`.

---

## 4. Configuração

### `.env` (raiz do repo)

```
GMAIL_USER=seu.email@gmail.com
GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
TZ=America/Sao_Paulo
```

- `GMAIL_*`: envio de e-mail via SMTP. Sem isso, o resumo é pulado com log de aviso.
- `CORS_ORIGINS`: lista separada por vírgula; a ausência cai no default de dev
  (`http://localhost:5173,http://127.0.0.1:5173`).
- `TZ`: timezone do processo (fixada no Dockerfile também — importante em VPS UTC).

O `notifier._ler_env` prioriza `os.environ` e cai no `.env` como fallback de dev.

---

## 5. Como Executar

### Endpoints principais

| Método | Rota | Uso |
|:------:|------|-----|
| `POST` | `/usuarios` | Cadastra usuário (rate limit: 5/min por IP) |
| `GET` | `/usuarios` | Lista usuários |
| `GET` | `/usuarios/{id}/sessoes` | Histórico persistente do usuário |
| `POST` | `/sessoes` | Cria sessão + abre driver (10/min) |
| `GET` | `/sessoes/{id}/valores` | Varre DOM e retorna valores numéricos |
| `GET` | `/sessoes/{id}/screenshot` | PNG em base64 (via CDP) |
| `POST` | `/sessoes/{id}/selecionar` | Grava XPath + inicia thread (15/min) |
| `GET` | `/sessoes/{id}/historico` | Alterações da sessão em memória |
| `DELETE` | `/sessoes/{id}` | Encerra, persiste, envia e-mail |
| `GET` | `/sessoes/historicas/{id}` | Detalhe de sessão encerrada |
| `GET` | `/sessoes/historicas/{id}/alteracoes` | Alterações persistidas |
| `WS` | `/ws/sessoes/{id}` | Stream live (screenshot + ciclo + alteracao + encerrada) |

OpenAPI em `http://localhost:8000/docs`.

---

## 6. Estrutura

```
recursive-scrap-a-algo-2026-01/
├── backend/
│   ├── main.py                # app FastAPI + lifespan + middlewares
│   ├── schemas.py             # Pydantic strict (extra="forbid")
│   ├── middlewares/
│   │   └── rate_limit.py      # token-bucket in-memory
│   ├── routes/
│   │   ├── usuarios.py
│   │   ├── sessoes.py
│   │   └── websocket.py
│   └── services/
│       └── session_manager.py # registry de sessões + thread de monitor
├── src/
│   ├── constants.py           # INTERVALO_SEGUNDOS, SMTP_HOST, etc.
│   ├── db.py                  # SQLite: usuarios + sessoes_historicas + alteracoes
│   ├── validators.py          # validar_nome_usuario, validar_email
│   ├── utils.py               # validar_url, criar_driver
│   ├── search_numbers.py      # regex de números
│   ├── value_selector.py      # list_values.js + ler_valor_por_xpath
│   ├── form_recorder.py       # [legado CLI] registra no Google Form
│   ├── notifier.py            # SMTP + montar_resumo_sessao
│   └── js/list_values.js      # varredura de DOM
└── tests/                     # pytest: usuários, histórico, rate limit
```

---

## 7. Fluxo de uma sessão

```
POST /usuarios                      → cadastro
POST /sessoes                       → abre driver + carrega URL
GET  /sessoes/{id}/valores          → varre DOM (n·d)
GET  /sessoes/{id}/screenshot       → preview CDP
POST /sessoes/{id}/selecionar       → dispara thread daemon
(monitor roda em background)
  ├─ a cada 1s: screenshot CDP + emit WS
  └─ a cada 15s: refresh + ler_valor_por_xpath + emit (+ alteracao se mudou)
WS   /ws/sessoes/{id}               → cliente recebe stream
DELETE /sessoes/{id}                → grava histórico + e-mail + fecha driver
```

---

## 8. Módulos

Os detalhes de complexidade de cada função estão em
[`complexidade_backend.md`](./complexidade_backend.md). Abaixo uma visão rápida
das responsabilidades.

### `backend/main.py`

Monta a aplicação: `lifespan` chama `inicializar_banco()`, CORS lê de `CORS_ORIGINS`,
`RateLimitMiddleware` protege rotas sensíveis. Registra os 3 routers.

### `backend/schemas.py`

`UsuarioIn`, `SessaoIn`, `SelecaoIn` com `ConfigDict(extra="forbid", str_strip_whitespace=True,
str_min_length=1)` — campos desconhecidos viram 422. Validadores extras pra URL (protocolo
`http(s)`) e nome (`isalpha`).

### `backend/middlewares/rate_limit.py`

Token-bucket por `(IP, método, path)`:

| Rota | Limite |
|------|:------:|
| `POST /usuarios` | 5/min |
| `POST /sessoes` | 10/min |
| `POST /sessoes/*/selecionar` | 15/min |

Janela deslizante com `deque`. Retorna **429** + `Retry-After` quando estoura.

### `backend/services/session_manager.py`

`SessionManager` — registry `{session_id: SessionState}` protegido por `Lock`.

Campos do `SessionState`: driver, status, xpath, valor_atual, historico (lista de
`RegistroAlteracao`), thread, `_subscribers` (filas de WS), `_parar` (Event).

Thread de monitor:
- `INTERVALO_SCREENSHOT = 1s` (captura via CDP `Page.captureScreenshot`)
- `INTERVALO_SEGUNDOS = 15s` (ciclo de verificação — `refresh` + `ler_valor_por_xpath`)

### `src/db.py`

Tabelas:
- `usuarios (id, nome, email)` — PK autoincrement.
- `sessoes_historicas (id, usuario_id, url, xpath_monitorado, valor_inicial, valor_final,
  total_alteracoes, iniciada_em, encerrada_em)` — PK = sessão.
- `alteracoes_historicas (sessao_id, ciclo, timestamp, valor_antigo, valor_novo)` — PK composta.

Índice: `idx_sessoes_historicas_usuario (usuario_id, encerrada_em DESC)` pra listar rápido.

### `src/notifier.py`

- `_ler_env(chave)` resolve de `os.environ` primeiro, `.env` como fallback.
- `enviar_email(dest, senha, assunto, corpo)` via `smtplib.SMTP` com STARTTLS.
- `montar_resumo_sessao(url, valor_final, historico)` monta o e-mail de encerramento.

### `src/value_selector.py` + `src/js/list_values.js`

O JS passa pelo DOM com `TreeWalker` coletando textos com dígitos; pra cada match, calcula
o XPath absoluto subindo até a raiz. Python dedup por `(text, xpath)`.

---

## 9. Banco de Dados

SQLite (`dados.db` na raiz). Criado em `inicializar_banco()` no lifespan da FastAPI.

Ver DDL completo em `src/db.py`. Persistência é **efêmera por container** na config
atual do `docker-compose.yml` — pra persistir, basta bind-mountar `./dados.db:/app/dados.db`
(sem shadow de `/app`, que quebraria o código da imagem).

---

## 10. Segurança & Observabilidade

- **CORS** fechado na origem do frontend (configurável por env).
- **Pydantic strict** barra campos extras (422).
- **Rate limiting** in-memory nos POSTs sensíveis.
- **Logs estruturados** via `logging` — cada rota e cada ciclo do monitor emite INFO/WARN/ERROR.
- **Healthcheck** `GET /health` usado pelo compose.

---

## 11. Análise de Complexidade

Documento dedicado com a análise validada contra o código:
[`complexidade_backend.md`](./complexidade_backend.md).

Resumo do pipeline principal:

> **T(n, d, u, k, s, C) = O(n · d + C · (d + s) + k)**
>
> Com `s = 1` (uma aba aberta, caso típico), degenera para `O(n · d + C · d + k)` —
> **linear no DOM no setup, constante por ciclo depois**.
