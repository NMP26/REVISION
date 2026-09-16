SHELL := /bin/bash
.DEFAULT_GOAL := help

PROJECT := revision-prix
COMPOSE := docker compose -p $(PROJECT) --env-file .env -f compose.yaml
VERSION := $(shell tr -d '[:space:]' < VERSION)

.PHONY: help build build-images up down restart status logs test lint check migrations migrate backup restore doctor \
        push-images release deploy rollback

help:
	@echo "RevisionPrix $(VERSION)"
	@echo "make build build-images up down restart status logs test lint check migrations migrate backup restore doctor"
	@echo "make push-images release deploy rollback (non opérationnels sans configuration de registry/release)"

build build-images:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) restart

status:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs --tail=200

test:
	$(COMPOSE) exec -T revision-prix-backend python manage.py test
	@python3 -c "import json,urllib.request; d=json.load(urllib.request.urlopen('http://127.0.0.1:12701/api/health/', timeout=5)); assert d['status']=='ok',d; assert d['database']['status']=='ok',d; assert d['migrations']['status']=='ok',d; print('Frontend/API smoke test: OK')"

lint:
	$(COMPOSE) exec -T revision-prix-backend python -m compileall -q .
	$(COMPOSE) exec -T revision-prix-backend python manage.py check --deploy

check: lint test

migrations:
	$(COMPOSE) exec -T revision-prix-backend python manage.py makemigrations --check --dry-run

migrate:
	$(COMPOSE) exec -T revision-prix-backend python manage.py migrate --noinput

backup:
	./scripts/backup.sh

restore:
	@if [ -z "$(BACKUP)" ]; then echo 'ERROR: make restore BACKUP=backups/<timestamp>'; exit 2; fi
	./scripts/restore.sh "$(BACKUP)"

doctor:
	./scripts/healthcheck.sh

push-images:
	@echo 'ERROR: push-images est désactivé : aucun registry autorisé/configuré pour le LOT 0.' >&2; exit 2

release:
	@echo 'ERROR: release est désactivé : le manifest de release et le registry seront activés après validation LOT 0.' >&2; exit 2

deploy:
	@echo 'ERROR: deploy est désactivé : le déploiement production appartient à une phase ultérieure.' >&2; exit 2

rollback:
	@echo 'ERROR: rollback est désactivé : aucune release de production n'existe dans le LOT 0.' >&2; exit 2
