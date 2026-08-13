.PHONY: config up down logs migrate discover plan demo full landing dbt-build ml-demo scheduled-demo test

config:
	docker compose config --quiet

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

migrate:
	docker compose run --rm pipeline migrate

discover:
	docker compose run --rm pipeline discover --mode full --start-date $(START_DATE) --end-date $(END_DATE)

plan:
	docker compose run --rm pipeline plan --mode full --start-date $(START_DATE) --end-date $(END_DATE)

demo:
	docker compose run --rm pipeline run --mode demo

full:
	docker compose run --rm pipeline run --mode full --start-date $(START_DATE) --end-date $(END_DATE)

landing:
	docker compose run --rm pipeline load-landing --source-kind demo

dbt-build:
	docker compose --profile tools run --rm dbt build

ml-demo:
	docker compose run --rm pipeline train-ml --mode demo

scheduled-demo:
	docker compose run --rm --entrypoint /app/scripts/run_scheduled_demo.sh scheduler

test:
	docker compose run --rm --no-deps --entrypoint python pipeline -m unittest discover -s /app/tests -v
