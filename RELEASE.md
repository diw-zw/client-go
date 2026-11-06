# Release Process

RBG client-go is released in lockstep with the matching RBG and rbg-api
versions.

1. Confirm the target RBG tag exists in the source repository.
2. Sync the generated client:

   ```bash
   git switch -c "release/$VERSION"
   make sync
   ```

3. Run `make build`, `make test`, and `make vet`.
4. Ask an [OWNER](OWNERS) to review the generated diff.
5. Tag the release:

   ```bash
   git tag -s "$VERSION"
   git push origin "$VERSION"
   ```

6. Publish the release notes and close the release issue.
