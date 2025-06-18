# OpenAPI Fixer & Enhancer

Este projeto contém um conjunto de scripts Python para ler um arquivo OpenAPI 3.0.1 gerado automaticamente (em formato JSON ou YAML), aplicar uma série de correções e melhorias, e exportar um novo arquivo YAML otimizado para ferramentas de documentação como Swagger UI, Stoplight, etc.

## Funcionalidades

O script aplica as seguintes regras de transformação:

1. **Adiciona Metadados:** Insere informações essenciais ausentes como `info`, `servers`, `license` e `contact`.
2. **Substitui Chaves i18n:** Traduz todas as descrições que usam chaves de internacionalização (ex: `api.doc.v1.x.description`) para texto legível, com base em um dicionário local.
3. **Define Autenticação:** Adiciona um esquema de segurança global (`BearerAuth` via HTTP header) a todas as operações.
4. **Respostas de Erro Padrão:** Inclui respostas de erro comuns (`400`, `401`, `403`, `404`, `500`) em endpoints que não as possuem.
5. **Normaliza Tags:** Converte nomes de tags (ex: `api.doc.v3.section.pointofsale.title`) para nomes curtos e legíveis (ex: `Pontos de Venda`) e adiciona uma descrição.
6. **Corrige `operationId` Duplicados:** Detecta `operationId`s duplicados ou genéricos (ex: `findById_1`) e os renomeia de forma semântica, usando o método HTTP e o path (ex: `getEmployeeById`).
7. **Enriquece Parâmetros:** Adiciona `example`s simples e validações (`minimum`, `maximum`) para parâmetros comuns como `id`, `page`, `size`, etc.

## Pré-requisitos

* Python 3.8+

## Instalação

1. Clone este repositório:

    ```bash
    git clone https://github.com/rafactx/involves-openapi-fixer
    cd involves-openapi-fixer
    ```

2. Instale as dependências:

    ```bash
    pip install -r requirements.txt
    ```

## Como Usar

Execute o script `fix_openapi.py` a partir da linha de comando, especificando o arquivo de entrada.

### Exemplo de Uso

Supondo que seu arquivo gerado automaticamente seja `openapi.json`:

```bash
python fix_openapi.py --input openapi.json --output openapi.fixed.yaml
```

**Argumentos:**

* `--input` (obrigatório): O caminho para o seu arquivo `openapi.json` ou `openapi.yaml`.
* `--output` (opcional): O nome do arquivo de saída. O padrão é `openapi.fixed.yaml`.

Após a execução, o script exibirá um relatório com as alterações realizadas e o arquivo `openapi.fixed.yaml` será criado no diretório.

## Customização

* **Traduções (i18n):** Para adicionar ou modificar as descrições, edite o dicionário `TRANSLATIONS` no arquivo `i18n.py`.
* **Mapeamento de Tags:** Para alterar como as tags são normalizadas, modifique o dicionário `TAG_MAP` no arquivo `tag_map.py`.
