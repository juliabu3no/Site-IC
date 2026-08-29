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

Os scripts auxiliares de atualização e preparação dos dados utilizam Python.

Principais bibliotecas previstas/utilizadas:

- pandas
- GeoPandas
- gdown
- PySUS

As dependências Python devem ser registradas em:

```text
requirements.txt
```

---

# Estrutura geral do projeto

```text
Site-IC/
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

> Alguns arquivos mostrados acima fazem parte da estrutura planejada do pipeline de dados e podem ainda estar em implementação.

---

# Como executar o site localmente

Esta seção é destinada a quem deseja baixar o projeto do GitHub, fazer alterações ou executar a aplicação no próprio computador.

## 1. Pré-requisitos

Para executar e modificar o site, é necessário instalar:

- [Git](https://git-scm.com/)
- [Node.js](https://nodejs.org/), preferencialmente uma versão LTS
- npm, instalado juntamente com o Node.js

O [Visual Studio Code](https://code.visualstudio.com/) é recomendado, mas não obrigatório.

Para trabalhar também com a atualização e preparação dos dados, será necessário instalar adicionalmente:

- [Python 3.13](https://www.python.org/)
- pip, instalado juntamente com o Python

> **Importante:** o pipeline de dados utiliza a biblioteca PySUS, que atualmente requer uma versão do Python entre 3.11 e 3.13. Por esse motivo, recomenda-se utilizar **Python 3.13** neste projeto. Python 3.14 não deve ser utilizado para os scripts de atualização dos dados.

Também é recomendado utilizar um ambiente virtual Python específico para o projeto, conforme descrito nas etapas de instalação.

---

## 2. Clonar o repositório

Abra um terminal e execute:

```bash
git clone https://github.com/juliabu3no/Site-IC.git
```

Entre na pasta do projeto:

```bash
cd Site-IC
```

Caso utilize o VS Code:

```bash
code .
```

---

## 3. Instalar as dependências do site

Na raiz do projeto, execute:

```bash
npm install
```

Esse comando lê os arquivos `package.json` e `package-lock.json` e instala automaticamente as dependências necessárias.

Será criada localmente a pasta:

```text
node_modules/
```

Essa pasta não deve ser adicionada manualmente ao GitHub.

---

## 4. Executar o servidor de desenvolvimento

Execute:

```bash
npm run dev
```

O Astro iniciará um servidor local. Por padrão, o endereço será semelhante a:

```text
http://localhost:4321/
```

Abra esse endereço no navegador.

Enquanto o servidor estiver ativo, alterações nos arquivos do projeto normalmente serão atualizadas automaticamente no navegador.

Para encerrar o servidor:

```text
Ctrl + C
```

---

# Como fazer alterações no site

## 1. Atualizar o repositório local

Antes de começar uma nova alteração, é recomendado garantir que a cópia local esteja atualizada:

```bash
git pull
```

---

## 2. Iniciar o site

```bash
npm run dev
```

---

## 3. Localizar os arquivos

As páginas principais ficam em:

```text
src/pages/
```

Por exemplo:

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

Conteúdos estruturados, como informações da equipe, ficam em:

```text
src/content/
```

Arquivos estáticos e arquivos de dados usados diretamente pelo navegador ficam em:

```text
public/
```

---

## 4. Testar as alterações

Com o servidor ativo:

```bash
npm run dev
```

verifique as páginas localmente antes de enviar as mudanças ao GitHub.

Também é recomendado testar a compilação da aplicação:

```bash
npm run build
```

Se o comando terminar sem erros, a aplicação foi compilada corretamente.

Para visualizar localmente a versão compilada:

```bash
npm run preview
```

---

## 5. Conferir os arquivos alterados

```bash
git status
```

---

## 6. Adicionar as alterações

Para adicionar todos os arquivos modificados:

```bash
git add .
```

Ou, para adicionar um arquivo específico:

```bash
git add caminho/do/arquivo
```

---

## 7. Criar um commit

```bash
git commit -m "Descrição da alteração"
```

Exemplo:

```bash
git commit -m "Atualiza dashboard"
```

---

## 8. Enviar para o GitHub

```bash
git push
```

A versão hospedada no Vercel pode ser atualizada automaticamente a partir do repositório conectado ao projeto.

---

# Fluxo dos dados

A aplicação foi planejada para separar completamente:

1. **obtenção dos dados brutos**;
2. **limpeza e preparação**;
3. **dados leves utilizados pelo site**.

Isso permite atualizar a base epidemiológica sem alterar manualmente o código do dashboard.

O fluxo desejado é:

```text
SINAN / PySUS
      │
      ▼
atualizar_sinan.py
      │
      ▼
CSV bruto
      │
      ▼
preparar_dashboard.py
      │
      ├── limpeza
      ├── padronização
      ├── criação de variáveis
      ├── agregações
      └── compactação
      │
      ▼
public/data/*.json
      │
      ▼
Dashboard Astro
```

O navegador **não deve receber a base completa do SINAN**. Ele recebe apenas arquivos agregados e compactos necessários às visualizações.

Isso reduz o tamanho dos arquivos transferidos e melhora o desempenho do site.

---

# Atualização dos dados do SINAN

A atualização dos dados deve ser uma tarefa separada da execução normal do site.

O objetivo do script:

```text
scripts/atualizar_sinan.py
```

é:

1. consultar os dados de acidentes com animais peçonhentos no SINAN utilizando o PySUS;
2. obter os anos definidos para o projeto;
3. restringir os dados ao estado de São Paulo;
4. reunir os anos em uma única base;
5. salvar um CSV bruto.

Esse script **não deve realizar a limpeza analítica dos dados**.

A ideia é que, sempre que uma nova versão da base estiver disponível, seja necessário apenas executar novamente o processo de atualização.

---

## Instalar as dependências Python

Para trabalhar com os scripts de atualização e preparação dos dados, utilize Python 3.13.

Na raiz do projeto, crie e ative um ambiente virtual e instale as dependências:

```bash
py -3.13 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

---

## Executar a atualização do SINAN

Quando o script estiver finalizado:

```bash
python scripts/atualizar_sinan.py
```

O resultado será um arquivo bruto local.

Arquivos brutos grandes **não devem ser adicionados ao GitHub**.

A pasta ou os arquivos de dados brutos devem permanecer no `.gitignore`.

---

# Preparação dos dados do dashboard

O script:

```text
scripts/preparar_dashboard.py
```

é responsável pela transformação da base para o formato utilizado pela aplicação.

A versão atual do script realiza, entre outras etapas:

- leitura da base epidemiológica;
- leitura dos dados geográficos dos municípios;
- associação entre código e nome do município;
- recodificação do tipo de animal;
- criação das opções dos filtros;
- tratamento das variáveis utilizadas pelo dashboard;
- identificação de óbitos;
- obtenção do mês da notificação;
- agregações por ano, animal e município;
- compactação das informações;
- geração dos arquivos JSON.

Atualmente são gerados arquivos como:

```text
public/data/filtros.json
public/data/base.json
public/data/gravidade.json
public/data/trabalho.json
public/data/mes.json
public/data/tempo.json
```

Esses são os arquivos que devem ser utilizados pelo código do dashboard.

---

## Executar a preparação do dashboard

Depois de atualizar/substituir a base bruta:

```bash
python scripts/preparar_dashboard.py
```

Após a execução, os arquivos em:

```text
public/data/
```

serão atualizados.

Em seguida, execute:

```bash
npm run dev
```

e confira se o dashboard está funcionando corretamente com a nova base.

Antes de enviar ao GitHub:

```bash
npm run build
```

---

# Processo completo para atualizar os dados

De forma resumida:

```bash
git pull
```

Instalar as dependências Python, caso ainda não estejam instaladas:

```bash
python -m pip install -r requirements.txt
```

Baixar novamente os dados do SINAN:

```bash
python scripts/atualizar_sinan.py
```

Preparar os dados utilizados pelo dashboard:

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

Adicionar somente os arquivos necessários ao repositório:

```bash
git add .
```

Criar o commit:

```bash
git commit -m "Atualiza dados do dashboard"
```

Enviar:

```bash
git push
```

> Antes do commit, é importante confirmar que nenhum CSV bruto ou arquivo excessivamente grande foi incluído acidentalmente.

---

# Dados brutos e Git

Bases completas do SINAN podem ser grandes e não são necessárias para a execução pública da aplicação.

Por isso:

- arquivos CSV brutos não devem ser versionados;
- dados geográficos originais grandes também podem permanecer fora do Git;
- os arquivos compactos de `public/data/` podem ser versionados quando forem necessários para o funcionamento da versão pública do site.

Antes de qualquer commit, utilize:

```bash
git status
```

para verificar exatamente o que será enviado.

---

# Implantação no Vercel

O Vercel é utilizado para hospedar a aplicação Astro.

A implantação utiliza a aplicação web e suas dependências Node.js.

O pipeline Python **não precisa ser executado pelo Vercel**.

O fluxo é:

```text
scripts Python executados localmente
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

Assim, bibliotecas como pandas, GeoPandas e PySUS não precisam ser instaladas no ambiente de execução do site.

---

# Separação entre Dashboard e “Encontrar soro”

O **Dashboard** tem finalidade analítica e apresenta dados históricos e agregados sobre os acidentes e a rede de atendimento.

A página **Encontrar soro** tem finalidade operacional e será responsável por auxiliar na localização de unidades de atendimento soroterápico.

Informações de localização, disponibilidade de soros, distância e rota até uma unidade devem ser tratadas separadamente das análises epidemiológicas do dashboard.

---

# Fontes de dados

A principal fonte epidemiológica utilizada pelo projeto é o:

**Sistema de Informação de Agravos de Notificação (SINAN)**.

A atualização automatizada da base está sendo estruturada com a biblioteca **PySUS**.

Também são utilizados dados geográficos para a associação e representação dos municípios do estado de São Paulo.

---

# Créditos do desenvolvimento web

Este projeto foi construído com o framework open source **[Astro](https://astro.build/)**.

A estrutura inicial da interface foi baseada no template gratuito **[Astroship](https://github.com/surjithctly/astroship)**, desenvolvido por **Surjith S M** e disponibilizado pela **[Web3Templates](https://web3templates.com/)**.

O template original utiliza Astro e Tailwind CSS e foi adaptado para as necessidades específicas deste projeto acadêmico.

Os créditos aos projetos originais são mantidos em reconhecimento às ferramentas e recursos utilizados no desenvolvimento da plataforma.

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

O uso do ChatGPT não substitui as fontes científicas, bases de dados ou documentação oficial das tecnologias utilizadas.

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
- pipeline automatizado de atualização e preparação dos dados;
- visualizações temporais, clínicas e espaciais;
- análise de fluxos de pacientes;
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
- [Astroship](https://github.com/surjithctly/astroship)
- [Web3Templates](https://web3templates.com/)
- [Vercel](https://vercel.com/)
