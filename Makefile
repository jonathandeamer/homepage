# Jonathan Deamer homepage - common tasks

.DEFAULT_GOAL := help
.PHONY: help dev build test check clean

help:  ## list available targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-14s %s\n", $$1, $$2}'

dev:  ## hugo dev server
	hugo server --port 1313 --bind 127.0.0.1

build:  ## clean production build
	hugo --cleanDestinationDir --minify --gc --printPathWarnings

test:  ## run unit tests for local scripts
	python3 -m unittest discover -s tests -p 'test_*.py'

check: build test  ## build then sanity-check rendered output
	@echo
	@echo "-> rendered site contract:"
	@python3 scripts/check_rendered_site.py public
	@echo
	@if command -v htmltest >/dev/null 2>&1; then \
		echo "-> htmltest (internal link check):"; \
		htmltest -s public; \
	else \
		echo "-> htmltest not installed (skipping link check)"; \
		echo "    install with: brew install htmltest"; \
	fi
	@echo
	@if command -v pa11y >/dev/null 2>&1; then \
		echo "-> pa11y (accessibility audit on homepage):"; \
		pa11y "file://$(PWD)/public/index.html"; \
		echo; \
		echo "-> pa11y (accessibility audit on 404):"; \
		pa11y "file://$(PWD)/public/404.html"; \
	else \
		echo "-> pa11y not installed (skipping accessibility check)"; \
		echo "    install with: npm install -g pa11y"; \
	fi
	@echo
	@if command -v vnu >/dev/null 2>&1; then \
		echo "-> vnu HTML validation:"; \
		vnu --skip-non-html "public/index.html" "public/404.html"; \
	elif [ -f "$$HOME/.vnu/vnu.jar" ] && java -version >/dev/null 2>&1; then \
		echo "-> vnu HTML validation:"; \
		java -jar "$$HOME/.vnu/vnu.jar" --skip-non-html "public/index.html" "public/404.html"; \
	else \
		echo "-> vnu HTML validator not installed (skipping)"; \
		echo "    install: mkdir -p ~/.vnu && curl -sL https://github.com/validator/validator/releases/latest/download/vnu.jar -o ~/.vnu/vnu.jar"; \
	fi
	@echo
	@echo "-> sitemap:"
	@test -s public/sitemap.xml
	@xmllint --noout public/sitemap.xml
	@echo "    ok"
	@echo

clean:  ## remove generated output
	rm -rf public resources/_gen .hugo_build.lock .hugo-deploy.generated.toml
