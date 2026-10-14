# Publication contract

The repository stores only final rendered publications and their verification metadata. Work-in-progress manuscripts, PDF source files and algorithm code belong in separate repositories.

## Immutable paths

Use `publications/<topic>/<paper-id>/<version>/`. Example:

```text
publications/sliding-puzzles/constructive-million/v1.0.0/
  article.pdf
  manifest.json
  manifest.json.minisig
  SHA256SUMS
```

An earlier release version is retained as published; amendments and corrections create a **new** version directory. The PDF links to its exact source commit, which remains available even if the main branch changes. Git repository owners can technically rewrite history: this contract is a publication discipline, **not** an append-only guarantee provided by GitHub. Independent signatures, separately anchored public keys and backups make silent modifications detectable.

## Manifest schema v1

```json
{
  "schema": "quendoris-papers-v1",
  "paper_id": "constructive-million",
  "version": "v1.0.0",
  "title": "Constructively Solvable Million-Side Sliding Puzzles",
  "published_utc": "2026-10-14T20:00:00Z",
  "source": {
    "repository": "https://github.com/quendoris/implicit-sliding-puzzles",
    "commit": "0123456789abcdef0123456789abcdef01234567"
  },
  "files": [
    {
      "path": "article.pdf",
      "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    }
  ]
}
```

**This is illustrative, not a real release**; use the genuine UTC time, source commit and SHA-256 for every asset. Filenames must be safe ASCII relative paths (no spaces, traversal or symlinks). `article.pdf` is required. The manifest also supports additional rendered assets such as separate figures or supplementary PDFs. All files must be listed.

For each file, `SHA256SUMS` contains the lowercase SHA-256 followed by two spaces and the relative filename, sorted by filename, with a final newline.

## Signing

The private Minisign key is generated and stored on the trusted authoring workstation (Arch), *never* uploaded to GitHub or the publication server.

After placing the public key in `keys/papers.pub`, a release can be signed offline:

```sh
minisign -S -s /path/on/Arch/papers.key \
  -m publications/sliding-puzzles/constructive-million/v1.0.0/manifest.json \
  -x publications/sliding-puzzles/constructive-million/v1.0.0/manifest.json.minisig
```

Check before publishing:

```sh
python3 tools/verify_papers.py --all
```

The repository CI rejects missing/invalid signatures once releases are added, using `keys/papers.pub`. **The public key itself requires an independent trust anchor:** publish the key fingerprint and/or the key on a separate trusted channel. A GitHub repository rewrite could otherwise replace both manifests and public keys.

In this archive the manifest signature covers hashes of every listed PDF/asset. `SHA256SUMS` is cross-checked against the signed manifest. A checksum alone is not proof of origin.

## Cross-links and provenance

Each PDF should cite a fixed source commit or release, and the code repository should link back to the published paper version. The site hosted on HP may render a catalog and links, but must not be the only distribution source.

## Licenses and attribution

Original published PDFs and accompanying non-software illustrations in this archive are licensed **Creative Commons Attribution 4.0 International (CC BY 4.0)**, see repository [LICENSE](../LICENSE) and [official legal code](https://creativecommons.org/licenses/by/4.0/legalcode). The PDF itself must identify the author(s), title, original publication URL and CC BY 4.0 notice. Reusers must provide appropriate attribution, refer to the license and indicate modifications.

Repository verifier scripts, unit tests and CI configurations are licensed **Apache-2.0**, see [LICENSE-CODE](../LICENSE-CODE). Any separately identified third-party material retains its own rights and must have permission/attribution recorded before inclusion.

Publication of the PDF and its source commit must not imply mathematical proof beyond what is documented in the article and checked by the independent verifier.
