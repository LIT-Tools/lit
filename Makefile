.PHONY: build clean help test

help: ## Список команд
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

test: ## Тесты, покрытие, CRAP и HTML-отчёт
	@set -e; \
	trap 'rm -f coverage.json cc.json .coverage' EXIT; \
	uv run coverage run --branch -m unittest discover; \
	uv run coverage report -m; \
	uv run coverage json -o coverage.json; \
	uv run radon cc . -j -O cc.json; \
	uv run python calc_crap.py; \
	uv run coverage html; \
	echo "✅ HTML-отчёт: htmlcov/index.html"

build: ## Собрать бинарный файл
	@echo "🚀 Сборка..."
	uv run pyinstaller --noconfirm lit.spec
	@echo "🧹 Чистим промежуточные файлы..."
	rm -rf build/
	@echo "✅ Готово: dist/lit"

clean: ## Удалить сгенерированные файлы
	@echo "🧹 Чистим временные файлы..."
	rm -rf build/ dist/ htmlcov/ .coverage coverage.json cc.json .DS_Store
	find . -path ./.venv -prune -o -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Готово."
