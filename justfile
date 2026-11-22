# Hand-authored docs-first gate; no project.cue projects exist yet.
# Future slot projects use Shaka-generated justfiles.

validate:
    shaka preflight
    shaka whitespace check
    nix flake check

corpus-check:
    cue fmt --check corpus/*.cue experiments/jev/*.cue experiments/workbench/*.cue
    cue vet -c corpus/*.cue
    cue vet -c experiments/jev/*.cue
    cue vet -c experiments/workbench/*.cue
    python -m unittest discover -s tests -v

# Offline, recorded responses only. Use a new output path for each run.
workbench output:
    python -m scripts.workbench --output {{quote(output)}}

corpus-export:
    cue export corpus/*.cue

fmt:
    nix fmt -- flake.nix
    cue fmt corpus/*.cue experiments/jev/*.cue experiments/workbench/*.cue

repo-audit:
    shaka repo audit --repo kolohelios/doozer
