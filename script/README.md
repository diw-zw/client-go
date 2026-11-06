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
git switch "release/$VERSION"

python3 script/sync_from_rbg.py \
  --source "$RBG_SOURCE" \
  --go go
```

On a `release/<version>` branch, the version is derived from the branch name.
If `--ref` is also supplied, it must match the branch version. On any other
branch, or on a detached HEAD, `--ref` must be supplied explicitly.

Before writing any files, the script validates all of the following:

1. the version format;
2. the `release/<version>` branch alignment;
3. the rbg tag, resolved explicitly as `refs/tags/<version>`;
4. the matching rbg-api tag.

It then uses the resolved rbg tag commit for every source read, updates
`go.mod` to require the matching `sigs.k8s.io/rbgs/api` version, and replaces
it with the published `github.com/sgl-project/rbg-api` repository.

`replace` directives in this repository's `go.mod` only affect this repository's
own builds and tests. Consumers must still add the documented `replace`
directives for both `sigs.k8s.io/rbgs/api` and
`sigs.k8s.io/rbgs/client-go` in their own main module.

Only these tag formats are accepted:

```text
vX.Y.Z
vX.Y.Z-alpha.N
vX.Y.Z-beta.N
vX.Y.Z-rc.N
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
