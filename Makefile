.PHONY: setup test integration smoke lint format pre-commit-install pre-commit run doctor

setup:
	uv sync --extra dev --python 3.12

test:
	uv run pytest -q -m "not integration and not smoke"

integration:
	uv run pytest -q -m integration

smoke:
	@set -a; [ ! -f .env ] || . ./.env; set +a; uv run pytest -q -m smoke

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff format .
	uv run ruff check --fix .

pre-commit-install:
	uv run pre-commit install

pre-commit:
	uv run pre-commit run --all-files

run:
	@set -a; [ ! -f .env ] || . ./.env; set +a; uv run claude-esg-mcp

doctor:
	@uv --version
	@uv run python --version
	@uv run python -c "import chromadb, mcp, openai, pydantic; print('chromadb', chromadb.__version__); print('mcp', getattr(mcp, '__version__', 'unknown')); print('openai', openai.__version__); print('pydantic', pydantic.__version__)"
	@set -a; [ ! -f .env ] || . ./.env; set +a; uv run python -c "import os; print('OPENAI_API_KEY', 'set' if os.getenv('OPENAI_API_KEY') else 'missing'); print('CLAUDE_ESG_INDEX_PATH', os.getenv('CLAUDE_ESG_INDEX_PATH') or 'missing')"
