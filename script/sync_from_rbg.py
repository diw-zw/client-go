#!/usr/bin/env python3
"""Extract the generated client-go tree from an rbg repository revision.

The generated client imports the public API as ``sigs.k8s.io/rbgs/api``.
That API is intentionally not copied into this repository. Instead, this
client-go module requires the matching version of the separately published
rbg-api module.

Example:

    python3 script/sync_from_rbg.py \
        --source ../rbg \
        --go go
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable


CLIENT_SOURCE = "client-go"
API_SOURCE = "api/workloads"
MODULE_PATH = "sigs.k8s.io/rbgs/client-go"
API_MODULE = "sigs.k8s.io/rbgs/api"
API_REPOSITORY = "https://github.com/sgl-project/rbg-api"
RELEASE_BRANCH_PREFIX = "release/"

GENERATED_DIRECTORIES = (
    "applyconfiguration",
    "clientset",
    "informers",
    "listers",
)

SOURCE_DIRECT_DEPENDENCIES = (
    "k8s.io/api",
    "k8s.io/apimachinery",
    "k8s.io/client-go",
)

VERSION_PATTERN = re.compile(
    r"^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-(?:alpha|beta|rc)\.(0|[1-9][0-9]*))?$"
)
GO_DIRECTIVE_PATTERN = re.compile(
    r"^go\s+([0-9]+(?:\.[0-9]+)+)\s*$", re.MULTILINE
)
IMPORT_PATTERN = re.compile(r"\"([^\"\n]+)\"")


class SyncError(RuntimeError):
    pass


def run_git(source: Path, args: Iterable[str]) -> subprocess.CompletedProcess[bytes]:
    command = ["git", "-C", str(source), *args]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise SyncError(f"command failed ({' '.join(command)}): {detail}")
    return result


def run_go(
    go_command: str,
    root: Path,
    args: Iterable[str],
) -> subprocess.CompletedProcess[bytes]:
    command = [go_command, *args]
    result = subprocess.run(command, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise SyncError(f"command failed ({' '.join(command)}): {detail}")
    return result


def resolve_rbg_tag(source: Path, version: str) -> str:
    if not source.is_dir():
        raise SyncError(f"rbg source does not exist: {source}")
    if not (source / ".git").exists():
        raise SyncError(f"rbg source is not a Git repository: {source}")
    result = run_git(
        source,
        ["rev-parse", "--verify", f"refs/tags/{version}^{{commit}}"],
    )
    return result.stdout.decode("utf-8").strip()


def ensure_rbg_api_tag(version: str) -> None:
    result = subprocess.run(
        [
            "git",
            "ls-remote",
            "--exit-code",
            "--tags",
            API_REPOSITORY,
            f"refs/tags/{version}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise SyncError(f"rbg-api tag does not exist: {version}")


def current_branch(root: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(root), "symbolic-ref", "--quiet", "--short", "HEAD"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def resolve_release_version(root: Path, requested: str | None) -> str:
    branch = current_branch(root)
    from_branch = (
        branch[len(RELEASE_BRANCH_PREFIX):]
        if branch and branch.startswith(RELEASE_BRANCH_PREFIX)
        else None
    )
    if requested and from_branch and requested != from_branch:
        raise SyncError(
            f"--ref {requested} does not match branch {branch}"
        )
    version = requested or from_branch
    if not version:
        raise SyncError(
            "--ref is required unless HEAD is on a release/<version> branch"
        )
    if not VERSION_PATTERN.fullmatch(version):
        raise SyncError(
            f"invalid version {version!r}: expected vX.Y.Z or "
            "vX.Y.Z-(alpha|beta|rc).N"
        )
    return version


def ensure_destination(root: Path) -> None:
    if not root.is_dir():
        raise SyncError(f"destination does not exist: {root}")
    if not (root / "go.mod").is_file():
        raise SyncError(f"destination is not a Go module: {root}")


def source_paths(source: Path, commit: str, path: str) -> list[str]:
    result = run_git(
        source,
        ["ls-tree", "-r", "--name-only", commit, "--", path],
    )
    paths = result.stdout.decode("utf-8").splitlines()
    return [item for item in paths if item and not item.endswith("/")]


def clear_generated_tree(root: Path, directory: str) -> None:
    target = root / directory
    if not target.exists():
        return

    resolved_root = root.resolve()
    resolved_target = target.resolve()
    if resolved_root not in resolved_target.parents:
        raise SyncError(f"refusing to remove directory outside repository: {target}")
    shutil.rmtree(target)


def destination_path(root: Path, source_path: str) -> Path:
    relative = source_path[len(CLIENT_SOURCE) + 1 :]
    target = root / relative
    resolved_root = root.resolve()
    resolved_target = target.resolve()
    if resolved_root not in resolved_target.parents:
        raise SyncError(f"destination escapes repository: {target}")
    return target


def copy_generated_client(
    source: Path,
    commit: str,
    root: Path,
    files: list[str],
) -> int:
    for directory in GENERATED_DIRECTORIES:
        clear_generated_tree(root, directory)

    copied = 0
    for source_path in files:
        if not source_path.endswith(".go"):
            continue
        if not source_path.startswith(CLIENT_SOURCE + "/"):
            raise SyncError(f"unexpected client-go source path: {source_path}")

        blob = run_git(source, ["show", f"{commit}:{source_path}"]).stdout
        target = destination_path(root, source_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob)
        copied += 1

    return copied


def generated_go_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for directory in GENERATED_DIRECTORIES:
        files.extend(sorted((root / directory).rglob("*.go")))
    return files


def format_copied_go_files(root: Path) -> None:
    files = generated_go_files(root)
    if files:
        subprocess.run(
            ["gofmt", "-w", *(str(path) for path in files)],
            check=True,
        )


def versions_from_paths(paths: list[str], prefix: str) -> set[str]:
    versions: set[str] = set()
    pattern = re.compile(
        re.escape(prefix)
        + r"(?:/[^/]+)*/(v[0-9]+(?:alpha|beta)?[0-9]*)/"
    )
    for path in paths:
        match = pattern.search(path)
        if match:
            versions.add(match.group(1))
    return versions


def validate_api_coverage(
    source: Path,
    commit: str,
    client_files: list[str],
) -> set[str]:
    api_files = source_paths(source, commit, API_SOURCE)
    if not api_files:
        raise SyncError(f"no {API_SOURCE} files found in rbg commit {commit}")

    api_versions = versions_from_paths(api_files, API_SOURCE)
    client_versions = versions_from_paths(client_files, CLIENT_SOURCE)
    if not client_versions:
        raise SyncError("generated client contains no API versions")

    missing = sorted(client_versions - api_versions)
    if missing:
        raise SyncError(
            "generated client references API versions absent from rbg: "
            + ", ".join(missing)
        )
    return api_versions


def validate_generated_imports(root: Path) -> None:
    for path in generated_go_files(root):
        content = path.read_text(encoding="utf-8")
        if "sigs.k8s.io/controller-runtime" in content:
            raise SyncError(f"controller-runtime import remains in {path}")

        for imported in IMPORT_PATTERN.findall(content):
            if not imported.startswith("sigs.k8s.io/rbgs/"):
                continue
            allowed = (
                imported.startswith(API_MODULE + "/")
                or imported.startswith(MODULE_PATH + "/")
            )
            if not allowed:
                raise SyncError(
                    f"unexpected rbg import {imported!r} in {path}; "
                    f"only {API_MODULE}/... and {MODULE_PATH}/... are allowed"
                )


def source_go_mod(source: Path, commit: str) -> str:
    return run_git(source, ["show", f"{commit}:go.mod"]).stdout.decode("utf-8")


def required_version(go_mod: str, module: str) -> str:
    pattern = re.compile(
        rf"^\s*{re.escape(module)}\s+(v[^\s]+)\s*$", re.MULTILINE
    )
    match = pattern.search(go_mod)
    if match is None:
        raise SyncError(f"could not find required version for {module} in rbg go.mod")
    return match.group(1)


def update_go_mod(
    root: Path,
    source: Path,
    commit: str,
    api_version: str,
    go_command: str,
) -> None:
    go_mod = root / "go.mod"
    if not go_mod.is_file():
        go_mod.write_text(f"module {MODULE_PATH}\n\ngo 1.25.0\n", encoding="utf-8")

    source_module = source_go_mod(source, commit)
    go_match = GO_DIRECTIVE_PATTERN.search(source_module)
    if go_match is None:
        raise SyncError("could not parse the go directive from rbg go.mod")

    requirements = [f"{API_MODULE}@{api_version}"]
    requirements.extend(
        f"{module}@{required_version(source_module, module)}"
        for module in SOURCE_DIRECT_DEPENDENCIES
    )

    run_go(go_command, root, ["mod", "edit", f"-module={MODULE_PATH}"])
    run_go(go_command, root, ["mod", "edit", f"-go={go_match.group(1)}"])
    for requirement in requirements:
        run_go(go_command, root, ["mod", "edit", f"-require={requirement}"])
    run_go(
        go_command,
        root,
        [
            "mod",
            "edit",
            f"-replace={API_MODULE}=github.com/sgl-project/rbg-api@{api_version}",
        ],
    )


def update_readme_version(root: Path, version: str, api_versions: set[str]) -> None:
    readme = root / "README.md"
    if not readme.is_file():
        return

    preferred = "v1alpha2" if "v1alpha2" in api_versions else ", ".join(sorted(api_versions))
    release_row = (
        f"| {version} | {version} | [{version}]"
        "(https://github.com/sgl-project/rbg/releases/tag/"
        f"{version}) | {preferred} |"
    )
    text = readme.read_text(encoding="utf-8")
    if release_row in text:
        return

    pattern = r"(## Release compatibility\n\n\|[^\n]+\n\|[^\n]+\n)"
    updated, count = re.subn(pattern, rf"\1{release_row}\n", text, count=1)
    if count:
        readme.write_text(updated, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    default_source = Path(__file__).resolve().parents[2] / "rbg"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=default_source,
        help=f"path to the rbg repository (default: {default_source})",
    )
    parser.add_argument(
        "--ref",
        help=(
            "rbg semantic version tag; defaults to the release/<version> "
            "branch name"
        ),
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=Path.cwd(),
        help="client-go repository root (default: current directory)",
    )
    parser.add_argument("--go", default="go", help="Go executable (default: go)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.expanduser().resolve()
    root = args.destination.expanduser().resolve()
    version = resolve_release_version(root, args.ref)
    api_version = version

    tag_commit = resolve_rbg_tag(source, version)
    ensure_destination(root)
    ensure_rbg_api_tag(version)

    client_files = source_paths(source, tag_commit, CLIENT_SOURCE)
    if not any(path.endswith(".go") for path in client_files):
        raise SyncError(f"no generated client-go files found in rbg {version}")
    api_versions = validate_api_coverage(source, tag_commit, client_files)

    copied = copy_generated_client(source, tag_commit, root, client_files)
    format_copied_go_files(root)
    validate_generated_imports(root)
    if copied == 0:
        raise SyncError("selected no generated client-go files")

    update_go_mod(root, source, tag_commit, api_version, args.go)
    run_go(args.go, root, ["mod", "tidy"])

    update_readme_version(root, version, api_versions)
    print(
        f"Synced rbg {version} at {tag_commit}: {copied} generated client-go files; "
        f"requires {API_MODULE} {api_version}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (SyncError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
