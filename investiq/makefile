
help: ## Show help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n",$$1,$$2}'

setup: ## Setup the project
	poetry install 
	poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000

up: ## Run the project
	docker compose up --build

restart_backend: ## Restart the backend 
	docker-compose restart backend

down: ## Down the project 
	docker compose down -v

down_clean: ## Down the project and remove the volumes
	docker-compose down --volumes --remove-orphans


clean_build: ## Clean the build cache
	docker builder prune


poetry_clear: ## Clear the poetry cache
	rm poetry.lock
	poetry cache clear . --all
	poetry install 


library:
	pip install exa-py openai python-dotenv

tree: ## Show the tree of the project
	tree -I node_modules


--------------------------------

status_ollama:
	curl -X GET "http://localhost:8000/api/ollama-status"
status_