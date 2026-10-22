.PHONY: build clean

build:
	@echo "🚀 Сборка..."
	uv run pyinstaller --noconfirm lit.spec
	@echo "🧹 Чистим промежуточные файлы..."
	rm -rf build/
	@echo "✅ Готово: dist/lit"

clean:
	@echo "🧹 Удаляем build/ и dist/..."
	rm -rf build/ dist/
	@echo "✅ Готово."
