# Development and release guide

## Checks

Run these commands from the repository root:

```sh
npm test
npm run test:release
python -B dev-tools/buildScripts/build_release.py --dist dist
```

The builder creates a versioned ZIP, the ZIP referenced by `module.json`, an external manifest, and `SHA256SUMS.txt`. It reads from a committed Git reference, so an ordinary build requires a clean working tree. Use `--ref <commit-or-tag>` to inspect another revision.

## Release procedure

1. Move completed notes from `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD` in `CHANGELOG.md`.
2. Set the same `X.Y.Z` version in `module.json` and its versioned `download` URL.
3. Commit the changes and run the checks above.
4. Create and push the annotated tag `vX.Y.Z` on that commit.
5. The GitHub release workflow validates the tag, then creates a draft release with the ZIP, `module.json`, and checksum file. Review the draft and publish it.

Never change document IDs, UUIDs, activity IDs, effect IDs, advancement IDs, module IDs, or the compendium filename as part of a translation release.
