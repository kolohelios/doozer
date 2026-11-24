# Hand-authored docs-first gate; no project.cue projects exist yet.
# Future slot projects use Shaka-generated justfiles.

validate:
    shaka preflight
    shaka whitespace check
    nix flake check

corpus-check:
    cue fmt --check corpus/*.cue corpus/standards/*.cue experiments/jev/*.cue experiments/workbench/*.cue experiments/retrieval/*.cue experiments/understanding/*.cue experiments/calibration/*.cue experiments/judgment/*.cue
    cue vet -c corpus/*.cue
    cue vet -c corpus/standards/*.cue
    cue vet -c experiments/jev/*.cue
    cue vet -c experiments/workbench/*.cue
    cue vet -c experiments/retrieval/*.cue
    cue vet -c experiments/understanding/*.cue
    cue vet -c experiments/calibration/*.cue
    cue vet -c experiments/judgment/*.cue
    python -m scripts.calibration
    python -m unittest discover -s tests -v

# Offline, recorded responses only. Use a new output path for each run.
workbench output:
    python -m scripts.workbench --output {{quote(output)}}

# Offline source-free consolidation, append-only ablation, rollback, and replay.
retry-maintenance output:
    python -m scripts.retry_maintenance --output {{quote(output)}}

# Prepare one proposer checkpoint offline; no model, provider, budget, or live flag.
maintenance-proposer output:
    python -m scripts.maintenance_proposer --output {{quote(output)}}

# Freeze the proposed one-call request only; live opt-in is deliberately separate.
maintenance-call output:
    python -m scripts.maintenance_call --output {{quote(output)}}

# Same evidence, two working representations; freeze only, no generation.
maintenance-contrast output:
    python -m scripts.maintenance_call --contrast --output {{quote(output)}}

# Offline lexical baseline; use retrieval_probe --embed for opt-in embeddings.
retrieval output:
    python -m scripts.retrieval_probe --output {{quote(output)}}

# Freeze a plan only: no embedding, generation, or judging calls.
understanding output:
    python -m scripts.understanding --output {{quote(output)}}

# Draft annotations and support availability only: no judge, no approval, no scores.
calibration:
    python -m scripts.calibration

# Freeze the multi-pass protocol without credentials or paid calls.
judgment output:
    python -m scripts.jev_multipass --output {{quote(output)}}

# Freeze forked evidence updates and bounded retrieval; no model calls.
evidence-expansion output:
    python -m scripts.evidence_expansion --output {{quote(output)}}

# Freeze independent source interpretations and panel controls; no paid calls.
source-panel output:
    python -m scripts.source_panel --output {{quote(output)}}

# Freeze the paired longer-thread comparison under the shared contract; no calls.
reviewed-panel output:
    python -m scripts.reviewed_panel --output {{quote(output)}}

# Freeze the fresh 84-call paired protocol offline; never resume old runs.
scale-panel output:
    python -m scripts.scale_panel --output {{quote(output)}}

# Prospective shared-contract/ABI request previews only; no live option or budget.
scale-contract output:
    python -m scripts.scale_contract --output {{quote(output)}}

# Check the exact human-review packet against its CUE source; never approve.
interpretation-review:
    python -m scripts.interpretation_review --check

# Prospective audit ABI and pending source-meaning reviews; entirely offline.
audit-contract:
    python -m scripts.audit_contract --check

transfer-review:
    python -m scripts.transfer_review --check

# Authored extraction-to-reader checks only; no model calls or approval effects.
meaning-projection:
    python -m scripts.meaning_projection --check

corpus-export:
    cue export corpus/*.cue

fmt:
    nix fmt -- flake.nix
    cue fmt corpus/*.cue corpus/standards/*.cue experiments/jev/*.cue experiments/workbench/*.cue experiments/retrieval/*.cue experiments/understanding/*.cue experiments/calibration/*.cue experiments/judgment/*.cue

repo-audit:
    shaka repo audit --repo kolohelios/doozer
