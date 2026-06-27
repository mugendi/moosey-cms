# ============================================================================
# Makefile - Production Deployment for Moosey CMS Advanced Example
# ============================================================================
# Usage:
#   make build-css     Build Tailwind CSS for production
#   make pm2-start     Build assets, then start PM2 with MODE=production
#   make pm2-stop      Stop the PM2 process
#   make pm2-restart   Restart with fresh build
#   make dev           Run in development mode with hot-reload
# ============================================================================

# -- Environment -------------------------------------------------------------
MODE ?= production
VENV ?= .venv
PYTHON ?= $(VENV)/bin/python

# -- Tailwind CSS ------------------------------------------------------------
# Build from the example's static source to the output directory.
# Adjust source/input paths to match your project structure.
TAILWIND_INPUT ?= ../static/css/input.css
TAILWIND_OUTPUT ?= ../static/css/style.css

.PHONY: build-css
build-css:
	npm run build:css -- \
		--input $(TAILWIND_INPUT) \
		--output $(TAILWIND_OUTPUT) \
		--minify

# -- PM2 Process Manager ----------------------------------------------------
APP_MODULE ?= example.advanced.main:app

.PHONY: pm2-start
pm2-start: build-css
	MODE=$(MODE) pm2 start $(PYTHON) \
		--name moosey-advanced \
		--interpreter $(PYTHON) \
		-- \
		-m uvicorn $(APP_MODULE) \
		--host 0.0.0.0 \
		--port 8000

.PHONY: pm2-stop
pm2-stop:
	pm2 stop moosey-advanced

.PHONY: pm2-restart
pm2-restart: build-css
	MODE=$(MODE) pm2 restart moosey-advanced

# -- Development -------------------------------------------------------------
.PHONY: dev
dev:
	MODE=development $(PYTHON) -m uvicorn $(APP_MODULE) \
		--host 0.0.0.0 \
		--port 8000 \
		--reload

# -- Cleanup -----------------------------------------------------------------
.PHONY: clean
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
