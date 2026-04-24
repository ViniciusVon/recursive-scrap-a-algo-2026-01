# Frontend — Monitor de Preços

SPA em React + TypeScript que consome a API FastAPI do backend.

## Stack

| Camada             | Tecnologia                              |
| ------------------ | --------------------------------------- |
| Build / dev-server | [Vite](https://vitejs.dev)              |
| UI                 | React 19 + TypeScript                   |
| Styling            | Tailwind CSS 3                          |
| Estado global      | [Zustand](https://github.com/pmndrs/zustand) |
| Validação          | [Zod](https://zod.dev)                  |
| HTTP               | `fetch` nativo + cliente fino (`api/client.ts`) |
| Streaming ao vivo  | WebSocket (`hooks/useSessionWS`)        |
| Testes             | Vitest + Testing Library + jsdom        |

## Estrutura

```
frontend/src/
├── api/
│   ├── client.ts        # fetch + ApiError + retry em verbos idempotentes
│   └── schemas.ts       # Zod schemas (espelham Pydantic do backend)
├── components/
│   ├── BrowserPreview.tsx  # stream de screenshots do monitor
│   ├── ErrorBoundary.tsx   # captura erros de render
│   ├── Skeleton.tsx        # placeholders de loading
│   └── ToastContainer.tsx  # stack global de notificações
├── hooks/
│   ├── useSessionWS.ts            # conexão + reconnect do WS
│   └── useNotificarAlteracoes.ts  # toast + Notification nativa
├── pages/
│   ├── SetupWizard.tsx  # fluxo de 3 passos até escolher o valor
│   └── MonitorPage.tsx  # painel ao vivo (chega via /monitor/:id)
├── store/
│   ├── sessionStore.ts  # estado da sessão ativa (WS)
│   └── toastStore.ts    # fila de toasts + API `toast.sucesso/erro/...`
└── test/                # suites Vitest
```

## Scripts

```bash
npm install          # dependências
npm run dev          # dev-server em http://localhost:5173
npm run build        # typecheck + bundle para dist/
npm run test         # vitest run (CI)
npm run test:watch   # vitest em modo interativo
npm run lint         # eslint
npm run preview      # serve o dist/ localmente
```

## Variáveis de ambiente

| Variável             | Default                 | Descrição                               |
| -------------------- | ----------------------- | --------------------------------------- |
| `VITE_API_BASE_URL`  | `http://localhost:8000` | Base das chamadas HTTP/WS               |

O Vite inlineia o valor no bundle — troca requer rebuild.

## Fluxo

1. **Step Usuário** — lista existentes ou cadastra novo (validação Zod
   em tempo real; strict no backend barra campos desconhecidos).
2. **Step URL** — valida `http(s)://`, lembra a última URL via
   `localStorage`, mostra sessões anteriores do usuário.
3. **Step Valor** — screenshot via CDP + lista de números encontrados.
   Escolher um abre o `/monitor/:id` em nova guia.
4. **MonitorPage** — WebSocket recebe `inicial`, `ciclo`, `alteracao`,
   `screenshot`, `encerrada`. Cada `alteracao` dispara toast +
   `Notification` nativa (quando concedida).

## Tratamento de erros

- `ApiError` (em `api/client.ts`) carrega `status` + `detail`.
- `mensagemDeErro(e)` extrai texto legível: array de validação do
  Pydantic → `body.detail[0].msg`; falha de rede → status 0 com
  mensagem genérica.
- Falhas de rede em GET/HEAD/OPTIONS passam por 2 retries com backoff
  (250ms, 750ms). POST/DELETE não são refeitos automaticamente.
- `<ToastContainer />` em App.tsx renderiza a fila global; qualquer
  módulo usa `toast.sucesso(...)` / `toast.erro(...)`.
- `<ErrorBoundary />` envolve as rotas — erros de render caem na UI
  de fallback em vez de quebrar a tela inteira.

## Produção via Docker

Do root do repo:

```bash
docker compose up --build
```

Sobe backend em `:8000` e frontend (nginx) em `:5173`. Veja o
`docker-compose.yml` pra variáveis (`GMAIL_USER`, `CORS_ORIGINS`).

## Análise de complexidade

Consulte [`complexidade_frontend.md`](./complexidade_frontend.md)
para a análise Big O dos principais fluxos do frontend.
