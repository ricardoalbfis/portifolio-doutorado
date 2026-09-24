"""
Healpy na pratica - mapa real da CMB e corte galactico (versao Streamlit).

Versao interativa do notebook cosmologia/notebooks/healpy_mapa_real_planck.ipynb:
carrega um mapa real da CMB (WMAP 9 anos, ILC, ja usado nos outros apps deste
repositorio), mostra o mapa cheio, deixa escolher a latitude galactica de
corte |b| e mostra o mapa com a mascara aplicada (hp.UNSEEN) e a fracao do
ceu (f_sky) resultante.

Rodar com:
    streamlit run mapa_cmb_streamlit_corte_galatico.py
"""

import io
import os

import healpy as hp
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

st.set_page_config(page_title="Mapa CMB - corte galactico", layout="wide")
st.title("Healpy na pratica: mapa real da CMB e corte galactico")
st.markdown(
    "A faixa central da Via Lactea (o \"plano galactico\") emite muita radiacao "
    "que contamina o sinal da CMB. Antes de analisar o mapa, os cosmologos "
    "recortam essa faixa. Aqui voce ve isso acontecer com um mapa **real** da "
    "CMB (WMAP), ajustando a latitude galactica de corte."
)

MAPA_PATH = os.path.join(
    os.path.dirname(__file__), "dados", "wmap9_ilc_nside256_uK.fits"
)


@st.cache_data(show_spinner="Carregando mapa real da CMB (WMAP)...")
def carregar_mapa():
    mapa = hp.read_map(MAPA_PATH)
    nside = hp.get_nside(mapa)
    npix = hp.nside2npix(nside)
    theta, _ = hp.pix2ang(nside, np.arange(npix))
    b = 90.0 - np.degrees(theta)
    return mapa, nside, npix, b


@st.cache_data(show_spinner=False, max_entries=20)
def renderizar_mollview_png(mapa, vmin, vmax, titulo):
    plt.close("all")
    hp.mollview(
        mapa, coord="G", min=vmin, max=vmax, cmap="coolwarm",
        title=titulo, unit="µK_CMB", xsize=400,
    )
    fig = plt.gcf()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close("all")
    buf.seek(0)
    return buf.getvalue()


@st.cache_data(show_spinner=False, max_entries=20)
def renderizar_gnomview_png(mapa, l, b_centro, vmin, vmax, titulo):
    plt.close("all")
    hp.gnomview(
        mapa, rot=[l, b_centro], xsize=300, reso=6, min=vmin, max=vmax,
        cmap="coolwarm", title=titulo, unit="µK_CMB",
    )
    fig = plt.gcf()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close("all")
    buf.seek(0)
    return buf.getvalue()


mapa, nside, npix, b_lat = carregar_mapa()

with st.sidebar:
    st.header("Corte galactico")
    st.caption(
        "A mascara aqui e didatica e nao substitui as mascaras cientificas "
        "completas do Planck."
    )
    corte = st.slider(
        "Latitude galactica de corte |b| (graus)", 0, 45, 20,
        help="Pixels com |latitude galactica| menor que isso sao excluidos (regiao do plano da Via Lactea).",
    )

    st.header("Zoom (gnomview)")
    l_zoom = st.slider("Longitude galactica l (graus)", 0, 360, 0)
    b_zoom = st.slider("Latitude galactica b (graus)", -90, 90, 0)

    st.caption(f"Mapa: CMB real (WMAP 9 anos, ILC), NSIDE={nside} ({npix:,} pixels).")

mask_excluir = np.abs(b_lat) < corte
f_sky = (~mask_excluir).sum() / npix

mapa_mask = mapa.copy()
mapa_mask[mask_excluir] = hp.UNSEEN

mapa_binario = (~mask_excluir).astype(int)  # 1 = mantido, 0 = excluido

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Mapa completo (sem corte)")
    st.image(
        renderizar_mollview_png(mapa, -300, 300, ""),
        use_container_width=True,
    )
    st.caption(
        "Mapa real da CMB (WMAP). A faixa horizontal brilhante e a emissao "
        "termica/sincrotron da nossa propria galaxia, nao e sinal da CMB."
    )

    st.subheader("2. Mapa com corte galactico aplicado")
    st.image(
        renderizar_mollview_png(mapa_mask, -300, 300, ""),
        use_container_width=True,
    )
    st.caption(
        "Pixels dentro do corte foram marcados com hp.UNSEEN (cinza) - o array "
        "continua do mesmo tamanho, so os valores mudam (nada e apagado)."
    )

with col2:
    st.subheader("3. Mascara binaria (1=mantido, 0=excluido)")
    st.image(
        renderizar_mollview_png(mapa_binario, 0, 1, ""),
        use_container_width=True,
    )
    st.caption("Visualizacao separada da mascara, sem misturar com o mapa fisico de temperatura.")

    st.subheader("4. Zoom (hp.gnomview)")
    st.image(
        renderizar_gnomview_png(mapa, l_zoom, b_zoom, -300, 300, ""),
        use_container_width=True,
    )
    st.caption(f"Regiao centrada em l={l_zoom}°, b={b_zoom}° (coordenadas galacticas).")

st.subheader("5. Fracao do ceu (f_sky)")
st.latex(r"f_{sky} = \frac{N_{pixels\ mantidos}}{N_{pixels\ totais}}")
col3, col4 = st.columns([1, 2])
with col3:
    st.metric(f"f_sky para |b| < {corte}°", f"{f_sky:.2f}")
with col4:
    linhas = []
    for c in (10, 20, 30):
        m = np.abs(b_lat) < c
        linhas.append((c, (~m).sum() / npix))
    st.table(
        {
            "Corte": [f"{c}°" for c, _ in linhas],
            "Regra": [f"|b| < {c}°" for c, _ in linhas],
            "f_sky (aprox.)": [f"{fs:.2f}" for _, fs in linhas],
        }
    )

st.info(
    "Nao usamos `anafast` aqui. Uma mascara modifica a relacao entre os "
    "multipolos - o espectro de potencia de um ceu incompleto precisa de "
    "tratamento proprio (deconvolucao da mascara) para nao introduzir "
    "vazamento espectral entre multipolos."
)

st.caption(
    "Dados reais: WMAP 9 anos, metodo ILC (NASA LAMBDA). Veja o notebook "
    "cosmologia/notebooks/healpy_mapa_real_planck.ipynb para o mesmo fluxo "
    "com instrucoes para usar o mapa original do Planck (143 GHz, NSIDE=2048)."
)
