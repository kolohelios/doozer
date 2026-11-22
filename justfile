# Hand-authored docs-first gate; no project.cue projects exist yet.
# Future slot projects use Shaka-generated justfiles.

validate:
    shaka preflight
    shaka whitespace check
    nix flake check

corpus-check:
    cue fmt --check corpus/*.cue
    cue vet -c corpus/*.cue
    python -m unittest discover -s tests -v

corpus-export:
    cue export corpus/*.cue

fmt:
    nix fmt -- flake.nix
    cue fmt corpus/*.cue

repo-audit:
    shaka repo audit --repo kolohelios/doozer
