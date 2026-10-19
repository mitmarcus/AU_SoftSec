build:
	docker compose build

up:
	docker compose up -d --wait

seed:
	docker compose exec -T records python - < seed/seed.py

test:
	python3 -m pytest payrates/tests
	docker compose run --rm --build tests

down:
	docker compose down -v

# needed because of conflicting targets with files of the same name
.PHONY: build up seed test down