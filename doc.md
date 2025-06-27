# 📘 Especificação Técnica - Ferramenta de Documentação de Relacionamento entre Arquivos/Classes Python

## 🧩 Objetivo

Desenvolver uma ferramenta que analisa um projeto Python e gera **uma documentação em HTML interativa** com **diagramas de dependência entre arquivos e classes**, baseando-se em **importações** e **referências internas**. Essa documentação deve facilitar a compreensão da **arquitetura do projeto** por desenvolvedores e analistas.

---

## ✅ Funcionalidades Principais

### 1. Análise Estática de Código
- Analisar arquivos `.py` de forma recursiva a partir de um diretório base.
- Utilizar a biblioteca `ast` para identificar:
  - Importações entre módulos (`import`, `from ... import ...`)
  - Definições de classes e funções
  - Uso de classes de outros módulos (dependência de uso)

### 2. Mapeamento e Construção do Grafo
- Gerar um **grafo direcionado**:
  - Nós: arquivos `.py` e/ou classes identificadas
  - Arestas: dependências (importações ou uso)
- Relacionamento em dois níveis:
  - Entre **arquivos**
  - Entre **classes**, quando possível

### 3. Geração de Visualização Interativa em HTML
- Gerar HTML interativo com visualização do grafo:
  - Utilizar bibliotecas como `pyvis`, `d3.js` ou `vis-network.js`
  - Cada nó do grafo deve ser clicável, levando à visualização dos detalhes do arquivo ou classe
  - Arestas devem exibir tooltip com o tipo de relacionamento

### 4. Geração de Documentação HTML
- Estrutura de documentação:
  - Página principal com o grafo de dependência
  - Página por arquivo:
    - Lista de classes/funções contidas
    - Relações de dependência (quem importa/é importado)
  - Página por classe (se possível):
    - Métodos, atributos, heranças, etc.
- Navegação entre arquivos/classes a partir do grafo

---

## 🧪 Requisitos Técnicos

### Linguagem
- Python 3.8+

### Bibliotecas sugeridas
- `ast` – para análise estática do código
- `pyvis` ou `networkx` + `pyvis` – para geração de grafos em HTML
- `jinja2` – para templating HTML das páginas
- `os`, `glob`, `pathlib` – para leitura de diretórios

---

## 📂 Estrutura Esperada do Projeto

```text
docs/
├── index.html                 # Página com o grafo geral
├── modules/
│   ├── app__main.html         # Representação do arquivo app/main.py
│   ├── utils__parser.html     # Representação do arquivo utils/parser.py
├── classes/
│   ├── Parser.html            # Representação da classe Parser
├── assets/
│   ├── graph-style.css
│   └── interactivity.js

## ⚙️ Configurações

### Arquivo de Configuração (`config.yaml`)

-   Diretório raiz do projeto a ser documentado
    
-   Tipos de visualização a serem gerados: `arquivos`, `classes`, ou ambos
    
-   Formato de saída: `html`, `json` (grafo bruto opcional)
    

* * *

## 📈 Exemplo de Uso

bash

CopiarEditar

`python generate_docs.py --config config.yaml`

Saída:

-   HTML gerado na pasta `docs/`
    
-   Grafo interativo visualizável em navegador
    

* * *

## 🔐 Requisitos Não Funcionais

-   A ferramenta deve ser multiplataforma (Linux, macOS, Windows)
    
-   Não deve executar código do projeto (análise puramente estática)
    
-   Geração completa deve ocorrer em menos de 30 segundos para projetos com até 300 arquivos
    

* * *

## 💡 Diferenciais (Extras/Futuros)

-   Suporte a notebooks `.ipynb`
    
-   Análise de dependência por função (grau mais granular)
    
-   Exportação para PDF/Markdown além de HTML
    
-   Integração com CI/CD (ex: gerar automaticamente ao fazer push para o repositório)
    

* * *

## 📦 Entregáveis

-   Script principal `generate_docs.py`
    
-   Templates HTML e assets CSS/JS
    
-   Documentação de uso em `README.md`
    
-   Exemplo de output em `docs/example_project/`
    

* * *



