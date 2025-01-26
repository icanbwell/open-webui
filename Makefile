
ifneq ($(shell which docker-compose 2>/dev/null),)
    DOCKER_COMPOSE := docker-compose
else
    DOCKER_COMPOSE := docker compose
endif

install:
	$(DOCKER_COMPOSE) up -d

remove:
	@chmod +x confirm_remove.sh
	@./confirm_remove.sh

start:
	$(DOCKER_COMPOSE) start
startAndBuild:
	$(DOCKER_COMPOSE) up -d --build

stop:
	$(DOCKER_COMPOSE) stop

update:
	# Calls the LLM update script
	chmod +x update_ollama_models.sh
	@./update_ollama_models.sh
	@git pull
	$(DOCKER_COMPOSE) down
	# Make sure the ollama-webui container is stopped before rebuilding
	@docker stop open-webui || true
	$(DOCKER_COMPOSE) up --build -d
	$(DOCKER_COMPOSE) start

build:
	@docker build . -t openwebui-local:latest

.PHONY: run-pre-commit
run-pre-commit:
	docker run -it --rm \
		-v $(PWD):/app \
		-w /app/backend \
		python:3.11-slim \
		bash -c "pip install black && black . --exclude \".venv/|/venv/\""

# Update uv.lock file using Docker
update-uv-lock:
	@echo "Updating uv.lock file using Docker..."
	docker build \
		--target base \
		-t open-webui-lock-builder \
		.
	docker run --rm \
		-v $(PWD)/backend:/app/backend \
		-v $(PWD)/uv.lock:/app/backend/uv.lock \
		-w /app/backend \
		open-webui-lock-builder \
		bash -c "uv pip install --system -r requirements.txt && uv lock > ./uv.lock"
	@echo "uv.lock file updated successfully."

# Optional: Clean up the temporary image
clean-lock-builder:
	docker rmi open-webui-lock-builder || true
