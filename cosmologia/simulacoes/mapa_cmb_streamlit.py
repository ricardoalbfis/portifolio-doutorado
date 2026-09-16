"""
Simulador interativo de mapas da radiacao cosmica de fundo (CMB).

Calcula o espectro de potencia com CAMB, permite escolher quais multipolos
(polos) l entram na reconstrucao do mapa, e gera o mapa com healpy.synfast.

Rodar com:
    streamlit run mapa_cmb_streamlit.py
"""

import camb
import healpy as hp
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

st.set_page_config(page_title="Mapa CMB", layout="wide")
st.title("Simulador de mapas da radiacao cosmica de fundo")

LMAX_CALC = 1000


@st.cache_data(show_spinner="Calculando espectro de potencia com CAMB...", max_entries=8)
def calcular_cl(h0, ombh2, omch2, ns, ln10_10_As, tau):
    As = np.exp(ln10_10_As) / 1.0e10
    pars = camb.CAMBparams()
    pars.set_cosmology(H0=h0, ombh2=ombh2, omch2=omch2, tau=tau)
    pars.InitPower.set_params(As=As, ns=ns)
    pars.set_for_lmax(LMAX_CALC, lens_potential_accuracy=0)
    results = camb.get_results(pars)
    powers = results.get_cmb_power_spectra(pars, CMB_unit="muK", raw_cl=True)
    return powers["total"][:, 0]  # TT, indexado por l = 0..LMAX_CALC


with st.sidebar:
    st.header("Parametros cosmologicos")
    h0 = st.slider("$H_0$ (km/s/Mpc)", 50.0, 90.0, 67.4)
    ombh2 = st.slider("$\\Omega_b h^2$", 0.005, 0.05, 0.0224, format="%.4f")
    omch2 = st.slider("$\\Omega_c h^2$", 0.05, 0.30, 0.120, format="%.3f")
    ns = st.slider("$n_s$ (indice espectral)", 0.85, 1.10, 0.965)
    ln10_10_As = st.slider(
        "$\\ln(10^{10} A_s)$ (amplitude escalar)", 2.5, 3.7, 3.045, format="%.3f"
    )
    tau = st.slider("$\\tau$ (reionizacao)", 0.01, 0.15, 0.054)

    st.header("Mapa")
    nside = st.selectbox("NSIDE", [32, 64, 128, 256], index=1)
    seed = st.number_input("Seed (aleatorio)", value=42, step=1)

    st.header("Polos (multipolos $\\ell$) a incluir")
    modo = st.radio("Modo de selecao", ["Intervalo continuo", "Valores especificos"])

    if modo == "Intervalo continuo":
        lmin, lmax = st.slider(
            "Faixa de $\\ell$ incluida no mapa", 2, LMAX_CALC, (2, 200)
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
    cl_total = calcular_cl(h0, ombh2, omch2, ns, ln10_10_As, tau)
except Exception as exc:
    st.error(
        "Essa combinacao de parametros nao pode ser calculada pelo CAMB "
        f"({type(exc).__name__}). Ajuste os valores e tente novamente."
    )
    st.stop()

cl_filtrado = np.zeros_like(cl_total)
for l in l_selecionados:
    if 0 <= l < len(cl_total):
        cl_filtrado[l] = cl_total[l]

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Espectro de potencia")
    st.latex(r"D_\ell = \frac{\ell(\ell+1)C_\ell}{2\pi}")
    ell = np.arange(len(cl_total))
    dl_total = ell * (ell + 1) * cl_total / (2 * np.pi)
    dl_filtrado = ell * (ell + 1) * cl_filtrado / (2 * np.pi)

    fig_cl, ax = plt.subplots()
    ax.plot(ell[2:], dl_total[2:], label="Espectro completo", color="lightgray")
    ax.scatter(
        sorted(l_selecionados),
        [dl_filtrado[l] for l in sorted(l_selecionados) if l < len(dl_filtrado)],
        color="crimson",
        s=15,
        label="Polos selecionados",
        zorder=3,
    )
    ax.set_xlabel("l")
    ax.set_ylabel("D_l  [µK²]")
    ax.legend()
    st.pyplot(fig_cl)

with col2:
    st.subheader(f"Mapa simulado ({len(l_selecionados)} polo(s) ativo(s))")
    if l_selecionados:
        np.random.seed(int(seed))
        mapa = hp.synfast(cl_filtrado, nside=nside, new=True, verbose=False)

        plt.close("all")
        hp.mollview(
            mapa,
            title="",
            unit="µK",
            cmap="RdBu_r",
        )
        st.pyplot(plt.gcf())
    else:
        st.warning("Selecione ao menos um polo para gerar o mapa.")

st.caption(
    "Polos = multipolos $\\ell$ do espectro de potencia angular. "
    "$\\ell=2$ e o quadrupolo, $\\ell=3$ o octopolo, valores altos de "
    "$\\ell$ correspondem a estruturas em escala angular menor no mapa."
)
