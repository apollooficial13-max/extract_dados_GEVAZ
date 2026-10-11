# GEVaz — Pipeline de Extração e Consolidação de Dados

Pipeline em Python para **extrair, organizar e consolidar dados geográficos e arquivos de metadados** relacionados à base GEVaz. O projeto lê arquivos encontrados na pasta `Dados_extraidos`, preserva as colunas originais e gera saídas em CSV, JSON e Excel para análise ou integração futura com um banco de dados.

## Funcionalidades

- **Extração de arquivos:** lista recursivamente os arquivos encontrados na pasta de entrada.
- **Leitura de shapefiles:** processa bases de Distritos Sanitários, Estações Disseminadoras e Ovitrampas 2026.
- **Leitura de XML:** extrai tags, textos e atributos dos arquivos XML de metadados.
- **Preservação dos dados:** mantém as colunas originais e adiciona campos auxiliares de origem e geolocalização.
- **Exportação individual:** salva cada conjunto de dados em CSV e JSON.
- **Consolidação:** gera uma planilha Excel, um JSON único e um CSV consolidado.

## Tecnologias

- Python
- Pandas
- GeoPandas
- OpenPyXL

## Estrutura do projeto

```text
codigo_gevaz/
├── Dados_extraidos/          # Dados de entrada (não incluídos no repositório)
├── Extract.py                # Extração dos arquivos e dados geográficos
├── Load.py                   # Exportação individual em CSV e JSON
├── Transform.py              # Preparação e consolidação dos dados
├── Main.py                   # Execução completa do pipeline
├── requirements.txt          # Dependências Python
└── .gitignore                # Arquivos e pastas ignorados pelo Git
```

## Requisitos

- Python 3.10 ou superior (recomendado).
- Arquivos de entrada organizados conforme a estrutura esperada pelo projeto.
- `pip` para instalar as dependências.

## Instalação

Clone o repositório:

```bash
git clone <URL_DO_REPOSITORIO>
cd codigo_gevaz
```

Crie e ative um ambiente virtual.

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows (Prompt de Comando):**

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

**Linux/macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instale as dependências:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Preparação dos dados

Coloque os dados de entrada dentro da pasta `Dados_extraidos`, respeitando os nomes e a organização esperados pelo código. Entre os caminhos previstos estão:

```text
Dados_extraidos/
├── BASE Distritos sanitários shapefile/
├── ESTAÇÕES DISSEMINADORAS shapefile/
│   ├── DS 1/
│   ├── DS 2/
│   └── ... DS 8/
└── ATUALIZAÇÃO TOTAL DAS OVITRAMPAS 2026 shapefile/
    ├── DS 1/
    ├── DS 2/
    └── ... DS 8/
```

Os shapefiles precisam conter seus arquivos auxiliares necessários (por exemplo, `.shp`, `.shx`, `.dbf` e, quando aplicável, `.prj`). Os XMLs de metadados `*.shp.xml` são lidos quando encontrados no caminho esperado.

> **Importante:** a pasta `Dados_extraidos` está no `.gitignore` e não é enviada ao Git. Obtenha os dados por uma fonte autorizada e coloque-os localmente antes de executar o pipeline.

## Como executar

Com o ambiente virtual ativado e os dados preparados, execute na raiz do projeto:

```bash
python Main.py
```

O `Main.py` executa as etapas na seguinte ordem:

1. **Extract:** lê os arquivos e monta os conjuntos de dados.
2. **Load:** salva cada conjunto individualmente em CSV e JSON.
3. **Transform:** consolida os conjuntos em arquivos finais.

Também é possível executar módulos isoladamente para testes:

```bash
python Extract.py
python Load.py
```

## Arquivos gerados

Após uma execução bem-sucedida, serão criadas as pastas:

| Pasta | Conteúdo |
|---|---|
| `Dados_csv/` | Arquivos CSV individuais |
| `Dados_json/` | Arquivos JSON individuais |
| `Dados_Gevaz_Gerais/` | Arquivos consolidados |

Na pasta `Dados_Gevaz_Gerais/`:

- `dados_completos.xlsx` — uma aba por conjunto de dados e uma aba `resumo`.
- `dados_completos.json` — todos os conjuntos em um único JSON.
- `dados_completos.csv` — conjuntos empilhados, identificados pela coluna `conjunto`.

Para dados geográficos, o processo também adiciona campos auxiliares como `arquivo_origem`, `caminho_origem`, `crs_origem`, `geometry_wkt`, `tipo_geometria`, `latitude` e `longitude`, quando aplicável. As coordenadas auxiliares são calculadas para uso em graus (EPSG:4326) quando o sistema de referência de coordenadas original está disponível.

## Observações

- A execução pode falhar se os caminhos esperados não existirem ou se algum arquivo estiver inválido. Confira a estrutura de `Dados_extraidos` e as mensagens exibidas no terminal.
- Os arquivos gerados podem ocupar bastante espaço, dependendo do volume dos dados.
- Verifique a política de privacidade e as permissões de compartilhamento antes de publicar dados reais no GitHub.
- Este projeto prepara arquivos para integração futura com banco de dados; o código atual não realiza, por si só, uma gravação direta em banco de dados.

## Licença

Nenhuma licença foi identificada nos arquivos fornecidos. Antes de permitir reutilização por terceiros, escolha e adicione uma licença apropriada ao repositório.
