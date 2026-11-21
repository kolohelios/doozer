# Hand-authored docs-first gate; no project.cue projects exist yet.
# Future slot projects use Shaka-generated justfiles.

validate:
    shaka preflight
    shaka whitespace check
    nix flake check

fmt:
    nix fmt -- flake.nix

repo-audit:
    shaka repo audit --repo kolohelios/doozer
