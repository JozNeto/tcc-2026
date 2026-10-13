from __future__ import annotations

import pandas as pd

from src.models.baseline import NaiveModel
from src.models.cenarios import HORIZONTE_PRINCIPAL_MESES, projetar_cenarios


def _modelo_ajustado() -> NaiveModel:
    datas = pd.date_range("2020-01-01", periods=30, freq="MS").date
    serie = pd.Series(range(30), index=datas, dtype=float)
    return NaiveModel().fit(serie)


def test_projetar_cenarios_produz_os_tres_cenarios():
    resultado = projetar_cenarios(_modelo_ajustado(), horizonte=24)
    assert set(resultado["cenario"]) == {"inercial", "contencao", "expansao"}
    assert len(resultado) == 24 * 3


def test_cenario_inercial_e_condicional_a_regulacao_estavel():
    resultado = projetar_cenarios(_modelo_ajustado(), horizonte=6)
    inercial = resultado[resultado["cenario"] == "inercial"]
    outros = resultado[resultado["cenario"] != "inercial"]

    assert inercial["condicional_a_regulacao_estavel"].all()
    assert not outros["condicional_a_regulacao_estavel"].any()


def test_contencao_e_menor_e_expansao_e_maior_que_inercial():
    resultado = projetar_cenarios(_modelo_ajustado(), horizonte=6)
    pivotado = resultado.pivot(index="passo", columns="cenario", values="previsao")

    assert (pivotado["contencao"] < pivotado["inercial"]).all()
    assert (pivotado["expansao"] > pivotado["inercial"]).all()


def test_horizonte_dentro_do_principal_e_rotulado_previsao():
    resultado = projetar_cenarios(_modelo_ajustado(), horizonte=HORIZONTE_PRINCIPAL_MESES)
    assert (resultado["tipo"] == "previsao").all()


def test_horizonte_alem_do_principal_e_rotulado_exercicio_de_cenario():
    resultado = projetar_cenarios(_modelo_ajustado(), horizonte=HORIZONTE_PRINCIPAL_MESES + 12)

    dentro = resultado[resultado["passo"] <= HORIZONTE_PRINCIPAL_MESES]
    alem = resultado[resultado["passo"] > HORIZONTE_PRINCIPAL_MESES]

    assert (dentro["tipo"] == "previsao").all()
    assert (alem["tipo"] == "exercicio_de_cenario").all()
