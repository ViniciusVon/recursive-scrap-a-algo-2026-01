# Guia de Testes - Auction Bid Assistant

## Pre-requisitos

1. Python 3.9+
2. Chrome instalado
3. Dependencias instaladas: `pip install -r requirements.txt`

---

## Passo 1: Iniciar o Servidor Local

Abra um terminal e execute:

```bash
cd "/Users/gabrielheni/Desktop/stop reading my files /vscode/faculdade/analise_algo_2026/work_01/recursive-scrap-a-algo-2026-01/test_pages"
python3 -m http.server 8080
```

Deixe este terminal aberto. O servidor estara rodando em `http://localhost:8080`

---

## Passo 2: Verificar as Paginas de Teste

Abra no navegador:
- Produto: http://localhost:8080/product.html
- Notificador: http://localhost:8080/notifier.html

---

## Passo 3: Executar o Auction Bid Assistant

Em outro terminal, execute:

```bash
cd "/Users/gabrielheni/Desktop/stop reading my files /vscode/faculdade/analise_algo_2026/work_01/recursive-scrap-a-algo-2026-01"
python3 -m src.main
```

---

## Passo 4: Configuracao Interativa

### 4.1 Username
- Digite um nome com 3+ letras (ex: `gabriel`)
- Teste invalido: `ab` (deve dar erro)
- Teste invalido: `user123` (deve dar erro - so letras)

### 4.2 Monitor URL
- Digite: `http://localhost:8080/product.html`
- Teste invalido: `localhost:8080` (deve dar erro - falta http)

### 4.3 Notifier URL
- Digite: `http://localhost:8080/notifier.html`

---

## Passo 5: Selecionar Elemento de Preco

1. O browser abre a pagina do produto
2. O sistema lista elementos com precos encontrados
3. Digite o numero do elemento que mostra "R$ 4.599,00"
4. Confirme a selecao

---

## Passo 6: Configurar Notificador

1. O browser abre a pagina do notificador
2. Selecione o **textarea** (campo de mensagem)
3. Selecione o **botao** "Enviar Notificacao"

---

## Passo 7: Testar Monitoramento

1. Defina o intervalo (ex: `5` segundos)
2. O monitoramento inicia
3. **VA ATE A PAGINA DO PRODUTO** no browser que o Selenium abriu
4. Clique em "Simular Novo Lance"
5. Aguarde o proximo ciclo de verificacao
6. O sistema deve:
   - Detectar a mudanca de preco
   - Enviar notificacao automaticamente
   - Mostrar no console: `[ALERT] Price changed`

---

## Passo 8: Encerrar

- Pressione `Ctrl+C` no terminal
- O sistema mostra o resumo de logs
- Os browsers fecham automaticamente

---

## Testes de Validacao (Casos de Erro)

| Input | Esperado |
|-------|----------|
| Username: `ab` | Erro: minimo 3 caracteres |
| Username: `user1` | Erro: apenas letras |
| URL: `google.com` | Erro: falta scheme |
| URL: `ftp://files.com` | Erro: deve ser http/https |
| URL vazia | Erro: URL cannot be empty |

---

## Checklist de Funcionalidades

- [ ] Validacao de username funciona
- [ ] Validacao de URL funciona
- [ ] Browser abre pagina de monitoramento
- [ ] Deteccao de precos com RegEx funciona
- [ ] Selecao interativa de elemento funciona
- [ ] Browser abre pagina de notificacao
- [ ] Selecao de input/botao funciona
- [ ] Loop de monitoramento executa
- [ ] Mudanca de preco e detectada
- [ ] Notificacao e enviada automaticamente
- [ ] Logs sao registrados corretamente
- [ ] Shutdown gracioso com Ctrl+C
