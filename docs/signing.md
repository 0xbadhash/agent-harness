# Signing / SBOM (Tier C-3 scaffold)

Optional until a product ships public release artifacts.

## Recommended when ready

1. Generate CycloneDX or SPDX SBOM in CI (`sbom.cdx.json`).
2. Sign container images or release tarballs with cosign / sigstore.
3. Pin public key or identity in `cosign.pub` or this doc.
4. Gate: `python3 scripts/check_sbom_signing.py --strict` on release branches only.

agent-harness itself remains a **scripts + skills** repo; SBOM is product-facing.
