# client-go sync script

`sync_from_rbg.py` extracts the generated `client-go` tree from an rbg Git
revision and writes it at the repository root:

- `applyconfiguration/`
- `clientset/`
- `informers/`
- `listers/`

The script does **not** copy `api/workloads`. This module intentionally
depends on `sigs.k8s.io/rbgs/api` from the separate rbg-api repository, which
keeps the API module free of client-go dependencies.

## Sync a release

From the repository root:

```bash
python3 script/sync_from_rbg.py \
  --source ../rbg \
  --ref v0.8.0 \
  --api-version v0.8.0 \
  --api-source ../rbg-api
```

`--api-source` is optional. When supplied, the script temporarily replaces
`sigs.k8s.io/rbgs/api` with that local checkout while running `go mod tidy`,
then removes the temporary replace directive. The generated files and final
`go.mod` remain release-ready.

Consumers must still add the documented `replace` for
`sigs.k8s.io/rbgs/api` in their own main module; `replace` directives in a
dependency's `go.mod` are ignored when that dependency is consumed.

`make tidy` uses the same local-replacement strategy. `make build`, `make
test`, and `make vet` use a stricter variant that restores `go.mod` exactly
after the command finishes.

For a branch or commit, explicitly provide the rbg-api version that should be
required:

```bash
python3 script/sync_from_rbg.py \
  --source ../rbg \
  --ref main \
  --api-version v0.9.0-alpha.1
```

## Verify a sync

```bash
make test
make vet
git diff --check
git status --short
```

Inspect the diff before committing. The four generated directories should
contain only files copied from rbg; API types, controllers, webhooks, and
validation logic should not appear in this repository.
