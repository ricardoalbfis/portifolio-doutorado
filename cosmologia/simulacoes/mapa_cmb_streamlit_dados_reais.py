"""
Simulador do mapa da radiacao cosmica de fundo (CMB) com dados REAIS.

Diferente das versoes anteriores (que usam so o espectro teorico do CAMB),
este app carrega o espectro de potencia TT medido de verdade pelo satelite
Planck (2018, dados publicos da ESA - ver dados/FONTE.md) e compara com a
curva teorica do CAMB para os parametros escolhidos nos sliders.

Mostra tres mapas lado a lado:
  1. o mapa real observado pela sonda WMAP (imagem estatica, dados reais);
  2. o mesmo mapa real, filtrado por harmonicos esfericos para mostrar so
     os multipolos (polos) selecionados na barra lateral;
  3. um mapa simulado (synfast) a partir da curva teorica do CAMB com os
     parametros atuais, para comparar teoria com observacao.

Rodar com:
    streamlit run mapa_cmb_streamlit_dados_reais.py
"""

import os

import camb
import healpy as hp
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

st.set_page_config(page_title="Mapa CMB - dados reais", layout="wide")
st.title("Simulador do mapa da CMB com dados reais (Planck)")

LMAX_CALC = 1000

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


def filtrar_mapa_real(l_selecionados):
    alm, l_por_alm, lmax_real, nside_real = calcular_alm_mapa_real()
    mascara = np.isin(l_por_alm, list(l_selecionados))
    alm_filtrado = np.where(mascara, alm, 0)
    return hp.alm2map(alm_filtrado, nside=nside_real), lmax_real


@st.cache_data(show_spinner="Calculando espectro teorico com CAMB...", max_entries=8)
def calcular_cl_teorico(h0, ombh2, omch2, ns, ln10_10_As, tau):
    As = np.exp(ln10_10_As) / 1.0e10
    pars = camb.CAMBparams()
    pars.set_cosmology(H0=h0, ombh2=ombh2, omch2=omch2, tau=tau)
    pars.InitPower.set_params(As=As, ns=ns)
    pars.set_for_lmax(LMAX_CALC, lens_potential_accuracy=0)
    results = camb.get_results(pars)
    powers = results.get_cmb_power_spectra(pars, CMB_unit="muK", raw_cl=True)
    return powers["total"][:, 0]  # TT, indexado por l = 0..LMAX_CALC


l_obs, dl_obs, erro_menos, erro_mais = carregar_dados_reais()
LMAX_OBS = int(l_obs.max())

with st.sidebar:
    st.header("Parametros cosmologicos (curva teorica)")
    h0 = st.slider("$H_0$ (km/s/Mpc)", 50.0, 90.0, PARAMS_REFERENCIA["h0"])
    ombh2 = st.slider(
        "$\\Omega_b h^2$", 0.005, 0.05, PARAMS_REFERENCIA["ombh2"], format="%.4f"
    )
    omch2 = st.slider(
        "$\\Omega_c h^2$", 0.05, 0.30, PARAMS_REFERENCIA["omch2"], format="%.3f"
    )
    ns = st.slider("$n_s$ (indice espectral)", 0.85, 1.10, PARAMS_REFERENCIA["ns"])
    ln10_10_As = st.slider(
        "$\\ln(10^{10} A_s)$ (amplitude escalar)",
        2.5,
        3.7,
        PARAMS_REFERENCIA["ln10_10_As"],
        format="%.3f",
    )
    tau = st.slider("$\\tau$ (reionizacao)", 0.01, 0.15, PARAMS_REFERENCIA["tau"])

    st.header("Mapa simulado (item 3)")
    nside = st.selectbox("NSIDE", [32, 64, 128, 256], index=1)
    seed = st.number_input("Seed (aleatorio)", value=42, step=1)

    st.header("Polos (multipolos $\\ell$) a destacar")
    modo = st.radio("Modo de selecao", ["Intervalo continuo", "Valores especificos"])

    lmax_sel = min(LMAX_CALC, LMAX_OBS)
    if modo == "Intervalo continuo":
        lmin, lmax = st.slider(
            "Faixa de $\\ell$ incluida no mapa", 2, lmax_sel, (2, 200)
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
        except ValueError:
            st.error("Digite apenas numeros inteiros separados por virgula.")
            l_selecionados = set()


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
        label="Polos observados selecionados",
        zorder=3,
    )
    ax.set_xlabel("l")
    ax.set_ylabel("D_l  [µK²]")
    ax.set_xlim(0, lmax_sel)
    ax.legend(fontsize=8)
    st.pyplot(fig_cl)

with col2:
    st.subheader("1. Mapa real observado (WMAP 9 anos, ILC)")
    mapa_real = carregar_mapa_real()
    plt.close("all")
    hp.mollview(mapa_real, title="", unit="µK", cmap="RdBu_r")
    st.pyplot(plt.gcf())
    st.caption(
        "Imagem estatica: flutuacoes de temperatura da CMB realmente "
        "observadas pela sonda WMAP (9 anos, metodo ILC), nao muda com os "
        "controles ao lado. A faixa horizontal ao centro e residuo da "
        "limpeza de emissao da nossa propria galaxia, nao e sinal da CMB."
    )

    st.subheader("2. Mapa real, so com os polos selecionados")
    _, _, lmax_real, nside_real = calcular_alm_mapa_real()
    l_sel_real = {l for l in l_selecionados if l <= lmax_real}
    if l_sel_real:
        mapa_real_filtrado, _ = filtrar_mapa_real(l_sel_real)
        plt.close("all")
        hp.mollview(mapa_real_filtrado, title="", unit="µK", cmap="RdBu_r")
        st.pyplot(plt.gcf())
        if any(l > lmax_real for l in l_selecionados):
            st.caption(
                f"O mapa real tem resolucao NSIDE={nside_real}, entao so "
                f"consegue mostrar ate l={lmax_real}; polos selecionados "
                f"acima disso foram ignorados aqui (mas aparecem no grafico "
                f"e no mapa simulado abaixo)."
            )
    else:
        st.warning(f"Nenhum polo selecionado esta dentro do alcance do mapa real (l ≤ {lmax_real}).")

    st.subheader("3. Mapa simulado (CAMB, parametros atuais)")
    if l_selecionados:
        np.random.seed(int(seed))
        mapa_sim = hp.synfast(cl_teorico_filtrado, nside=nside, new=True, verbose=False)
        plt.close("all")
        hp.mollview(mapa_sim, title="", unit="µK", cmap="RdBu_r")
        st.pyplot(plt.gcf())
        st.caption(
            "Realizacao aleatoria gerada a partir da curva teorica do CAMB "
            "com os parametros escolhidos nos sliders. Mude os parametros "
            "ou o seed para ver como o mapa simulado se compara aos mapas "
            "reais acima."
        )
    else:
        st.warning("Selecione ao menos um polo para gerar o mapa.")

st.caption(
    "Pontos cinzas com barra de erro = espectro TT realmente medido pelo "
    "Planck (2018, dados publicos da ESA). Curva azul = previsao teorica do "
    "CAMB para os parametros escolhidos ao lado."
)
