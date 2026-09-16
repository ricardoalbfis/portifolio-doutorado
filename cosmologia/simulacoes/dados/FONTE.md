# Fonte dos dados

`planck2018_TT_full_R3.01.txt` — espectro de potencia angular da temperatura
da CMB (TT), Planck 2018, produto `COM_PowerSpect_CMB-TT-full_R3.01`.

Baixado em 2026-09-16 de:
https://pla.esac.esa.int/pla/aio/product-action?COSMOLOGY.FILE_ID=COM_PowerSpect_CMB-TT-full_R3.01.txt

Planck Legacy Archive (ESA). Colunas: l, D_l [uK^2], -dD_l, +dD_l (erro
assimetrico observacional, l = 2 a 2508).

---

`wmap9_ilc_nside256_uK.fits` — mapa real do ceu inteiro da CMB, WMAP 9 anos,
metodo ILC (Internal Linear Combination), unidades em microK.

Baixado em 2026-09-16 de:
https://lambda.gsfc.nasa.gov/data/map/dr5/dfp/ilc/wmap_ilc_9yr_v5.fits

NASA LAMBDA (WMAP Science Team). Arquivo original em nside=512 e mK;
convertido para uK e reamostrado para nside=256 (hp.ud_grade), que permite
mostrar multipolos reais ate l=767 (3*nside-1) e ainda fica leve o
suficiente para o repositorio (~3 MB em vez de ~24 MB do original em
nside=512). O mapa do Planck em resolucao completa (nside=2048) chega a
varias centenas de MB e nao foi usado por esse motivo; o WMAP ILC e um
mapa real e publico, so que de resolucao/sensibilidade menor que o Planck.
