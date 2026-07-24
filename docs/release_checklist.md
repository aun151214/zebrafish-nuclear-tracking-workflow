# Private repository release checklist

## Required before the first commit

- [ ] Work from the final clean candidate directory, not the audit/staging tree.
- [ ] `python -m pytest tests -q` passes.
- [ ] Every command-line script exits successfully with `--help`, except
      scripts intentionally designed as direct environment checks.
- [ ] `python scripts/check_repository_cleanliness.py --root .` passes.
- [ ] No `audit/`, `legacy_reference/`, cache or local path file is present.
- [ ] No microscopy TIFF/HDF5/MAT/Mastodon data is present.
- [ ] `configs/paths.yaml` is absent and ignored.
- [ ] `LICENSE_PENDING.md` remains present.
- [ ] The repository is created as **private**.
- [ ] The initial Git remote is reviewed before pushing.

## Required before any public release

- [ ] Oates Lab / EPFL confirms ownership.
- [ ] A licence is selected and approved.
- [ ] Authorship and citation metadata are approved.
- [ ] iTEC and Dark-sectioning redistribution boundaries are confirmed.
- [ ] Any example data is approved for sharing.
- [ ] The repository URL is added to `CITATION.cff`.
- [ ] A tagged release is created only after the preceding items are complete.
