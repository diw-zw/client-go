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

**Important:** Both module paths (`sigs.k8s.io/rbgs/api` and
`sigs.k8s.io/rbgs/client-go`) do not match their repository hosts. Direct
`go get` calls will fail without the `replace` directives shown below.

The generated clients in this repository require `k8s.io/client-go` v0.34.2
or newer. Older versions do not provide the `gentype` helper used by the
generated `GetClient()` calls.

Add the following to your application's `go.mod`:

```go
require (
    sigs.k8s.io/rbgs/api v0.8.0
    sigs.k8s.io/rbgs/client-go v0.8.0
)

replace (
    sigs.k8s.io/rbgs/api => github.com/sgl-project/rbg-api v0.8.0
    sigs.k8s.io/rbgs/client-go => github.com/rolebasedgroup/client-go v0.8.0
)
```

Then run:

```bash
go mod tidy
```

Once `v0.8.0` is tagged in the client-go repository, both modules can be
resolved through the `replace` directives above.

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
make sync
```

On a `release/<version>` branch, the version is inferred from the branch name.
On any other branch, pass `VERSION` explicitly:

```bash
make sync VERSION=v0.8.0
```

The command requires a local `../rbg` checkout. It automatically updates
`go.mod` to use the matching published `rbg-api` version. See
`script/README.md` for direct script usage.

## Verification

```bash
make test
make vet
```

These targets use the `replace` directive maintained by the sync script.

## Release compatibility

| client-go | rbg-api | RBG | Preferred API version |
|-----------|---------|-----|-----------------------|
| v0.9.0-alpha.2 | v0.9.0-alpha.2 | [v0.9.0-alpha.2](https://github.com/sgl-project/rbg/releases/tag/v0.9.0-alpha.2) | v1alpha2 |
| v0.9.0-alpha.1 | v0.9.0-alpha.1 | [v0.9.0-alpha.1](https://github.com/sgl-project/rbg/releases/tag/v0.9.0-alpha.1) | v1alpha2 |
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
