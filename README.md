# Papers

Published research papers, technical articles, and cryptographic verification records.

This repository contains **rendered, versioned publications**. Algorithm implementations, tests and proofs-as-code live in their respective research repositories. The publication web site is a separate distribution channel.

## Publication format

Each released version has a stable path:

```text
<topic>/<paper-id>/<version>/
  article.pdf
  manifest.json
  manifest.json.minisig
  SHA256SUMS
```

The manifest binds the publication to exact PDF bytes and, when applicable, a 40-character Git commit identifying its source code. `SHA256SUMS` provides an additional convenient checksum listing. Release manifests are signed with an **offline** Minisign key; the public verification key is kept under `keys/`.

**Existing releases are never intentionally overwritten.** Corrections are published as additional versions, retaining previous ones.

## Verification

```sh
python3 -m unittest discover -s tests -v
python3 tools/verify_papers.py --all
```

The second command verifies publication hashes and signatures. If no publications have been released yet, it checks repository structure and exits successfully. Once released documents exist, a missing signing key or detached signature is an error.

See [Publication contract](docs/PUBLICATION_CONTRACT.md) for the manifest format and offline signing workflow.

## Research sources

- [Implicit Sliding Puzzles](https://github.com/quendoris/implicit-sliding-puzzles)

## Status

Repository initialized; no paper has been published yet. Licenses for papers and supporting material will be declared explicitly before the first public release. Public visibility alone is not a reuse license.
