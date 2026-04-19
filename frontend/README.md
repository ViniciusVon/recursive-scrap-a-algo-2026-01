# Frontend — Monitor de Preços

Fase 1 (MVP) do frontend: React 19 + Vite + TypeScript + Tailwind CSS v3.

## Rodar em desenvolvimento

```bash
cd frontend
npm install
npm run dev
```

O Vite sobe em `http://localhost:5173` e consome a API FastAPI em
`http://localhost:8000` (override via `VITE_API_BASE_URL`).

## Build de produção

```bash
npm run build
```

Gera `dist/` com os assets estáticos.

## Estrutura

```
src/
├── api/client.ts      # cliente HTTP (fetch) + tipos
├── pages/
│   ├── LoginPage.tsx        # Tela 1 — identificação
│   ├── ConfigPage.tsx       # Tela 2 — URL + headless
│   ├── SelectValuePage.tsx  # Tela 4 — escolha do valor
│   └── DashboardPage.tsx    # Tela 3 — monitor + histórico
├── App.tsx            # shell + rotas
└── main.tsx
```

## Próximas fases

- Fase 2 (#28): WebSocket, streaming de screenshots do Selenium
- Fase 3 (#29): design system polido, dark mode, hover-to-highlight
- Fase 4 (#30): validações, testes, Docker Compose
