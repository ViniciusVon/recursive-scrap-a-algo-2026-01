# Documentação — Monitor de Preços

Índice da documentação do projeto. Tudo o que não é `README.md` raiz mora aqui.

## Visão por camada

| Camada | Overview | Complexidade |
|--------|----------|--------------|
| Backend (FastAPI + Selenium) | [`backend.md`](./backend.md) | [`complexidade_backend.md`](./complexidade_backend.md) |
| Frontend (React + Vite) | [`frontend.md`](./frontend.md) | [`complexidade_frontend.md`](./complexidade_frontend.md) |

## Outros artefatos

- [`git-flow-example.jpg`](./git-flow-example.jpg) — diagrama do fluxo de branches
  (feature/fix/release/hotfix) usado pelo grupo.

## Onde mora o quê

- **Especificação do trabalho + Big O consolidado** → `README.md` na raiz.
- **Como rodar (backend/frontend, dev e Docker)** → `backend.md` e `frontend.md`.
- **Análise Big O por módulo** → os dois `complexidade_*.md`. Ambos são validados
  contra o código em `main` e batem com os docstrings das funções.
