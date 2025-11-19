  .PHONY: dev test build run install

  venv := .venv

  install:
	python -m venv $(venv); . $(venv)/bin/activate && pip install -r requirements.txt

  dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  test:
	pytest -q

  build:
	docker buildx build --platform linux/amd64 -t mich43l/opensips-api:0.4 .

  run:
	docker compose -f docker-compose.dev.yml up --build
