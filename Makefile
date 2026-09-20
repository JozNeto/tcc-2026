.PHONY: setup test test-network test-data-quality lint dashboard mcp clean

setup:
	python -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt

# Testes locais: unitários, data quality, harness de modelos e integração sem rede
# (ex.: smoke test do dashboard). Nenhum teste marcado @pytest.mark.network roda aqui.
test:
	pytest tests/unit tests/data_quality tests/model_eval_harness tests/integration -m "not network"

# Testes de integração contra as fontes reais (rede necessária).
test-network:
	pytest tests/integration -m network

test-data-quality:
	pytest tests/data_quality

lint:
	ruff check src tests .mcp

dashboard:
	streamlit run src/dashboard/app.py

mcp:
	python .mcp/server.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
