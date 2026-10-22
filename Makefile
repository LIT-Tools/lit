.PHONY: build clean help

help: ## Список команд
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

build: ## Собрать бинарный файл
	@echo "🚀 Сборка..."
	uv run pyinstaller --noconfirm lit.spec
	@echo "🧹 Чистим промежуточные файлы..."
	rm -rf build/
	@echo "✅ Готово: dist/lit"

clean: ## Удалить build/ и dist/
	@echo "🧹 Удаляем build/ и dist/..."
	rm -rf build/ dist/
	@echo "✅ Готово."
