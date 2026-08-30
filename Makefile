.PHONY: lint

lint:
	@if [ ! -d "src" ]; then \
		echo "Error: `src` directory not found. Please ensure you are in the project root directory."; \
		exit 1; \
	fi
	uv run ruff format src
	uv run ruff check src
