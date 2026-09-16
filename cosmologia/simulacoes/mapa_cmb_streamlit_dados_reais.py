"""
Simulador didatico do mapa da radiacao cosmica de fundo (CMB) com dados
REAIS.

Carrega o espectro de potencia TT medido de verdade pelo satelite Planck
(2018, dados publicos da ESA - ver dados/FONTE.md) e compara com a curva
teorica do CAMB para os parametros escolhidos nos sliders. Mostra tres
mapas lado a lado:
  1. o mapa real observado pela sonda WMAP (imagem estatica, dados reais);
  2. o mesmo mapa real, filtrado por harmonicos esfericos para mostrar so
     os multipolos (polos) selecionados na barra lateral;
  3. um mapa simulado (synfast) a partir da curva teorica do CAMB com os
     parametros atuais, para comparar teoria com observacao.

Os mapas renderizados ficam em cache: cada imagem so e redesenhada quando
os dados que a formam realmente mudam, entao alternar entre valores ja
vistos e instantaneo.

Rodar com:
    streamlit run mapa_cmb_streamlit_dados_reais.py
"""

import io
import os

import camb
import healpy as hp
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

st.set_page_config(page_title="Mapa CMB - dados reais", layout="wide")
st.title("Simulador do mapa da CMB com dados reais (Planck / WMAP)")
st.markdown(
    "A radiacao cosmica de fundo (CMB) e a luz mais antiga do universo, "
    "emitida cerca de 380 mil anos apos o Big Bang. Suas pequenas variacoes "
    "de temperatura (da ordem de microkelvins) sao decompostas em "
    "**multipolos** $\\ell$, um pouco como uma musica e decomposta em notas: "
    "$\\ell$ baixo = estruturas grandes no ceu, $\\ell$ alto = detalhes "
    "finos. Este simulador deixa voce escolher quais multipolos (\"polos\") "
    "olhar, e compara mapas e espectros **reais** (medidos por satelites) "
    "com a previsao **teorica** do CAMB."
)

LMAX_CALC = 1000
LMAX_SELECAO = 300  # limite pratico dos controles, para manter o app rapido

PARAMS_REFERENCIA = dict(
    h0=67.4, ombh2=0.0224, omch2=0.120, ns=0.965, ln10_10_As=3.045, tau=0.054
)

DADOS_PATH = os.path.join(
    os.path.dirname(__file__), "dados", "planck2018_TT_full_R3.01.txt"
)
MAPA_REAL_PATH = os.path.join(
    os.path.dirname(__file__), "dados", "wmap9_ilc_nside256_uK.fits"
)


@st.cache_data(show_spinner="Carregando espectro observado pelo Planck...")
def carregar_dados_reais():
    dados = np.loadtxt(DADOS_PATH)
    l_obs = dados[:, 0].astype(int)
    dl_obs = dados[:, 1]
    erro_menos = dados[:, 2]
    erro_mais = dados[:, 3]
    return l_obs, dl_obs, erro_menos, erro_mais


@st.cache_data(show_spinner="Carregando mapa real observado (WMAP)...")
def carregar_mapa_real():
    return hp.read_map(MAPA_REAL_PATH)


@st.cache_data(show_spinner="Decompondo o mapa real em harmonicos esfericos...")
def calcular_alm_mapa_real():
    mapa_real = carregar_mapa_real()
    nside_real = hp.get_nside(mapa_real)
    lmax_real = 3 * nside_real - 1
    alm = hp.map2alm(mapa_real, lmax=lmax_real)
    l_por_alm, _ = hp.Alm.getlm(lmax_real)
    return alm, l_por_alm, lmax_real, nside_real


@st.cache_data(show_spinner=False, max_entries=20)
def filtrar_mapa_real(l_selecionados_tupla):
    alm, l_por_alm, lmax_real, nside_real = calcular_alm_mapa_real()
    mascara = np.isin(l_por_alm, l_selecionados_tupla)
    alm_filtrado = np.where(mascara, alm, 0)
    return hp.alm2map(alm_filtrado, nside=nside_real)


@st.cache_data(show_spinner="Calculando espectro teorico com CAMB...", max_entries=10)
def calcular_cl_teorico(h0, ombh2, omch2, ns, ln10_10_As, tau):
    As = np.exp(ln10_10_As) / 1.0e10
    pars = camb.CAMBparams()
    pars.set_cosmology(H0=h0, ombh2=ombh2, omch2=omch2, tau=tau)
    pars.InitPower.set_params(As=As, ns=ns)
    pars.set_for_lmax(LMAX_CALC, lens_potential_accuracy=0)
    results = camb.get_results(pars)
    powers = results.get_cmb_power_spectra(pars, CMB_unit="muK", raw_cl=True)
    return powers["total"][:, 0]  # TT, indexado por l = 0..LMAX_CALC


@st.cache_data(show_spinner=False, max_entries=20)
def renderizar_mapa_png(mapa):
    """Desenha um mapa HEALPix e devolve os bytes do PNG. Em cache: o mesmo
    mapa nunca e redesenhado duas vezes."""
    plt.close("all")
    hp.mollview(mapa, title="", unit="µK", cmap="RdBu_r", xsize=400)
    fig = plt.gcf()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close("all")
    buf.seek(0)
    return buf.getvalue()


l_obs, dl_obs, erro_menos, erro_mais = carregar_dados_reais()
LMAX_OBS = int(l_obs.max())

with st.sidebar:
    st.header("1. Parametros cosmologicos")
    st.caption("Controlam a curva teorica do CAMB (mapa 3 e a linha azul do grafico).")
    h0 = st.slider(
        "$H_0$ — Constante de Hubble (km/s/Mpc)",
        50.0, 90.0, PARAMS_REFERENCIA["h0"],
        help="Taxa de expansao atual do universo.",
    )
    ombh2 = st.slider(
        "$\\Omega_b h^2$ — densidade de barions",
        0.005, 0.05, PARAMS_REFERENCIA["ombh2"], format="%.4f",
        help="Quantidade de materia comum (protons e neutrons) no universo.",
    )
    omch2 = st.slider(
        "$\\Omega_c h^2$ — densidade de materia escura",
        0.05, 0.30, PARAMS_REFERENCIA["omch2"], format="%.3f",
        help="Quantidade de materia escura fria, que nao interage com a luz.",
    )
    ns = st.slider(
        "$n_s$ — indice espectral escalar",
        0.85, 1.10, PARAMS_REFERENCIA["ns"],
        help="Inclinacao do espectro de perturbacoes primordiais (1 = invariante de escala).",
    )
    ln10_10_As = st.slider(
        "$\\ln(10^{10} A_s)$ — amplitude das perturbacoes",
        2.5, 3.7, PARAMS_REFERENCIA["ln10_10_As"], format="%.3f",
        help="Intensidade das flutuacoes de densidade primordiais que deram origem a tudo.",
    )
    tau = st.slider(
        "$\\tau$ — profundidade optica de reionizacao",
        0.01, 0.15, PARAMS_REFERENCIA["tau"],
        help="Quanto a luz da CMB foi espalhada pelas primeiras estrelas/galaxias.",
    )

    st.header("2. Mapa simulado (item 3)")
    nside = st.selectbox(
        "NSIDE (resolucao do mapa)", [32, 64, 128], index=1,
        help="Quanto maior, mais pixels e mais detalhe - mas mais lento.",
    )
    seed = st.number_input("Seed (aleatorio)", value=42, step=1)

    st.header("3. Polos (multipolos $\\ell$) a destacar")
    st.caption(
        f"Limitado a l ≤ {LMAX_SELECAO} para o app continuar rapido. "
        "l baixo = estruturas grandes; l alto = detalhes finos."
    )
    modo = st.radio("Modo de selecao", ["Intervalo continuo", "Valores especificos"])

    if modo == "Intervalo continuo":
        lmin, lmax = st.slider(
            "Faixa de $\\ell$ incluida no mapa", 2, LMAX_SELECAO, (2, 60)
        )
        l_selecionados = set(range(lmin, lmax + 1))
    else:
        texto = st.text_input(
            "Lista de $\\ell$ separados por virgula (ex: 2,3,5,10,50)", "2,3,4,5"
        )
        try:
            l_selecionados = {
                int(x.strip()) for x in texto.split(",") if x.strip() != ""
            }
            l_selecionados = {l for l in l_selecionados if l <= LMAX_SELECAO}
        except ValueError:
            st.error("Digite apenas numeros inteiros separados por virgula.")
            l_selecionados = set()

    if l_selecionados:
        l_min_sel, l_max_sel = min(l_selecionados), max(l_selecionados)
        theta_max = 180.0 / max(l_min_sel, 1)
        theta_min = 180.0 / l_max_sel
        st.metric("Escala angular no ceu", f"{theta_min:.2f}° a {theta_max:.2f}°")
        st.caption(
            f"Formula aproximada: θ ≈ 180°/ℓ. l={l_min_sel} corresponde a "
            f"estruturas de ~{theta_max:.1f}°; l={l_max_sel} corresponde a "
            f"~{theta_min:.1f}° (quanto maior l, menor o detalhe no ceu)."
        )


try:
    cl_teorico = calcular_cl_teorico(h0, ombh2, omch2, ns, ln10_10_As, tau)
except Exception as exc:
    st.error(
        "Essa combinacao de parametros nao pode ser calculada pelo CAMB "
        f"({type(exc).__name__}). Ajuste os valores e tente novamente."
    )
    st.stop()

# Espectro teorico (CAMB, parametros dos sliders) filtrado pelos mesmos polos.
cl_teorico_filtrado = np.zeros_like(cl_teorico)
for l in l_selecionados:
    if 0 <= l < len(cl_teorico):
        cl_teorico_filtrado[l] = cl_teorico[l]

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Espectro de potencia: dados reais x teoria")
    st.markdown(
        "Cada ponto cinza e uma medida real do Planck; a curva azul e a "
        "previsao teorica do CAMB para os parametros escolhidos ao lado. "
        "Os pontos vermelhos sao os polos que voce selecionou."
    )
    st.latex(r"D_\ell = \frac{\ell(\ell+1)C_\ell}{2\pi}")

    ell_teo = np.arange(len(cl_teorico))
    dl_teo = ell_teo * (ell_teo + 1) * cl_teorico / (2 * np.pi)

    fig_cl, ax = plt.subplots()
    ax.errorbar(
        l_obs,
        dl_obs,
        yerr=[erro_menos, erro_mais],
        fmt=".",
        color="darkgray",
        ecolor="lightgray",
        markersize=2,
        elinewidth=0.5,
        alpha=0.6,
        label="Planck 2018 (observado)",
    )
    ax.plot(
        ell_teo[2:],
        dl_teo[2:],
        color="steelblue",
        label="CAMB (parametros atuais)",
    )
    l_dest = sorted(l for l in l_selecionados if l <= LMAX_OBS)
    ax.scatter(
        l_dest,
        dl_obs[np.searchsorted(l_obs, l_dest)],
        color="crimson",
        s=15,
        label="Polos selecionados",
        zorder=3,
    )
    ax.set_xlabel("l (multipolo)")
    ax.set_ylabel("D_l  [µK²]")
    ax.set_xlim(0, max(LMAX_SELECAO, 300))
    ax.legend(fontsize=8)
    st.pyplot(fig_cl)

with col2:
    st.subheader("1. Mapa real observado (WMAP 9 anos, ILC)")
    st.caption(
        "Imagem estatica: flutuacoes de temperatura da CMB realmente "
        "observadas pela sonda WMAP, nao muda com os controles ao lado. A "
        "faixa horizontal ao centro e residuo da limpeza de emissao da "
        "nossa propria galaxia, nao e sinal da CMB."
    )
    mapa_real = carregar_mapa_real()
    st.image(renderizar_mapa_png(mapa_real), use_container_width=True)

    st.subheader("2. Mapa real, so com os polos selecionados")
    _, _, lmax_real, nside_real = calcular_alm_mapa_real()
    l_sel_real = tuple(sorted(l for l in l_selecionados if l <= lmax_real))
    if l_sel_real:
        mapa_real_filtrado = filtrar_mapa_real(l_sel_real)
        st.image(renderizar_mapa_png(mapa_real_filtrado), use_container_width=True)
        st.caption(
            "O mapa real filtrado: mesma informacao do mapa 1, mas mantendo "
            "so os multipolos selecionados (compare com o espectro acima)."
        )
    else:
        st.warning(f"Nenhum polo selecionado esta dentro do alcance do mapa real (l ≤ {lmax_real}).")

    st.subheader("3. Mapa simulado (CAMB, parametros atuais)")
    if l_selecionados:
        np.random.seed(int(seed))
        mapa_sim = hp.synfast(cl_teorico_filtrado, nside=nside, new=True, verbose=False)
        st.image(renderizar_mapa_png(mapa_sim), use_container_width=True)
        st.caption(
            "Realizacao aleatoria gerada a partir da curva teorica do CAMB "
            "com os parametros escolhidos nos sliders. Mude os parametros "
            "ou o seed para ver como o mapa simulado se compara aos mapas "
            "reais acima."
        )
    else:
        st.warning("Selecione ao menos um polo para gerar o mapa.")
