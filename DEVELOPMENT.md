# Development

The following commands are available for developers:

```sh
just install        # setup venv, install dependencies and local package
just test           # run unit tests
just format         # format code
just lint           # check linting
just doc            # build docs
just doc-preview    # preview docs in browser
just changelog      # print the inputs for a release's changelog section
just release        # build distribution packages
just upload         # upload the current version to pypi
just clean          # clean build and docs artifacts
```

## Versioning and release notes

The version lives in `pyproject.toml` and follows `major.minor.patch`. Ordinary
PRs touch neither the version nor `CHANGELOG.md`: write a clear conventional-commit
title and a description that says what changed for users, because those are the
raw material for the release notes.

A release starts with a release PR, which does two things:

1. Bumps the version, choosing major, minor or patch by hand:
   `uv version --bump minor` (this also updates `uv.lock`).
2. Adds a `## X.Y.Z` section to `CHANGELOG.md`. Run `just changelog` to print the
   merged PRs (with descriptions) and commits since the last tag, and give that
   to an agent or write the section yourself. Group entries (for example
   Breaking changes, New features, Fixes), say what users must do about breaking
   changes, and link PRs. Review it like any other PR.

The section's heading is the bare version, such as `## 0.9.0`, because
`create_release` looks it up by that exact text.

## Release process

`dev` is the only long-lived branch. Once the release PR is merged, run the
[create_release](https://github.com/cmu-delphi/epidatpy/actions/workflows/create_release.yml)
workflow from `dev`. It tags `vX.Y.Z` at `dev` HEAD and refuses if that tag already
exists, which usually means the version wasn't bumped.

We don't maintain release lines. If an old version ever needs a hotfix, branch from
its tag (`git switch -c rel-X.Y vX.Y.Z`), apply the fix, and tag and publish by hand.

The workflow creates a [GitHub release](https://github.com/cmu-delphi/epidatpy/releases)
whose notes are the version's `CHANGELOG.md` section, so the file and the release
never disagree. It checks for that section before pushing anything and fails with a
clear message if it is missing. Pushing the `vX.Y.Z` tag then triggers `pypi_publish`
(build + upload to [PyPI](https://pypi.python.org/pypi/epidatpy/)) and `documentation`
(docs rebuild). Because publishing is a separate workflow keyed off the tag rather
than a step inside `create_release`, a failed PyPI upload can be re-run against the
existing tag via the `pypi_publish` workflow's `Run workflow` button, without redoing
the release cut.
