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
export VERSION=v0.8.0
export RBG_SOURCE=../rbg

python3 script/sync_from_rbg.py \
  --source "$RBG_SOURCE" \
  --ref "$VERSION"
```

The script automatically updates `go.mod` to require the matching
`sigs.k8s.io/rbgs/api` version and to replace it with the published
`github.com/sgl-project/rbg-api` repository.

`replace` directives in this repository's `go.mod` only affect this repository's
own builds and tests. Consumers must still add the documented `replace` in
their own main module.

Only semantic version tags are accepted. rbg, rbg-api, and client-go are
assumed to share the same version.

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
