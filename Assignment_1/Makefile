build:
	docker compose build

up:
	docker compose up -d

seed:
	docker compose exec -T records python - < seed/seed.py

test:
	python3 -m pytest payrates/tests
	python3 -m pytest tests

down:
	docker compose down -v
