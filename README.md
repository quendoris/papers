# Papers

Published research papers, technical articles, and cryptographic verification records.

This repository holds only **rendered, versioned publications**. Algorithm code, tests, and manuscript sources belong in their respective research repositories. A separately hosted static website may link to these PDFs, but is not a dependency for retrieving or verifying them.

## Layout

```text
publications/
  <topic>/<paper-id>/<version>/
    article.pdf
    manifest.json
    manifest.json.minisig
    SHA256SUMS
keys/
  papers.pub  (added with the first signed release)
docs/
  PUBLICATION_CONTRACT.md
tools/
  verify_papers.py
```

Each released version has a permanent path. Corrections add a new version rather than replacing the old PDF. The manifest binds PDF hashes to the exact source Git commit; the detached Minisign signature binds the manifest to the publication key.

```sh
python3 -m unittest discover -s tests -v
python3 tools/verify_papers.py --all
```

Until a first signed release exists, no papers are published here. See [Publication contract](docs/PUBLICATION_CONTRACT.md) for schema, signature and offline-key rules.

## Related research

- [Implicit Sliding Puzzles](https://github.com/quendoris/implicit-sliding-puzzles)

## Status and licensing

Initialized on 14 October 2026. Licenses for individual articles and supporting materials will be explicitly declared before release; a public repository is not by itself a license grant.
