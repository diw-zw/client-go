GO ?= go
PYTHON ?= python3
RBG_SOURCE ?= ../rbg
RBG_API_SOURCE ?= ../rbg-api
REF ?= v0.8.0
API_VERSION ?= $(REF)

.PHONY: help
help: ## Display this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

.PHONY: sync
sync: ## Sync generated client-go from RBG.
	$(PYTHON) script/sync_from_rbg.py \
		--source "$(RBG_SOURCE)" \
		--ref "$(REF)" \
		--api-version "$(API_VERSION)" \
		--api-source "$(RBG_API_SOURCE)"

.PHONY: fmt
fmt: ## Format generated Go files.
	gofmt -w applyconfiguration clientset informers listers

.PHONY: tidy
tidy: ## Run go mod tidy.
	KEEP_GO_MOD=1 script/with_api_replace.sh "$(RBG_API_SOURCE)" -- $(GO) mod tidy

.PHONY: build
build: ## Compile all packages.
	script/with_api_replace.sh "$(RBG_API_SOURCE)" -- $(GO) build ./...

.PHONY: test
test: ## Run unit tests.
	script/with_api_replace.sh "$(RBG_API_SOURCE)" -- $(GO) test ./... -count=1

.PHONY: vet
vet: ## Run go vet.
	script/with_api_replace.sh "$(RBG_API_SOURCE)" -- $(GO) vet ./...
