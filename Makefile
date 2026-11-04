GO ?= go
PYTHON ?= python3
RBG_SOURCE ?= ../rbg
VERSION ?= v0.8.0

.PHONY: help
help: ## Display this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

.PHONY: sync
sync: ## Sync generated client-go from RBG.
	$(PYTHON) script/sync_from_rbg.py \
		--source "$(RBG_SOURCE)" \
		--ref "$(VERSION)"

.PHONY: fmt
fmt: ## Format generated Go files.
	gofmt -w applyconfiguration clientset informers listers

.PHONY: tidy
tidy: ## Run go mod tidy.
	$(GO) mod tidy

.PHONY: build
build: ## Compile all packages.
	$(GO) build ./...

.PHONY: test
test: ## Run unit tests.
	$(GO) test ./... -count=1

.PHONY: vet
vet: ## Run go vet.
	$(GO) vet ./...
