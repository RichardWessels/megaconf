.PHONY: lint

lint:
	@if [ ! -d "src" ]; then \
		echo "Error: `src` directory not found. Please ensure you are in the project root directory."; \
		exit 1; \
	fi
	ruff format src
	ruff check src
