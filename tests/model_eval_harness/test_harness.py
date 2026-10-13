import pytest

from tests.model_eval_harness.harness import (
    RegressaoDeMetricaError,
    registrar_e_comparar,
    ultimo_registro,
)

KWARGS_BASE = {
    "modelo": "sarimax_exogena",
    "serie": "comprometimento_renda_pf",
    "metrica": "mase",
    "versao_base_usada": "base_nacional_corte-2025-12-31_run-teste",
    "seed": 42,
}


def test_primeira_execucao_grava_baseline_sem_comparar(tmp_path):
    historico = tmp_path / "historico_metricas.jsonl"
    registrar_e_comparar(valor=0.80, caminho_historico=historico, **KWARGS_BASE)

    registro = ultimo_registro(historico, KWARGS_BASE["modelo"], KWARGS_BASE["serie"], KWARGS_BASE["metrica"])
    assert registro is not None
    assert registro.valor == 0.80


def test_melhora_de_metrica_nao_levanta_erro(tmp_path):
    historico = tmp_path / "historico_metricas.jsonl"
    registrar_e_comparar(valor=0.80, caminho_historico=historico, **KWARGS_BASE)
    registrar_e_comparar(valor=0.70, caminho_historico=historico, **KWARGS_BASE)  # melhora


def test_piora_pequena_dentro_do_limiar_nao_levanta_erro(tmp_path):
    historico = tmp_path / "historico_metricas.jsonl"
    registrar_e_comparar(valor=0.80, caminho_historico=historico, **KWARGS_BASE)
    registrar_e_comparar(valor=0.81, caminho_historico=historico, **KWARGS_BASE)  # +1.25%, limiar padrão é 5%


def test_piora_alem_do_limiar_levanta_regressao(tmp_path):
    historico = tmp_path / "historico_metricas.jsonl"
    registrar_e_comparar(valor=0.80, caminho_historico=historico, **KWARGS_BASE)
    with pytest.raises(RegressaoDeMetricaError, match="piorou"):
        registrar_e_comparar(valor=1.00, caminho_historico=historico, **KWARGS_BASE)  # +25%


def test_regressao_nao_grava_novo_registro(tmp_path):
    historico = tmp_path / "historico_metricas.jsonl"
    registrar_e_comparar(valor=0.80, caminho_historico=historico, **KWARGS_BASE)
    with pytest.raises(RegressaoDeMetricaError):
        registrar_e_comparar(valor=1.00, caminho_historico=historico, **KWARGS_BASE)

    registro = ultimo_registro(historico, KWARGS_BASE["modelo"], KWARGS_BASE["serie"], KWARGS_BASE["metrica"])
    assert registro.valor == 0.80  # o registro ruim não deve ter sido persistido


def test_metrica_maior_e_melhor_inverte_direcao_da_piora(tmp_path):
    historico = tmp_path / "historico_metricas.jsonl"
    kwargs = {**KWARGS_BASE, "metrica": "acuracia", "metrica_menor_e_melhor": False}
    registrar_e_comparar(valor=0.80, caminho_historico=historico, **kwargs)
    with pytest.raises(RegressaoDeMetricaError):
        registrar_e_comparar(valor=0.50, caminho_historico=historico, **kwargs)  # queda de acurácia = piora


def test_historico_inexistente_retorna_none(tmp_path):
    historico = tmp_path / "nao_existe.jsonl"
    assert ultimo_registro(historico, "x", "y", "z") is None
