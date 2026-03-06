# Planejador de Viagem Personalizado

Aplicacao que gera roteiros de viagem completos dia a dia usando **3 agentes de IA** do CrewAI, com interface profissional em Streamlit.

## O que faz

O usuario preenche um formulario com destino, datas, orcamento, estilo de viagem e numero de viajantes. Tres agentes trabalham em sequencia:

1. **Pesquisador de Destinos** — pesquisa clima, transporte, vistos, seguranca, bairros e eventos no periodo (usa busca web via SerperDev)
2. **Curador de Experiencias** — seleciona hoteis, restaurantes e atracoes respeitando orcamento e estilo, agrupando por proximidade geografica
3. **Redator de Roteiros** — escreve o roteiro final formatado dia a dia com horarios, dicas e estimativa de gastos

O progresso e exibido em tempo real usando o sistema de eventos do CrewAI.

## Como instalar

```bash
# Clone o repositorio
git clone https://github.com/danielfsbarreto/crew-action-2026-03.git
cd crew-action-2026-03/planejador-viagem

# Crie e ative o ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Instale as dependencias
pip install -e .
```

## Como configurar

Copie o arquivo de exemplo e preencha com suas chaves:

```bash
cp .env.example .env
```

Edite o `.env`:

```bash
OPENAI_API_KEY=sua-chave-da-openai
SERPER_API_KEY=sua-chave-do-serper
```

- **OPENAI_API_KEY**: obtenha em [platform.openai.com](https://platform.openai.com/)
- **SERPER_API_KEY**: obtenha em [serper.dev](https://serper.dev/) (plano gratuito disponivel)

## Como executar

```bash
streamlit run app.py --server.port 8501
```

Acesse no navegador: `http://localhost:8501`

## Exemplo de uso

1. Abra a aplicacao no navegador
2. Na barra lateral, preencha:
   - **Destino**: Tokyo, Japao
   - **Datas**: ida e volta desejadas
   - **Orcamento**: R$ 15.000
   - **Estilo**: Gastronomia
   - **Viajantes**: 2
3. Clique em "Planejar Minha Viagem"
4. Acompanhe o progresso dos agentes em tempo real
5. Receba o roteiro completo e faca download em Markdown

## Estrutura do projeto

```
planejador-viagem/
├── app.py                    # Interface Streamlit
├── crew.py                   # Definicao dos agentes, tasks e crew
├── config/
│   ├── agents.yaml           # Configuracao dos agentes
│   └── tasks.yaml            # Configuracao das tasks
├── listeners/
│   ├── __init__.py
│   └── progress_listener.py  # Event listener para progresso em tempo real
├── .env.example              # Variaveis de ambiente (exemplo)
├── .gitignore
├── pyproject.toml
└── README.md
```

## Tecnologias

- [CrewAI](https://crewai.com/) — framework de agentes de IA
- [Streamlit](https://streamlit.io/) — interface web
- [SerperDev](https://serper.dev/) — busca web para os agentes
