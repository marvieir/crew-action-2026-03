"""Planejador de Viagem Personalizado — Interface Streamlit."""

from __future__ import annotations

import threading
import time
from datetime import date, timedelta

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Importar listener ANTES do crew para registrar no event bus
from listeners.progress_listener import progress_state  # noqa: E402
from crew import build_crew  # noqa: E402

# ---------------------------------------------------------------------------
# Configuracao da pagina
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Planejador de Viagem",
    page_icon="\u2708\ufe0f",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS customizado
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Header */
    .main-header {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        color: white;
    }
    .main-header h1 {
        color: white;
        font-size: 2.2rem;
        margin-bottom: 0.3rem;
    }
    .main-header p {
        color: #b0c4de;
        font-size: 1.1rem;
        margin: 0;
    }

    /* Cards de info */
    .info-card {
        background: #f8f9fa;
        border-left: 4px solid #2c5364;
        padding: 1rem 1.2rem;
        border-radius: 8px;
        margin-bottom: 0.8rem;
    }
    .info-card strong {
        color: #203a43;
    }

    /* Progress steps */
    .step-running {
        color: #0d6efd;
        font-weight: 600;
    }
    .step-done {
        color: #198754;
    }
    .step-error {
        color: #dc3545;
        font-weight: 600;
    }

    /* Resultado */
    .result-container {
        background: #ffffff;
        border: 1px solid #dee2e6;
        border-radius: 12px;
        padding: 2rem;
        margin-top: 1rem;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }

    /* Botao primario */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        border: none;
        font-size: 1.1rem;
        padding: 0.7rem 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="main-header">
        <h1>\u2708\ufe0f Planejador de Viagem Personalizado</h1>
        <p>Seu roteiro completo dia a dia, criado por agentes de IA especializados</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "result" not in st.session_state:
    st.session_state.result = None
if "running" not in st.session_state:
    st.session_state.running = False
if "error" not in st.session_state:
    st.session_state.error = None

# ---------------------------------------------------------------------------
# Sidebar — Formulario
# ---------------------------------------------------------------------------
ESTILOS = {
    "Aventura": "aventura (trilhas, esportes, natureza)",
    "Cultura": "cultura (museus, historia, arquitetura)",
    "Gastronomia": "gastronomia (restaurantes, mercados, aulas de culinaria)",
    "Relaxamento": "relaxamento (praias, spas, ritmo tranquilo)",
}

with st.sidebar:
    st.markdown("### \U0001f4cb Dados da Viagem")

    with st.form("viagem_form"):
        destino = st.text_input(
            "Destino",
            placeholder="Ex: Tokyo, Japao",
            help="Cidade e pais de destino",
        )

        col_ida, col_volta = st.columns(2)
        with col_ida:
            data_ida = st.date_input(
                "Ida",
                value=date.today() + timedelta(days=30),
                min_value=date.today(),
            )
        with col_volta:
            data_volta = st.date_input(
                "Volta",
                value=date.today() + timedelta(days=37),
                min_value=date.today() + timedelta(days=1),
            )

        orcamento = st.number_input(
            "Orcamento total (R$)",
            min_value=500,
            max_value=500_000,
            value=10_000,
            step=500,
            help="Orcamento total para todos os viajantes",
        )

        estilo_label = st.selectbox(
            "Estilo de viagem",
            options=list(ESTILOS.keys()),
        )

        num_viajantes = st.slider(
            "Numero de viajantes",
            min_value=1,
            max_value=10,
            value=2,
        )

        submitted = st.form_submit_button(
            "\U0001f680 Planejar Minha Viagem",
            use_container_width=True,
            type="primary",
        )

    # Info de ajuda
    st.markdown("---")
    st.markdown(
        """
        <div style="font-size: 0.85rem; color: #6c757d;">
            <strong>Como funciona:</strong><br>
            3 agentes de IA trabalham em sequencia:<br>
            1. Pesquisador investiga o destino<br>
            2. Curador seleciona experiencias<br>
            3. Redator escreve o roteiro final
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Validacao e execucao
# ---------------------------------------------------------------------------


def _run_crew(inputs: dict) -> None:
    """Executa o crew em uma thread separada."""
    try:
        crew = build_crew()
        result = crew.kickoff(inputs=inputs)
        st.session_state.result = result.raw
        st.session_state.error = None
    except Exception as exc:
        st.session_state.error = str(exc)
        st.session_state.result = None
    finally:
        st.session_state.running = False


if submitted:
    # Validacoes
    errors = []
    if not destino or not destino.strip():
        errors.append("Informe o destino da viagem.")
    if data_volta <= data_ida:
        errors.append("A data de volta deve ser posterior a data de ida.")

    if errors:
        for e in errors:
            st.error(e)
    else:
        num_dias = (data_volta - data_ida).days
        orcamento_por_pessoa = round(orcamento / num_viajantes, 2)
        estilo = ESTILOS[estilo_label]

        inputs = {
            "destino": destino.strip(),
            "data_ida": data_ida.strftime("%d/%m/%Y"),
            "data_volta": data_volta.strftime("%d/%m/%Y"),
            "num_dias": str(num_dias),
            "orcamento": str(orcamento),
            "orcamento_por_pessoa": str(orcamento_por_pessoa),
            "estilo": estilo,
            "num_viajantes": str(num_viajantes),
        }

        st.session_state.result = None
        st.session_state.error = None
        st.session_state.running = True
        progress_state.reset()

        thread = threading.Thread(target=_run_crew, args=(inputs,), daemon=True)
        thread.start()

# ---------------------------------------------------------------------------
# Area principal — progresso e resultado
# ---------------------------------------------------------------------------
if st.session_state.running:
    st.markdown("### \u23f3 Planejando sua viagem...")

    # Info cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            '<div class="info-card"><strong>\U0001f50d Pesquisador</strong><br>'
            "Investigando o destino</div>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            '<div class="info-card"><strong>\u2728 Curador</strong><br>'
            "Selecionando experiencias</div>",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            '<div class="info-card"><strong>\u270d\ufe0f Redator</strong><br>'
            "Escrevendo o roteiro</div>",
            unsafe_allow_html=True,
        )

    # Progress steps
    progress_placeholder = st.empty()
    status_icon = {"running": "\u23f3", "done": "\u2705", "error": "\u274c"}
    status_class = {"running": "step-running", "done": "step-done", "error": "step-error"}

    while st.session_state.running:
        steps_html = ""
        for step in progress_state.steps:
            icon = status_icon.get(step.status, "\u23f3")
            cls = status_class.get(step.status, "step-running")
            steps_html += f'<div class="{cls}">{icon} {step.message}</div>'

        if steps_html:
            progress_placeholder.markdown(steps_html, unsafe_allow_html=True)

        time.sleep(1)

    # Atualizar uma ultima vez apos o termino
    st.rerun()

elif st.session_state.error:
    st.error(f"Ocorreu um erro durante o planejamento: {st.session_state.error}")
    if st.button("Tentar novamente"):
        st.session_state.error = None
        st.rerun()

elif st.session_state.result:
    st.markdown("### \u2705 Seu Roteiro de Viagem")

    # Botao para download
    st.download_button(
        label="\U0001f4e5 Baixar roteiro (.md)",
        data=st.session_state.result,
        file_name="roteiro_viagem.md",
        mime="text/markdown",
    )

    st.markdown("---")
    st.markdown(
        f'<div class="result-container">{""}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(st.session_state.result)

    if st.button("\U0001f504 Planejar outra viagem"):
        st.session_state.result = None
        st.rerun()

else:
    # Estado inicial — tela de boas-vindas
    st.markdown("### Bem-vindo ao Planejador de Viagem!")
    st.markdown(
        "Preencha os dados da viagem na barra lateral e clique em "
        '**"Planejar Minha Viagem"** para comecar.'
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
            #### \U0001f50d Pesquisa Inteligente
            Um agente especializado pesquisa tudo sobre seu destino:
            clima, transporte, seguranca e eventos.
            """
        )
    with col2:
        st.markdown(
            """
            #### \u2728 Curadoria Personalizada
            Seleciona hoteis, restaurantes e experiencias
            alinhados ao seu estilo e orcamento.
            """
        )
    with col3:
        st.markdown(
            """
            #### \U0001f4dd Roteiro Completo
            Receba um roteiro dia a dia com horarios,
            dicas praticas e estimativa de gastos.
            """
        )
