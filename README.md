# Rede de Soro Antiveneno no Estado de São Paulo

Plataforma web desenvolvida para reunir, explorar e comunicar resultados de um projeto de Iniciação Científica sobre acidentes com animais peçonhentos e a organização da rede de atendimento soroterápico no estado de São Paulo.

O projeto utiliza dados públicos do **Sistema de Informação de Agravos de Notificação (SINAN)** para analisar características dos acidentes, evolução temporal, gravidade, soroterapia, tempo de atendimento, distribuição espacial e fluxos de pacientes. A plataforma também prevê uma página específica para localização de unidades de atendimento soroterápico.

## Autores

- **Júlia Campos Bueno Paz Perez** — aluna de Iniciação Científica, Bacharelado em Matemática Aplicada e Computação Científica — USP.
- **Julia Graziosi Ortiz** — aluna de Iniciação Científica, Bacharelado em Matemática Aplicada e Computação Científica — USP.
- **Prof.ª Dr.ª Maristela Oliveira dos Santos** — professora orientadora.

Projeto desenvolvido no **Laboratório de Otimização (LOT)** do **Instituto de Ciências Matemáticas e de Computação da Universidade de São Paulo (ICMC-USP)**.

---

## Funcionalidades da plataforma

A plataforma está sendo organizada em diferentes áreas:

- **Página inicial:** apresentação geral do projeto.
- **Dashboard:** exploração interativa dos dados epidemiológicos e territoriais.
- **Guia Informativo:** informações de apoio sobre acidentes com animais peçonhentos e soroterapia.
- **Encontrar soro:** localização de unidades de atendimento soroterápico.
- **Sobre:** produção científica, participações em eventos, equipe e instituições de fomento.

---

# Tecnologias utilizadas

## Aplicação web

- [Astro](https://astro.build/)
- [Tailwind CSS](https://tailwindcss.com/)
- JavaScript
- HTML/CSS
- Vercel para hospedagem e implantação

As dependências da aplicação web são gerenciadas pelo **npm** e estão declaradas em:

```text
package.json
```

## Processamento de dados

Os scripts de atualização, tratamento e preparação dos dados utilizam Python.

Principais bibliotecas utilizadas:

- pandas
- NumPy
- GeoPandas
- Pyogrio
- gdown
- PySUS

As dependências Python estão registradas em:

```text
requirements.txt
```

O arquivo pode conter, de forma mínima:

```text
pandas
numpy
geopandas
pyogrio
gdown
pysus
```

---

# Estrutura geral do projeto

```text
Site-IC/
│
├── dados_local/
│   ├── sinan_animais_peconhentos_sp.csv
│   ├── sinan_sp_tratado.csv
│   ├── diagnostico_colunas.csv
│   └── divisoes.gpkg
│
├── public/
│   ├── data/
│   │   ├── filtros.json
│   │   ├── base.json
│   │   ├── gravidade.json
│   │   ├── trabalho.json
│   │   ├── mes.json
│   │   └── tempo.json
│   └── ...
│
├── scripts/
│   ├── atualizar_sinan.py
│   ├── tratar_dados.py
│   └── preparar_dashboard.py
│
├── src/
│   ├── components/
│   ├── content/
│   ├── layouts/
│   ├── pages/
│   └── styles/
│
├── .gitignore
├── astro.config.mjs
├── package.json
├── package-lock.json
├── requirements.txt
└── README.md
```

A pasta `dados_local/` contém arquivos auxiliares e bases intermediárias utilizadas apenas no processamento local e deve permanecer no `.gitignore`.

---

# Como executar o site localmente

## 1. Pré-requisitos

Para executar e modificar o site, é necessário instalar:

- [Git](https://git-scm.com/)
- [Node.js](https://nodejs.org/), preferencialmente uma versão LTS
- npm, instalado juntamente com o Node.js

O [Visual Studio Code](https://code.visualstudio.com/) é recomendado, mas não obrigatório.

Para trabalhar também com a atualização e preparação dos dados, será necessário instalar adicionalmente:

- [Python 3.13](https://www.python.org/)
- pip, instalado juntamente com o Python

> **Importante:** o pipeline de dados utiliza a biblioteca PySUS. Recomenda-se utilizar **Python 3.13** neste projeto.

Também é recomendado utilizar um ambiente virtual Python específico para o projeto.

---

## 2. Clonar o repositório

```bash
git clone https://github.com/juliabu3no/Site-IC.git
cd Site-IC
```

Caso utilize o VS Code:

```bash
code .
```

---

## 3. Instalar as dependências do site

Na raiz do projeto:

```bash
npm install
```

Esse comando lê os arquivos `package.json` e `package-lock.json` e instala automaticamente as dependências necessárias.

---

## 4. Executar o servidor de desenvolvimento

```bash
npm run dev
```

Por padrão, o endereço local será semelhante a:

```text
http://localhost:4321/
```

Para encerrar o servidor:

```text
Ctrl + C
```

---

# Como fazer alterações no site

Antes de iniciar alterações:

```bash
git pull
```

Inicie o site:

```bash
npm run dev
```

As páginas principais ficam em:

```text
src/pages/
```

Exemplos:

```text
src/pages/index.astro
src/pages/dashboard.astro
src/pages/guia.astro
src/pages/encontrar-soro.astro
src/pages/sobre.astro
```

Componentes reutilizáveis ficam em:

```text
src/components/
```

Conteúdos estruturados ficam em:

```text
src/content/
```

Arquivos estáticos e dados consumidos diretamente pelo navegador ficam em:

```text
public/
```

Antes de enviar alterações ao GitHub, teste a compilação:

```bash
npm run build
```

Para visualizar localmente a versão compilada:

```bash
npm run preview
```

Fluxo básico de versionamento:

```bash
git status
git add .
git commit -m "Descrição da alteração"
git push
```

---

# Fluxo dos dados

O pipeline separa a obtenção da base bruta, o tratamento analítico e a preparação dos arquivos leves utilizados pelo site.

```text
SINAN / PySUS
      │
      ▼
atualizar_sinan.py
      │
      ▼
dados_local/
sinan_animais_peconhentos_sp.csv
      │
      ▼
tratar_dados.py
      │
      ├── diagnóstico das colunas
      ├── remoção de variáveis fora do escopo
      ├── padronização e decodificação
      ├── tratamento de idade e tempo
      ├── validação dos códigos municipais
      ├── enriquecimento territorial
      └── cálculo de distância entre municípios
      │
      ▼
dados_local/
sinan_sp_tratado.csv
      │
      ▼
preparar_dashboard.py
      │
      ├── seleção das variáveis do dashboard
      ├── agregações
      ├── filtros
      └── compactação
      │
      ▼
public/data/*.json
      │
      ▼
Dashboard Astro
```

O navegador **não deve receber a base completa do SINAN**. A aplicação pública utiliza apenas arquivos agregados e compactos necessários às visualizações.

---

# Atualização dos dados do SINAN

O script:

```text
scripts/atualizar_sinan.py
```

é responsável pela obtenção da base epidemiológica.

Atualmente, o processo:

1. consulta os dados de acidentes com animais peçonhentos no SINAN utilizando o PySUS;
2. obtém os anos definidos para o projeto;
3. seleciona os casos em que o acidente ocorreu no estado de São Paulo e a notificação também foi realizada no estado;
4. reúne os anos em uma única base;
5. salva o CSV bruto em `dados_local/`.

O filtro estadual utiliza simultaneamente:

```text
ANT_UF = 35
SG_UF_NOT = 35
```

Assim, a base utilizada nas análises contém casos **ocorridos e notificados no estado de São Paulo**.

O script de atualização não realiza o tratamento analítico detalhado dos dados.

---

## Instalar as dependências Python

Na raiz do projeto:

```bash
py -3.13 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

---

## Executar a atualização do SINAN

```bash
python scripts/atualizar_sinan.py
```

Os arquivos brutos gerados devem permanecer em `dados_local/` e não devem ser adicionados ao GitHub.

---

# Tratamento dos dados

O script:

```text
scripts/tratar_dados.py
```

é responsável pela construção da base analítica utilizada nas etapas seguintes.

Entre os principais tratamentos realizados estão:

- diagnóstico de preenchimento, tipos e colunas constantes;
- remoção de variáveis administrativas, de residência e variáveis clínicas fora do escopo das análises;
- renomeação das variáveis utilizadas no projeto;
- decodificação das categorias do SINAN;
- padronização de valores categóricos ausentes como `Ignorado`, mantendo os códigos originais durante o processamento para rastreabilidade;
- conversão da idade codificada pelo SINAN para uma medida em anos;
- obtenção do ano da notificação e da semana epidemiológica;
- obtenção do mês do acidente a partir de `ANT_DT_ACI`;
- seleção das variáveis finais da base analítica;
- validação dos códigos de município de ocorrência e de notificação.

## Informações territoriais

O tratamento utiliza uma base territorial com os 645 municípios do estado de São Paulo.

O arquivo:

```text
dados_local/divisoes.gpkg
```

é baixado automaticamente pelo script com `gdown` quando ainda não está disponível localmente.

A base territorial acrescenta informações para os municípios de ocorrência e de notificação, incluindo:

- nome do município;
- Região de Saúde;
- RRAS;
- Departamento Regional de Saúde (DRS);
- Grupo de Vigilância Epidemiológica (GVE);
- área do município;
- população estimada pelo IBGE;
- latitude;
- longitude.

A geometria municipal não é duplicada na base epidemiológica tratada. Ela permanece no arquivo geográfico e pode ser utilizada separadamente para a construção de mapas.

## Validação territorial

Antes da associação territorial, os códigos municipais são padronizados para o formato de seis dígitos utilizado pela base geográfica.

Registros cujo município de ocorrência ou de notificação não pode ser associado a um município válido da base territorial são excluídos da base analítica utilizada nas etapas seguintes.

## Distância entre ocorrência e notificação

Após o enriquecimento territorial, o script cria:

```text
distancia_km
```

A variável é calculada pela fórmula de **Haversine**, utilizando as coordenadas de referência dos municípios de ocorrência e de notificação e o raio médio da Terra.

Portanto, `distancia_km` representa uma **distância geográfica em linha reta sobre a superfície terrestre** entre os pontos de referência dos dois municípios.

Ela não representa:

- a rota efetivamente percorrida pelo paciente;
- distância rodoviária;
- tempo de deslocamento;
- distância entre o local exato do acidente e o estabelecimento de saúde.

Quando o município de ocorrência e o município de notificação são o mesmo, a distância calculada é zero.

O resultado final do tratamento é salvo em:

```text
dados_local/sinan_sp_tratado.csv
```

---

## Executar o tratamento

Após atualizar a base bruta:

```bash
python scripts/tratar_dados.py
```

O terminal apresenta o andamento das principais etapas do processo, permitindo acompanhar leitura, diagnóstico, decodificação, tratamento temporal, validação territorial, enriquecimento geográfico e cálculo das distâncias.

---

# Preparação dos dados do dashboard

O script:

```text
scripts/preparar_dashboard.py
```

deve utilizar como entrada a base já tratada:

```text
dados_local/sinan_sp_tratado.csv
```

Sua função é preparar apenas os dados necessários para a aplicação web, evitando repetir o tratamento metodológico já realizado em `tratar_dados.py`.

Essa etapa pode incluir:

- seleção das variáveis utilizadas em cada visualização;
- aplicação dos filtros do dashboard;
- agregações por ano, animal, município ou divisão territorial;
- compactação das informações;
- geração dos arquivos JSON consumidos pela aplicação.

Os arquivos públicos são armazenados em:

```text
public/data/
```

Exemplos:

```text
public/data/filtros.json
public/data/base.json
public/data/gravidade.json
public/data/trabalho.json
public/data/mes.json
public/data/tempo.json
```

---

## Executar a preparação do dashboard

```bash
python scripts/preparar_dashboard.py
```

Depois:

```bash
npm run dev
```

Antes de enviar ao GitHub:

```bash
npm run build
```

---

# Processo completo para atualizar os dados

O fluxo completo é:

```bash
git pull
```

Ativar o ambiente Python:

```bash
.venv\Scripts\activate
```

Instalar ou atualizar as dependências, quando necessário:

```bash
python -m pip install -r requirements.txt
```

Atualizar os dados do SINAN:

```bash
python scripts/atualizar_sinan.py
```

Tratar a base:

```bash
python scripts/tratar_dados.py
```

Preparar os arquivos utilizados pelo dashboard:

```bash
python scripts/preparar_dashboard.py
```

Executar o site:

```bash
npm run dev
```

Validar a compilação:

```bash
npm run build
```

Conferir as mudanças:

```bash
git status
```

Enviar as alterações necessárias:

```bash
git add .
git commit -m "Atualiza dados do dashboard"
git push
```

> Antes do commit, confirme que nenhum CSV bruto, GeoPackage ou outro arquivo grande de `dados_local/` foi incluído acidentalmente.

---

# Dados locais e Git

Bases completas do SINAN e arquivos geográficos utilizados apenas no processamento local não são necessários para a execução pública da aplicação.

Por isso:

- `dados_local/` deve permanecer ignorada pelo Git;
- CSVs brutos e tratados não devem ser versionados;
- `divisoes.gpkg` não deve ser versionado;
- arquivos compactos de `public/data/` podem ser versionados quando necessários para o funcionamento da aplicação pública.

Antes de qualquer commit:

```bash
git status
```

---

# Implantação no Vercel

O Vercel é utilizado para hospedar a aplicação Astro.

O pipeline Python é executado localmente e **não precisa ser executado no Vercel**.

```text
PySUS / SINAN
      │
      ▼
atualizar_sinan.py
      │
      ▼
tratar_dados.py
      │
      ▼
preparar_dashboard.py
      │
      ▼
public/data/*.json
      │
      ▼
GitHub
      │
      ▼
Vercel
      │
      ▼
Aplicação pública
```

Assim, bibliotecas como pandas, NumPy, GeoPandas, Pyogrio, gdown e PySUS não precisam ser instaladas no ambiente de execução do site.

---

# Separação entre Dashboard e “Encontrar soro”

O **Dashboard** tem finalidade analítica e apresenta dados históricos e agregados sobre os acidentes e a rede de atendimento.

A página **Encontrar soro** tem finalidade operacional e será responsável por auxiliar na localização de unidades de atendimento soroterápico.

Informações de localização do usuário, disponibilidade de soros, rotas e tempo de viagem até uma unidade devem ser tratadas separadamente das análises epidemiológicas do dashboard.

---

# Fontes de dados

A principal fonte epidemiológica utilizada pelo projeto é o:

**Sistema de Informação de Agravos de Notificação (SINAN)**.

A atualização automatizada da base utiliza a biblioteca **PySUS**.

Também é utilizada uma base territorial dos municípios do estado de São Paulo para associação de município, Região de Saúde, RRAS, DRS, GVE, população e coordenadas geográficas.

---

# Créditos do desenvolvimento web

Este projeto foi construído com o framework open source **[Astro](https://astro.build/)**.

A estrutura inicial da interface foi baseada no template gratuito **[Astroship](https://github.com/surjithctly/astroship)**, desenvolvido por **Surjith S M** e disponibilizado pela **[Web3Templates](https://web3templates.com/)**.

O template original utiliza Astro e Tailwind CSS e foi adaptado para as necessidades específicas deste projeto acadêmico.

---

# Uso de Inteligência Artificial

Ferramentas de Inteligência Artificial foram utilizadas como apoio durante o desenvolvimento deste projeto.

Em particular, o **ChatGPT, da OpenAI**, foi utilizado para auxiliar em tarefas como:

- discussão da arquitetura da aplicação;
- apoio na escrita e revisão de trechos de código;
- sugestões de organização dos componentes;
- auxílio na migração e adaptação de análises para a aplicação web;
- identificação e resolução de erros;
- organização do pipeline de dados;
- documentação do projeto.

A Inteligência Artificial foi utilizada como **ferramenta de assistência ao desenvolvimento**. As decisões metodológicas, científicas e de implementação, bem como a revisão e validação dos códigos e resultados, permanecem sob responsabilidade dos autores do projeto.

---

# Desenvolvimento e manutenção

Para alterações comuns no site:

```text
git pull
   ↓
npm install          (quando necessário)
   ↓
npm run dev
   ↓
editar arquivos
   ↓
npm run build
   ↓
git status
   ↓
git add .
   ↓
git commit
   ↓
git push
   ↓
Vercel
```

Para atualização dos dados:

```text
PySUS / SINAN
   ↓
atualizar_sinan.py
   ↓
CSV bruto
   ↓
tratar_dados.py
   ↓
CSV tratado
   ↓
preparar_dashboard.py
   ↓
public/data/*.json
   ↓
npm run dev
   ↓
validação
   ↓
npm run build
   ↓
git commit / git push
   ↓
Vercel
```

---

# Status do projeto

A plataforma está em desenvolvimento.

Atualmente estão sendo consolidados:

- estrutura e conteúdo institucional do site;
- dashboard epidemiológico;
- pipeline automatizado de atualização, tratamento e preparação dos dados;
- visualizações temporais, clínicas e espaciais;
- análise territorial e de fluxos de pacientes;
- página para localização de atendimento soroterápico.

---

# Licença

Consulte o arquivo [`LICENSE`](LICENSE) deste repositório para as condições de uso e distribuição.

---

# Links úteis

- [Astro](https://astro.build/)
- [Documentação do Astro](https://docs.astro.build/)
- [Tailwind CSS](https://tailwindcss.com/)
- [PySUS](https://github.com/AlertaDengue/PySUS)
- [GeoPandas](https://geopandas.org/)
- [Astroship](https://github.com/surjithctly/astroship)
- [Web3Templates](https://web3templates.com/)
- [Vercel](https://vercel.com/)
