# Trabalho 01 - Análise de Algoritmos

## Desenvolver um assistente de lances para sites de leilão

### O objetivo é monitorar um preço que está dentro de uma página WEB, a qual você não sabe previamente a estrutura (o usuário vai passar a URL na hora de informar detro da página qual é o cammpmo a ser analisado).

### Ao identificar a mudança de preços, você deverá interagir com outra página (Qualquer uma que serja pública - você não controla o código fonte dela.) e inserir um textoinfromando o valor antigo e o novo e clicar em um botão.

### Outro sistema público - Gmail, por exemplo, e clicar no botão de send.

## Calcular

### Calcule o Big O do seu código.
### Pode usar qualquer biblioteca.
### Qualquer linguagem, arquitetura e cliente - WEB, app mobile ou desktop.

## *Critérios*

### **0 pontos** -> O sistema que não encontrar a variável OU travar durante a execução do código, seja por bug ou por não validação de entrada de usuário.

### **2 pontos** -> Se encontrar o número na página (o sistema deve logar no console sua posição na página - Xpath, Regex)

### **2 pontos** -> Monitorar adequadamente (O sistema deve logar no console todas as alterações identificadas do número).

### **2 pontos** -> Se identificar alteração, registar em outra página e acionar um botão da tela

### **1 ponto** -> Documentação do código
#### O resultado deve ser apresentado utilizando Sphinx, pydoc ou MkDocs, ou outra ferramenta.

### **1 ponto** -> Se o sistema tiver um log de ações do usuário (todas).
#### Nesse caso deve pedir o nome do usuário como entrada (Nesse caso não precisa ter crítica, exceto se é um nome composto APENAS por caracteres com ao menos 3 caracteres, Os nomes podem ser duplicados).

### **1 ponto** -> Se os testes unitários estiverem automatizados.

### **1 ponto** -> Se o big O estiver correto.

### *Ponto Extra*
#### **1 ponto** -> Se o git do projeto "contar" a história da evolução. Com commits de todos alunos, evoluções, controles de bugs, etc...
#### **1 ponto** -> Se a interface for amigável e intuitiva

## *Regras*

### No dia da apresentação todos devem estar presentes.
### A nota é do grupo. Perguntas serão feitas para os membros do grupo durante a apresentação sobre o código apresentado.

# **Proposta de Ferramentas**

## Utilizar RegEx para busca de valores nas páginas (De acordo com a página que o usuário informar).
## Utilizar Selenium para descobrir o Xpath daquele elemento que buscamos com o RegEx
## Utilizar python para a implementação do web scrapping

# **Organização do Repositório**

## Utilizaremos cada ponto a ser alcançado como uma milestone, com isso conseguiremos ter um controle melhor sobre o que precisa ser feito.
## Faremos uma pipeline de verificação de testes e build do projeto para um possível deploy em ambiente de homologação / produção
## Seguiremos o padrão de gitflow para a criação de branchs bem como a criação de Pull Requests.
### Nomes de branchs seguirão o modelo:
- **feature/nome-da-feature** -> para o desenvolvimento de novas funcionalidades que serão atribuídas a um milestone.

- **fix/nome-do-fix** -> para o desenvolvimento de ajustes de funcionalidades existentes dentro de um milestone.

- **release/version** -> Utilizaremos essa nomenclatura de branch para subir a versão para a branch principal. Version será o nome da versão que subiremos (Ex: 0.1.0).

- **hotfix/nome-do-hotfix** -> Se, porventura, subirmos o projeto para hospedagem, essa nomenclatura seria interessante caso for preciso realizar uma alteração urgente no projeto.

## *Lembrando que os commits precisam ter uma issue relacionada.*

## Cada Pull Request deverá ter 2 reviewers para que o código que vá para a branch principal tenha menos probabilidade de dar erro.

---

# **Análise de Complexidade (Big O)**

Esta seção analisa a complexidade assintótica de tempo de cada função
relevante do projeto e chega na complexidade total do algoritmo principal
(`monitorar_preco`), que é o que rege o custo da aplicação em execução.

## Variáveis usadas na análise

| Símbolo | Significado |
|:-------:|:------------|
| `n`     | Número de elementos no DOM da página monitorada |
| `d`     | Profundidade média da árvore do DOM (depth) |
| `m`     | Número de elementos no DOM do Google Form |
| `u`     | Número de usuários cadastrados no SQLite |
| `L`     | Tamanho (em caracteres) de uma string de entrada (URL, e-mail) |
| `C`     | Número de ciclos executados no loop de monitoramento |
| `k`     | Quantidade de valores numéricos retornados pelo seletor |

> **Observação:** custos de I/O (rede, disco, execução do Chrome) **não**
> entram no Big O algorítmico — são dominantes na prática, mas não escalam
> com o tamanho da entrada do nosso algoritmo.

## Complexidade por módulo / função

### `src/utils.py`
| Função | Complexidade | Justificativa |
|---|:---:|---|
| `validar_url(url)`     | **O(L)** ≈ O(1) | Regex match em URL de tamanho limitado |
| `criar_driver(headless)` | **O(1)**      | Configuração constante do ChromeDriver |

### `src/validators.py`
| Função | Complexidade | Justificativa |
|---|:---:|---|
| `validar_nome_usuario(nome)` | **O(L)** | `split` + `isalpha` percorrem a string |
| `validar_email(email)`       | **O(L)** ≈ O(1) | Regex sobre e-mail limitado (RFC 5321) |

### `src/db.py` (SQLite)
| Função | Complexidade | Justificativa |
|---|:---:|---|
| `inicializar_banco()`          | **O(1)**      | `CREATE TABLE IF NOT EXISTS` em metadado |
| `cadastrar_usuario(nome,email)`| **O(log u)**  | INSERT no B-tree do SQLite (índice PK) |
| `listar_usuarios()`            | **O(u)**      | Full scan da tabela |
| `buscar_usuario_por_id(id)`    | **O(log u)**  | Lookup por chave primária no B-tree |

### `src/search_numbers.py`
| Função | Complexidade | Justificativa |
|---|:---:|---|
| `encontrar_numeros(texto)` | **O(n)** | `re.findall` percorre o texto 1× (regex linear) |
| `buscar_numeros_na_pagina(url)` | **O(n)** | Dominado por `encontrar_numeros`; `driver.get` é I/O |

### `src/value_selector.py`
| Função | Complexidade | Justificativa |
|---|:---:|---|
| `_carregar_script_js()`            | **O(1)**        | Lê arquivo pequeno de tamanho fixo |
| `listar_valores_com_xpath(driver)` | **O(n · d)**    | JS varre n nós do DOM e, para cada folha com dígitos, `getXPath` sobe até a raiz (profundidade d). Deduplicação em Python é O(k) |
| `selecionar_valor(driver)`         | **O(n · d)**    | Dominado por `listar_valores_com_xpath` |
| `ler_valor_por_xpath(driver,xp)`   | **O(d)** *(médio)*, O(n) *(pior)* | Avaliação de XPath absoluto desce nível a nível |

### `src/form_recorder.py`
| Função | Complexidade | Justificativa |
|---|:---:|---|
| `abrir_aba_form(driver, url)`      | **O(1)** | `window.open` + leitura de handles |
| `registrar_alteracao(...)`         | **O(m)** | `find_elements` varre todo o DOM do form; preenchimento e busca de botão são O(campos + botões) ⊆ O(m) |

### `src/notifier.py`
| Função | Complexidade | Justificativa |
|---|:---:|---|
| `carregar_senha_app()`               | **O(1)** | `.env` tem poucas linhas (tamanho constante) |
| `enviar_email(...)`                  | **O(1)** algorítmico | Custo proporcional ao tamanho da mensagem (I/O) |
| `montar_corpo_alteracao(url,a,d)`    | **O(n log n)** | `sorted()` sobre sets de diferença domina `O(k)` das operações de conjunto |

### `app.py`
| Função | Complexidade | Justificativa |
|---|:---:|---|
| `identificar_usuario()` | **O(u)**          | Dominado por `listar_usuarios`; cadastro/busca são O(log u) |
| `coletar_entradas()`    | **O(u)**          | Dominado por `identificar_usuario` |
| `monitorar_preco(...)`  | **O(n·d + C·n)**  | Setup O(n·d) + C iterações de O(n) |
| `main()`                | **O(n·d + C·n)**  | Dominado por `monitorar_preco` |

## Complexidade total do algoritmo principal

O pipeline da aplicação é:

```
main()
 ├── inicializar_banco()            → O(1)
 ├── coletar_entradas()             → O(u)
 └── monitorar_preco()
      ├── driver.get(url)            → I/O
      ├── selecionar_valor(driver)   → O(n · d)          [setup, 1×]
      ├── abrir_aba_form(...)        → O(1)
      └── loop (C ciclos):
           ├── refresh               → I/O
           ├── ler_valor_por_xpath   → O(d)  médio
           └── [se alterou]
                registrar_alteracao  → O(m)
```

Somando:

```
T(n, d, m, u, C) = O(u) + O(n · d) + C · [ O(d) + α · O(m) ]
```

Onde `α ∈ [0, 1]` é a fração de ciclos em que houve alteração
(na prática α « 1). Como `d ≤ n` e `u` é independente das demais:

> ### **Complexidade final: O(n · d + C · (d + α · m))**
>
> Assumindo `α → 0` em regime estacionário (poucas alterações por ciclo),
> a complexidade se reduz a **O(n · d + C · d)**, ou seja, **linear no DOM
> para o setup e praticamente constante por ciclo** após a seleção inicial.

## Por que essa complexidade é adequada

1. **Setup pago uma vez**: o custo `O(n · d)` de listar todos os valores
   numéricos com seus XPaths ocorre só no início, não a cada ciclo.
2. **Ciclo barato**: dentro do loop de monitoramento, a leitura é feita
   por um único `XPath` absoluto — o navegador resolve isso em `O(d)`
   (profundidade do caminho), sem varrer o DOM inteiro.
3. **Sem estruturas quadráticas**: nenhuma rotina faz loop dentro de
   loop sobre o DOM. O JavaScript de listagem é `O(n · d)`, não `O(n²)`.
4. **Escalabilidade**: dobrar o tempo de monitoramento (C) não re-executa
   o setup, apenas soma `C · O(d)` — portanto o sistema pode monitorar
   uma página por horas sem degradação.

## Complexidade de espaço

| Estrutura | Espaço |
|---|:---:|
| Lista de valores + XPaths (pré-dedup)   | **O(n)**  |
| Set de valores vistos (deduplicação)    | **O(k)**  |
| `historico` de alterações               | **O(α · C)** |
| Banco SQLite (usuários)                 | **O(u)** |

**Espaço total: O(n + α · C + u)** — linear em cada dimensão
independente, sem explosão de memória durante a execução.