# RBG client-go

This repository contains the generated Kubernetes client libraries for
[RoleBasedGroup (RBG)](https://github.com/sgl-project/rbg):

- clientsets
- apply configurations
- informers
- listers

The API types live in the separate
[rbg-api](https://github.com/sgl-project/rbg-api) module. Splitting the
generated clients from the API keeps `sigs.k8s.io/rbgs/api` lightweight while
still allowing generated code to import the stable API path.

## Import path

```go
import (
    "context"

    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    "k8s.io/client-go/rest"
    rbgsapi "sigs.k8s.io/rbgs/api/workloads/v1alpha2"
    rbgsclient "sigs.k8s.io/rbgs/client-go/clientset/versioned"
)
```

This module is declared as `sigs.k8s.io/rbgs/client-go`. If the
`sigs.k8s.io` vanity endpoint is not configured for this repository, consumers
must add a temporary `replace` directive pointing at the actual Git repository.

## Installation

**Important:** The RBG API module path (`sigs.k8s.io/rbgs/api`) does not match
its repository host (`github.com/sgl-project/rbg-api`). Direct `go get
sigs.k8s.io/rbgs/api` will fail.

The generated clients in this repository require `k8s.io/client-go` v0.34.2
or newer. Older versions do not provide the `gentype` helper used by the
generated `GetClient()` calls.

Add the following to your application's `go.mod`:

```go
require (
    sigs.k8s.io/rbgs/api v0.8.0
    sigs.k8s.io/rbgs/client-go v0.8.0
)

replace sigs.k8s.io/rbgs/api => github.com/sgl-project/rbg-api v0.8.0
```

Then run:

```bash
go mod tidy
```

If `sigs.k8s.io/rbgs/client-go` is also not reachable through a vanity
endpoint, add a second `replace` directive for this repository's published Git
location.

## Example

```go
config, err := rest.InClusterConfig()
if err != nil {
    return err
}

client, err := rbgsclient.NewForConfig(config)
if err != nil {
    return err
}

var rbg *rbgsapi.RoleBasedGroup
rbg, err = client.WorkloadsV1alpha2().
    RoleBasedGroups(namespace).
    Get(ctx, name, metav1.GetOptions{})
```

## Sync from rbg

Generated code is synchronized from the rbg repository:

```bash
make sync REF=v0.8.0 API_VERSION=v0.8.0
```

The command requires a local `../rbg` checkout and, by default, a local
`../rbg-api` checkout. See `script/README.md` for direct script usage.

## Verification

```bash
make test
make vet
```

These targets temporarily point `sigs.k8s.io/rbgs/api` at the local
`../rbg-api` checkout while running the command, then restore `go.mod`.

## Release compatibility

| client-go | rbg-api | RBG | Preferred API version |
|-----------|---------|-----|-----------------------|
| v0.8.0 | v0.8.0 | [v0.8.0](https://github.com/sgl-project/rbg/releases/tag/v0.8.0) | v1alpha2 |

## Community, discussion, contribution, and support

Learn how to engage with the Kubernetes community on the
[community page](http://kubernetes.io/community/).

The maintainers of this project can be reached at:

- [Slack](https://slack.k8s.io/)
- [Mailing List](https://groups.google.com/a/kubernetes.io/g/dev)

### Code of conduct

Participation in the Kubernetes community is governed by the Kubernetes Code of
Conduct.
