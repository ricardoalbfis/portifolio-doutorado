"""
Simulador interativo de mapas da radiacao cosmica de fundo (CMB) - versao
comparativa.

Igual ao mapa_cmb_streamlit.py, mas o grafico do espectro de potencia mostra
tres curvas ao mesmo tempo:
  - o espectro de referencia, fixo, com os parametros padrao (Planck-like);
  - o espectro completo recalculado para os parametros atuais dos sliders;
  - os multipolos (polos) escolhidos, em destaque.

Rodar com:
    streamlit run mapa_cmb_streamlit_comparativo.py
"""

import io

import camb
import healpy as hp
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

st.set_page_config(page_title="Mapa CMB - comparativo", layout="wide")
st.title("Simulador de mapas da radiacao cosmica de fundo (comparativo)")

LMAX_CALC = 2500

PARAMS_REFERENCIA = dict(
    h0=67.4, ombh2=0.0224, omch2=0.120, ns=0.965, ln10_10_As=3.045, tau=0.054
)


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


with st.sidebar:
    st.header("Parametros cosmologicos")
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

    if l_selecionados:
        l_min_sel, l_max_sel = min(l_selecionados), max(l_selecionados)
        theta_max = 180.0 / max(l_min_sel, 1)
        theta_min = 180.0 / l_max_sel
        st.metric("Escala angular no ceu", f"{theta_min:.2f}° a {theta_max:.2f}°")
        st.caption(
            f"Formula aproximada: θ ≈ 180°/ℓ. l={l_min_sel} corresponde a "
            f"estruturas de ~{theta_max:.1f}°; l={l_max_sel} corresponde a "
            f"~{theta_min:.2f}° (quanto maior l, menor o detalhe no ceu)."
        )


try:
    # Espectro de referencia: sempre os parametros padrao, nunca muda com os sliders.
    cl_referencia = calcular_cl(**PARAMS_REFERENCIA)

    # Espectro completo recalculado para os parametros atuais escolhidos pelo usuario.
    cl_total = calcular_cl(h0, ombh2, omch2, ns, ln10_10_As, tau)
except Exception as exc:
    st.error(
        "Essa combinacao de parametros nao pode ser calculada pelo CAMB "
        f"({type(exc).__name__}). Ajuste os valores e tente novamente."
    )
    st.stop()

try:
    cl_filtrado = np.zeros_like(cl_total)
    for l in l_selecionados:
        if 0 <= l < len(cl_total):
            cl_filtrado[l] = cl_total[l]

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Espectro de potencia")
        st.latex(r"D_\ell = \frac{\ell(\ell+1)C_\ell}{2\pi}")

        ell = np.arange(len(cl_total))
        dl_referencia = ell * (ell + 1) * cl_referencia / (2 * np.pi)
        dl_total = ell * (ell + 1) * cl_total / (2 * np.pi)
        dl_filtrado = ell * (ell + 1) * cl_filtrado / (2 * np.pi)

        # Com selecoes muito grandes (milhares de polos), mostrar cada ponto
        # deixa o grafico pesado sem ganhar clareza - amostra para exibir.
        marcadores = sorted(l_selecionados)
        if len(marcadores) > 150:
            passo = len(marcadores) // 150 + 1
            marcadores = marcadores[::passo]

        fig_cl, ax = plt.subplots()
        ax.plot(
            ell[2:],
            dl_referencia[2:],
            label="Espectro de referencia (parametros padrao)",
            color="lightgray",
            linestyle="--",
        )
        ax.plot(
            ell[2:],
            dl_total[2:],
            label="Espectro completo (parametros atuais)",
            color="steelblue",
        )
        ax.scatter(
            marcadores,
            [dl_filtrado[l] for l in marcadores if l < len(dl_filtrado)],
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
            st.image(renderizar_mapa_png(mapa), use_container_width=True)
            lmax_nside = 3 * nside - 1
            if max(l_selecionados) > lmax_nside:
                st.info(
                    f"NSIDE={nside} só resolve até l={lmax_nside}; os polos "
                    f"selecionados acima disso não aparecem no mapa (mas "
                    f"aparecem no gráfico). Aumente o NSIDE para ve-los no mapa."
                )
        else:
            st.warning("Selecione ao menos um polo para gerar o mapa.")
except Exception as exc:
    st.error(
        "Nao foi possivel gerar o grafico/mapa para essa selecao "
        f"({type(exc).__name__}). Tente reduzir a faixa de polos ou o NSIDE."
    )
    st.stop()

st.caption(
    "Polos = multipolos $\\ell$ do espectro de potencia angular. "
    "$\\ell=2$ e o quadrupolo, $\\ell=3$ o octopolo, valores altos de "
    "$\\ell$ correspondem a estruturas em escala angular menor no mapa. "
    "A curva cinza tracejada e fixa (parametros padrao) e serve de referencia "
    "para comparar com o espectro atual, em azul."
)
