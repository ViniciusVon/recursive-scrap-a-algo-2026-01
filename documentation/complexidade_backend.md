# Análise de complexidade — backend

Validada contra o código em `main` (`src/` + `backend/`). Cada linha
aqui bate com o docstring da função correspondente.

## Variáveis usadas

| Símbolo | Significado |
|:-------:|:------------|
| `n`  | Nº de elementos no DOM da página monitorada |
| `d`  | Profundidade média da árvore do DOM |
| `m`  | Nº de elementos no DOM do Google Form |
| `u`  | Nº de usuários cadastrados no SQLite |
| `k`  | Nº de alterações registradas na sessão |
| `s`  | Nº de subscribers WebSocket ativos numa sessão |
| `C`  | Nº de ciclos executados no loop de monitoramento |
| `L`  | Tamanho (em caracteres) de uma string de entrada (URL, e-mail, nome) |

> I/O (rede, disco, Chrome) **não** entra no Big O algorítmico — é custo
> externo, dominante na prática mas independente do tamanho de entrada.

## `src/utils.py`

| Função | Complexidade | Justificativa |
|---|:---:|---|
| `validar_url(url)` | **O(L)** ≈ O(1) | Regex em URL limitada a ~2000 chars |
| `criar_driver(headless)` | **O(1)** | Config constante do ChromeDriver |

## `src/validators.py`

| Função | Complexidade | Justificativa |
|---|:---:|---|
| `validar_nome_usuario(nome)` | **O(L)** | `split` + `isalpha` percorrem o nome |
| `validar_email(email)` | **O(L)** ≈ O(1) | Regex em e-mail (RFC 5321 ≤ 254) |

## `src/db.py` (SQLite)

| Função | Complexidade | Justificativa |
|---|:---:|---|
| `inicializar_banco()` | **O(1)** | `CREATE TABLE IF NOT EXISTS` em metadado |
| `cadastrar_usuario(nome, email)` | **O(log u)** | INSERT em B-tree (índice PK implícito) |
| `listar_usuarios()` | **O(u)** | Full scan da tabela |
| `buscar_usuario_por_id(id)` | **O(log u)** | Lookup B-tree pela PK |
| `gravar_sessao_historica(...)` | **O(k)** | 1 INSERT na sessão + `executemany` de k alterações |
| `listar_sessoes_historicas(usuario_id)` | **O(r log u)** | Índice composto `(usuario_id, encerrada_em DESC)`; r = sessões do usuário |
| `obter_sessao_historica(sessao_id)` | **O(log S)** | Lookup por PK; S = total de sessões históricas |
| `listar_alteracoes_historicas(sessao_id)` | **O(k log S)** | Índice pela PK composta; retorna k linhas |

## `src/search_numbers.py`

| Função | Complexidade | Justificativa |
|---|:---:|---|
| `encontrar_numeros(texto)` | **O(n)** | `re.findall` com regex linear, 1 passada |
| `buscar_numeros_na_pagina(url)` | **O(n)** | Dominado por `encontrar_numeros` |

## `src/value_selector.py`

| Função | Complexidade | Justificativa |
|---|:---:|---|
| `_carregar_script_js()` | **O(1)** | Arquivo pequeno de tamanho fixo |
| `listar_valores_com_xpath(driver)` | **O(n · d)** | JS varre n nós; para cada folha com dígitos, `getXPath` sobe até a raiz |
| `selecionar_valor(driver)` | **O(n · d)** | Dominado por `listar_valores_com_xpath` |
| `ler_valor_por_xpath(driver, xp)` | **O(d)** médio, **O(n)** pior | XPath absoluto desce nível a nível |

## `src/form_recorder.py`

| Função | Complexidade | Justificativa |
|---|:---:|---|
| `abrir_aba_form(driver, url)` | **O(1)** | `window.open` + leitura de handles |
| `registrar_alteracao(...)` | **O(m)** | `find_elements(CSS)` é linear no DOM do form; preencher k campos + achar botão é O(k + b) ⊆ O(m) |

## `src/notifier.py`

| Função | Complexidade | Justificativa |
|---|:---:|---|
| `_ler_env(chave)` | **O(1)** amortizado | `os.environ.get` é hash; fallback em `.env` é O(linhas) mas arquivo é pequeno |
| `carregar_senha_app()` | **O(1)** | Wrapper sobre `_ler_env` |
| `carregar_remetente()` | **O(1)** | Idem |
| `enviar_email(...)` | **O(1)** algorítmico | Custo proporcional à mensagem (I/O); nada escala com `n` |
| `montar_resumo_sessao(url, valor, historico)` | **O(k)** | Itera k registros para montar linhas |
| `montar_corpo_alteracao(url, antes, depois)` | **O(n log n)** | `sorted()` sobre os sets de diferença domina |

## `backend/services/session_manager.py`

| Método | Complexidade | Justificativa |
|---|:---:|---|
| `SessionManager.criar(...)` | **O(1)** + I/O | Gera id, insere no dict, dispara driver |
| `SessionManager.obter(id)` | **O(1)** | Lookup em `dict` |
| `SessionManager.listar()` | **O(S)** | S = sessões ativas em memória |
| `SessionManager.encerrar(id)` | **O(s)** | Remove do registry (O(1)) + `_emit` broadcast para s subscribers |
| `SessionManager.iniciar_monitoramento(...)` | **O(1)** | Spawn de thread + atribuição |
| `SessionManager.subscribe(id)` | **O(1)** amortizado | `append` em lista |
| `SessionManager.unsubscribe(id, q)` | **O(s)** | `list.remove` percorre até achar |
| `SessionManager._emit(estado, event)` | **O(s)** | Itera todos os subscribers e enfileira |
| `SessionManager._loop_monitor` | **O(s)** por tick | Screenshot + broadcast; a cada `INTERVALO_SEGUNDOS/INTERVALO_SCREENSHOT` ticks também faz `refresh` + `ler_valor_por_xpath` (O(d)) + `_emit` (O(s)) |

> Nota sobre o loop: "O(1) por ciclo" seria uma simplificação válida só
> quando s = 1 (apenas uma aba aberta, caso típico). Em regime geral
> cada tick é **O(s)** e o ciclo de check completo é **O(d + s)**.

## `backend/middlewares/rate_limit.py`

| Componente | Complexidade | Justificativa |
|---|:---:|---|
| `_regra_para(metodo, caminho)` | **O(1)** | Hash lookup + 2 comparações de string |
| `RateLimitMiddleware.dispatch` | **O(w)** | w = nº de hits dentro da janela (deque com popleft no limite); w ≤ `regra.max`, portanto **O(1)** amortizado |

## `backend/routes/sessoes.py` — custos dominantes

| Endpoint | Complexidade | Dominante |
|---|:---:|---|
| `POST /sessoes` | **O(log u)** + I/O | `buscar_usuario_por_id` + abrir driver |
| `GET /sessoes/{id}` | **O(1)** | Lookup no manager |
| `GET /sessoes/{id}/valores` | **O(n · d)** | `listar_valores_com_xpath` |
| `GET /sessoes/{id}/screenshot` | **O(1)** algorítmico | CDP `Page.captureScreenshot` (I/O) |
| `POST /sessoes/{id}/selecionar` | **O(1)** | Sessão já tem o xpath — só grava e spawna thread |
| `GET /sessoes/{id}/historico` | **O(k)** | Materializa a lista em memória |
| `DELETE /sessoes/{id}` | **O(k + s)** + I/O | Grava histórico (O(k)) + `_emit encerrada` (O(s)) + envio de e-mail |
| `GET /sessoes/historicas/{id}` | **O(log S)** | Lookup por PK |
| `GET /sessoes/historicas/{id}/alteracoes` | **O(k log S)** | Leitura indexada |

## `backend/routes/usuarios.py` — custos dominantes

| Endpoint | Complexidade |
|---|:---:|
| `POST /usuarios` | **O(log u)** |
| `GET /usuarios` | **O(u)** |
| `GET /usuarios/{id}/sessoes` | **O(r log u)** (r = sessões histórias do usuário) |

## Complexidade total do algoritmo principal

Pipeline de uma sessão ativa (do `POST /sessoes` até o `DELETE`):

```
criar(url)                        → O(log u) + I/O
listar_valores_com_xpath(driver)  → O(n · d)       [setup, 1×]
iniciar_monitoramento(xpath)      → O(1)
loop (C ciclos, a cada 15s):
    refresh + ler_valor_por_xpath → O(d)
    se alterou: append historico  → O(1)
    _emit ciclo / alteracao       → O(s)
encerrar(id):
    gravar_sessao_historica       → O(k)
    montar_resumo_sessao + email  → O(k) + I/O
```

Somando:

```
T(n, d, u, k, s, C) = O(log u)
                    + O(n · d)
                    + C · O(d + s)
                    + O(k)
```

> ### **Complexidade final: O(n · d + C · (d + s) + k)**
>
> Com `s` pequeno (uma aba aberta), degenera para **O(n · d + C · d + k)**
> — linear no DOM no setup, constante por ciclo após a seleção.

## Complexidade de espaço

| Estrutura | Espaço |
|---|:---:|
| Valores + XPaths (pré-dedup) | **O(n)** |
| Set de deduplicação no selector | **O(valores únicos)** |
| `historico` em memória por sessão | **O(k)** |
| `_subscribers` por sessão | **O(s)** |
| Filas WS (buffered, maxsize=200) | **O(s · 200)** |
| Rate limit (hits por chave) | **O(chaves · max)** — finito e pequeno |
| SQLite | **O(u + S + k_total)** |

**Espaço total: O(n + k + s + u + S)** — linear em cada dimensão
independente, sem explosão.
