run:
	uv run python -m uvicorn app.main:app --reload

PORT ?= 8000

run_render:
	uv run python -m uvicorn app.main:app --host 0.0.0.0 --port $(PORT)