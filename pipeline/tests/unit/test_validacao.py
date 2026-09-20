from __future__ import annotations

import pandas as pd
import pytest

from src.models.baseline import NaiveModel
from src.models.validacao import validar_rolling_origin


def _serie(n: int) -> pd.Series:
    datas = pd.date_range("2020-01-01", periods=n, freq="MS").date
    return pd.Series(range(n), index=datas, dtype=float)


def test_validar_rolling_origin_gera_uma_previsao_por_origem():
    serie = _serie(20)
    resultado = validar_rolling_origin(serie, NaiveModel, tamanho_minimo_treino=15, horizonte=1, passo=1)

    # origens possíveis: 15, 16, 17, 18, 19 (origem + horizonte <= 20) => 5 origens
    assert resultado["origem"].nunique() == 5
    assert len(resultado) == 5


def test_validar_rolling_origin_nunca_usa_dados_futuros_no_treino():
    """NaiveModel prevê o último valor de treino — se o rolling origin vazasse dados
    futuros, a previsão em cada origem coincidiria com o valor real (a série é
    estritamente crescente, então vazamento seria detectável)."""
    serie = _serie(20)
    resultado = validar_rolling_origin(serie, NaiveModel, tamanho_minimo_treino=15, horizonte=1, passo=1)

    # NaiveModel prevê o valor da origem anterior (origem-1), nunca o valor_real da origem
    for _, linha in resultado.iterrows():
        assert linha["previsao"] != linha["valor_real"]
        assert linha["previsao"] == linha["valor_real"] - 1


def test_validar_rolling_origin_respeita_passo_maior_que_1():
    serie = _serie(20)
    resultado = validar_rolling_origin(serie, NaiveModel, tamanho_minimo_treino=15, horizonte=1, passo=2)
    assert resultado["origem"].nunique() == 3  # origens 15, 17, 19


def test_validar_rolling_origin_horizonte_maior_que_1_multiplica_linhas_por_origem():
    serie = _serie(20)
    resultado = validar_rolling_origin(serie, NaiveModel, tamanho_minimo_treino=15, horizonte=3, passo=1)
    assert (resultado.groupby("origem").size() == 3).all()


def test_validar_rolling_origin_levanta_erro_se_serie_curta_demais():
    serie = _serie(5)
    with pytest.raises(ValueError):
        validar_rolling_origin(serie, NaiveModel, tamanho_minimo_treino=10, horizonte=1)


def test_validar_rolling_origin_aceita_exogena_alinhada():
    serie = _serie(20)
    exogena = _serie(20) * 2

    class ModeloComExogena(NaiveModel):
        def fit(self, serie_treino, exogena_treino=None):
            assert exogena_treino is not None
            assert len(exogena_treino) == len(serie_treino)
            return super().fit(serie_treino)

    resultado = validar_rolling_origin(
        serie, ModeloComExogena, tamanho_minimo_treino=15, horizonte=1, exogena=exogena
    )
    assert len(resultado) == 5
