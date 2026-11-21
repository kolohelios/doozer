# Doozers — Engineering Design Document

**Version:** 0.4

**Date:** November 21, 2026

**Status:** Working design; behavioral invariants distinguished from hypotheses

**Companion:** [Doozers PRD v0.4](PRD.md)

**Revision focus:** Add native discovery, outcome-sensitive guidance, durable at-least-once event delivery, and incremental eventual reconciliation. Keep evidence/knowledge separate from the event transport and retain a small first implementation.

> **Design premise:** Doozers is an *optimizing compiler for collective knowledge*, not a documentation generator or decision-making authority. It should improve the live representation while preserving material meaning, temporal context, evidence, uncertainty, and paths to discovery. “Compiler” is an engineering analogy, **not** a claim that natural-language equivalence can be mechanically proven.

## 1. Purpose and boundaries

This EDD translates the PRD's product contract into a testable engineering model. We should revise it when experiments reveal mistakes, rather than locking in infrastructure prematurely.

**In scope now:** Knowledge IR; evidence and relationship semantics; semantic reconciliation and autonomous compaction; native search/discovery; contextual guidance and open-ended projections; durable asynchronous ingestion and eventual reconciliation; failure and replay semantics; fixture-driven verification.

**Not yet decided:** Graph versus relational persistence; physical IDs; embedding/model provider; dedicated stream broker versus database-backed dispatch; durable workflow engine; multiuser production deployment; ontology; chat/wiki frontend; output-specific publication mechanisms. These are implementation choices, not product requirements.

### Inherited engineering constraints

1. **Survivability:** Material meaning, exceptions, counterevidence, temporal scope, and historical recoverability survive ordinary transformations.
2. **Discoverability:** Relevant understanding remains findable, even by imprecise terms, former references, or source conversations.
3. **Compactness:** Keep active representation as terse as reasonably parseable, subject to the first two constraints.

No meaningful signal is too small. “No,” “stop,” and “rethink this” can matter more than an entire discussion. Conversely, a lengthy thread can correctly yield **no change**.

Autonomy is the default. Doozers should be able to tidy and reconcile the knowledge it can responsibly reconcile. It must tolerate ambiguity without manufacturing queues of tasks for humans or agents.

## 2. Working semantic model

We must distinguish what was observed, what somebody expressed, what the information bears upon, and what can presently be concluded.

| Concept | Role | Canonical or derived? |
|---|---|---|
| **Source** | Attributable, time-aware message, document, code excerpt, test, observation, or artifact; includes origin and addressable context | Canonical input or a durable authorized reference |
| **Assertion** | Meaning-bearing interpretation of a source: a claim, correction, objection, agreement, observation, question, or contextual speech act | Source-linked interpretation; revision/audit required |
| **Knowledge kernel** | A durable subject, question, or coherent piece of understanding to which assertions relate; not necessarily a settled answer | Canonical organization, at flexible granularity |
| **Relationship** | A contextual and potentially attributable link such as about, supports, qualifies, conflicts, depends-on, or supersedes | Explicit material links may be canonical; reproducible inferred links need not be |
| **Current understanding** | A best-available, scoped interpretation, potentially qualified or unresolved | Derived; optionally cached |
| **Projection** | Target-specific presentation of current understanding, including handbook prose and agent-facing directives | Derived; reproducible; not independent evidence |
| **Change record** | Account of the transformation, its supporting evidence and rationale, and its reversibility | Durable, separate from the current epistemic condition |

These are **semantic responsibilities**, not commitments to tables, object classes, or node types. A kernel's granularity should be justified by useful distinctions and discoverability, not by word count.

### 2.1 Knowledge kernels need not be facts

A useful kernel is **“Under what conditions is event retry safe?”** That question admits qualifications, dependencies, and exceptions. The answer might span database writes, notifications, retries, and manual replay. A kernel does not have to store an independently maintained `safe = true` field when its best-supported answer can be derived.

A kernel can organize a concept, procedure, interface contract, practice, or contested proposition. We do not force all knowledge into subject–predicate–object triples, nor do we commit that every assertion is a separate physical node.

### 2.2 Graph as semantic view, not mandatory persistence

```text
source + context ──anchors──> assertion ──about──> knowledge kernel
                                  │                    ▲
                                  ├──supports──────────┤
                                  ├──qualifies─────────┤──> derived understanding
                                  ├──conflicts─────────┤         │
                                  └──supersedes────────┘     projections
```

An assertion may bear on several kernels. Relationships may need their own source, temporal scope, and conditions. We should store explicitly meaningful relations, derive simple ones where reliable, and avoid duplicating independent representations of the same purported truth.

## 3. Worked fixture: event retries, side effects, and evolving meaning

**All people, dates, conversations, and system details in this fixture are synthetic.** They demonstrate expected behavior, not facts about any workplace.

### 3.1 Incoming evidence in several rounds

| Round | Source | Statement or observation | Why it matters |
|---|---|---|---|
| 1 | Engineering guide | “Event processing is idempotent.” | Broad established guidance; scope unspecified |
| 2 | Team conversation | “Yes, failed events can be retried safely.” | Appears to extend that guidance to a practical action |
| 3 | Code review | “We deduplicate database writes by event ID.” | Supports a narrower, implementation-specific property |
| 4 | Incident report | “Retrying a failed event caused two customer notifications.” | Material counterexample to unrestricted retry safety |
| 5 | Engineer clarification | “Database writes are deduplicated; notification side effects are not.” | Splits the old concept into two materially different behaviors |
| 6 | Operations guide | “Manual replay suppresses outbound notifications.” | Adds a mitigation with limited scope, not universal retry safety |

### 3.2 Expected reconciliation

After rounds 1–2, Doozers may present the team's *expressed* working guidance, but must not imply that every possible side effect has been verified.

After round 3, the system should **qualify** the earlier broad claim: the code supports deduplication of database writes, not idempotence of every downstream effect. Merely finding a source that contains the word “idempotent” is not proof of general retry safety.

After round 4, the system must not keep presenting “retries are safe” without qualification. The incident is evidence that the broad wording is unsafe for at least the reported path.

After rounds 5–6, a useful compact **derived projection** might be:

> **Event retry safety.** Database writes are deduplicated by event ID. Notification side effects can be duplicated by retries. The documented manual-replay path suppresses outbound notifications. Retry safety therefore depends on the execution path and its side effects; do not treat “event processing is idempotent” as a blanket guarantee.

This is **not** six separate wiki pages and is **not** a claim that the incident necessarily invalidates every kind of retry. The original generalization becomes historical; its narrower supported portions survive in current understanding. All source anchors remain available for explanation.

### 3.3 The transformation to test

- **Split:** Separate “database-write deduplication” from “notification-side-effect idempotence.” A correct optimizer sometimes creates a distinction instead of reducing node count.
- **Qualify:** Replace unrestricted retry safety with a scoped explanation.
- **Connect:** Relate incident evidence to the affected safety claim, and manual replay to the documented mitigation.
- **Retire:** Remove the obsolete unqualified guidance from the live view without erasing its history.
- **No-op:** Repeated paraphrases of the same evidence do not necessarily require new canonical knowledge.

**Failure:** The system simply swaps “safe” for “unsafe,” merges database writes and notifications into a single behavior, or suppresses the incident because the old document sounded authoritative.

### 3.4 Negative variants

1. **Nonproduction incident:** If duplicate notifications occurred only in an isolated test environment, the system must preserve that scope rather than asserting production impact.
2. **Echo versus independent evidence:** Two people repeating the same incident report do not become two independent proofs.
3. **Tiny intervention:** A clear reply of “No. That workaround doesn't apply to automatic retries” must retain its referent and correct an overbroad claim about manual replay.
4. **Unresolved case:** If there is no trustworthy evidence about a third side effect, the system should not invent one; it may leave the question unestablished without creating a task.

## 4. Illustrative knowledge IR (not a database schema)

A deliberately compact, loss-aware representation of part of the retry fixture:

```yaml
kernel:
  ref: event-processing/retry-safety
  question: Under what conditions is retrying a failed event safe?

assertions:
  - ref: a1
    source: {ref: s1, anchor: "guide#processing"}
    text: Event processing is idempotent.
    scope: unspecified
  - ref: a2
    source: {ref: s3, anchor: "review:42/comment:3"}
    text: Database writes are deduplicated using event IDs.
    scope: database-writes
  - ref: a3
    source: {ref: s4, anchor: "incident:7/observation:2"}
    text: Retrying an event caused duplicate customer notifications.
    scope: notification-side-effects
  - ref: a4
    source: {ref: s6, anchor: "ops#manual-replay"}
    text: Manual replay suppresses outbound notifications.
    scope: manual-replay

relationships:
  - {from: a2, to: a1, kind: qualifies, scope: database-writes}
  - {from: a3, to: a1, kind: counterexample-to, scope: notification-side-effects}
  - {from: a4, to: a3, kind: mitigates-in, scope: manual-replay}
```

The representation is illustrative, not a fixed ontology. In particular, `counterexample-to` and `mitigates-in` may be model-proposed interpretations that require independent validation before becoming canonical. The original source text, timeline, and contextual anchors must remain retrievable.

The current conclusion is **not** a separately stored truth competing with these inputs. It can be derived or cached, with a recorded rationale for whichever autonomous transformation last altered canonical knowledge.

### 4.1 Minimal invariants

1. Every material assertion has recoverable source context or is explicitly designated an inference or unsourced human assertion.
2. A derived explanation cannot suppress a material counterexample, qualification, or scope restriction.
3. “When said,” “when valid,” and “when ingested” remain distinguishable where the evidence supports them; unknown values remain unknown.
4. Merges, splits, revisions, and retirements preserve useful historical and current discovery paths.
5. A live transformation is auditable and reversible under applicable retention rules.
6. Re-ingesting identical sources cannot create duplicate semantic effects or rewording churn.
7. No result is fabricated merely to fill an apparently empty kernel.
8. Two similar claims are not automatically equivalent; two contradictory-looking claims are not automatically incompatible until their scopes are compared.

## 5. Multi-domain fixture family

These fixtures are based on **real categories of questions**, but their quoted statements are invented. They are not a description of the user's employer, its architecture, policies, or conclusions. They should eventually be replaced or supplemented with authorized, anonymized source material and human-reviewed expected outcomes.

### 5.1 CNPG versus RDS: conditional safety, evidence, and tradeoffs

**Kernel:** “Under what conditions would CloudNativePG be sufficiently safe and operable for this workload compared with Amazon RDS?”

Synthetic inputs arrive over time:

- An engineer says, “RDS is safer because failover is managed.”
- Another notes, “CloudNativePG supports automated failover and point-in-time recovery.”
- An operations engineer says, “We haven't tested a full restore or cross-cluster recovery against our recovery objectives.”
- A team runs a successful node-failure drill for a particular CNPG setup.
- A later drill exposes a recovery gap after loss of the entire Kubernetes cluster.
- A final discussion narrows scope: “CNPG could satisfy this internal service's requirements; the customer-facing critical database needs different evidence.”

**Expected behavior:** Doozers must **decompose “safe”** into the actual conditions being discussed: availability, durability, disaster recovery, backup/restore, operational readiness, workload criticality, failure domain, and accepted recovery objectives. It must distinguish *a product capability* from *our configuration* and from *our demonstrated operational competence*.

The node-failure drill is positive evidence for the scenario tested, **not** proof of disaster recovery. A newly discovered recovery gap is negative evidence within its demonstrated scope, **not** proof that CNPG is categorically unsafe. Later operating experience can change which conditions appear supportable. The current understanding may legitimately differ by workload.

**Unacceptable:** “RDS wins,” “CNPG is safe,” or “the team decided” when the underlying sources show only discussion, without the relevant scope and expressed settlement. Doozers must not make deployment decisions or mistake capability documentation for local operational evidence.

**Grounding for fixture design only:** [CloudNativePG architecture](https://cloudnative-pg.io/docs/current/architecture/), [CloudNativePG failover](https://cloudnative-pg.io/docs/current/failover/), [AWS RDS Multi-AZ failover](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZ.Failover.html). These establish that failure models and responsibilities differ; they do **not** establish any team's suitability judgment.

### 5.2 “Breaking changes”: compatibility is a relationship, not a label

**Kernel:** “What counts as a breaking change, and how do we avoid or manage one?”

Synthetic inputs:

- An engineering guide states, “Adding optional API fields is nonbreaking.”
- A client implementation reveals a strict decoder or exhaustive enum handling that rejects certain previously unseen values.
- A discussion proposes an expand/migrate/contract rollout, leaving old and new representations in place during consumer migration.
- Someone says, “Our compatibility checks all passed,” but the checks cover only generated SDK clients, not all actual consumers.
- A later report documents a behavior change that preserved the schema but altered user-visible semantics.

**Expected behavior:** The system distinguishes *source-level*, *wire/schema*, *behavioral*, *operational*, and *consumer-specific* compatibility. It connects change producers to affected consumers and records conditions such as deploy order, migration windows, and consumer assumptions. It should recognize that “nonbreaking” depends on a specified compatibility contract.

A newly discovered downstream consumer can invalidate an apparently settled guarantee. A passing suite supports only the behavior it tests. Multiple overlapping discussions about migration should compact into coherent, scoped guidance without discarding an exceptional consumer.

**Unacceptable:** Reducing compatibility to semantic-version number alone; inferring safety from “additive” without understanding consumers; merging API changes and database schema migrations as if their failure modes were identical.

**Grounding for fixture design only:** [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html), which presupposes an identified public API and treats incompatible changes differently from compatible changes. A team's real compatibility contract may be broader than SemVer.

### 5.3 Code review today: policy, practice, and changing norms

**Kernel:** “What does effective code review mean for this team, and how is it actually practiced?”

Synthetic inputs:

- An older team guide says, “Two human approvals are required before merge.”
- A developer says, “We use AI review to catch mechanical issues before humans look.”
- Repository records show that several low-risk changes used one human reviewer under a documented exception.
- A discussion says, “Human reviewers should focus on behavior, invariants, risk, and design.”
- A brief reply says, “No. Not for authentication or permission changes.”
- A new team agreement explicitly changes the normal review expectations for one class of repositories.

**Expected behavior:** Doozers distinguishes **stated policy**, **observed behavior**, **proposed practice**, and **an actual expressed change in team convention**. It must preserve repo/risk-specific exceptions. A tool's ability to perform an AI review does not by itself establish that AI review satisfies the team's human-review requirements.

The one-word “No” is substantial only when its target is known. An old written policy and newer behavior may be evidence of drift rather than an authorized policy change. Where the team has not settled the disagreement, an honest reader-facing view may show both.

**Unacceptable:** Concluding “AI has replaced human review” from tool usage; presenting a universal modern best practice as the team's policy; turning unresolved discussion into a review-approval ticket.

**Grounding for fixture design only:** [GitHub PR review semantics](https://docs.github.com/en/pull-requests/get-started/reviewing-pull-requests-quickstart) and [GitHub's optional AI review guidance](https://docs.github.com/en/get-started/start-your-journey/reviewing-your-proposed-changes). These inform examples; they do not determine team norms.

### 5.4 Required cross-cutting fixtures

- **Small token, large change:** “Stop,” “Yes,” “No,” or “rethink this,” evaluated with and without an unambiguous conversational referent.
- **Near-duplicate with critical exception:** Consolidate repeated guidance without destroying one narrow exception.
- **Noise:** Dozens of messages with no knowledge effect yield no live change.
- **Independent corroboration versus repetition:** Distinguish different evidence from retelling a single source.
- **Newly relevant old objection:** An earlier concern regains relevance after a later incident; no need to have generated a task when the concern was first recorded.
- **Nonengineering domain:** A community procedure changes for weekend events but not weekdays; Doozers must preserve this distinction, proving the IR is not software-architecture-specific.

## 6. Knowledge consumers and projections

**Handbook content and agent directives are two useful initial projection fixtures, not an exhaustive set of consumers.** Knowledge may also inform search results, IDE context, automated checks, workflows, APIs, wikis, and future interfaces. A published handbook page and a repository's `AGENTS.md` file may express the same understanding differently, but must not silently drift into incompatible claims. A projection is never a second canonical knowledge store.

### 6.1 Illustrative projections, different contracts

| Projection | Reader and use | Required properties |
|---|---|---|
| **Handbook content** | Engineers looking up current understanding and reasoning | Readable narrative; clear applicability and limitations; rationale; exceptions; discoverable links to source evidence and history |
| **Agent directives** | Coding agents acting in a specific repo, directory, or task context | Short, actionable, unambiguous instructions; bounded applicability; relevant guardrails; no invented policy or unsupported mandate; pointers to fuller handbook rationale when appropriate |

These are **compilation targets**, not mirror copies. The system should preserve semantic consistency without requiring verbatim parity. It should also be capable of emitting no directive when the knowledge is informative but does not justify an instruction.

For example, knowledge that database writes are deduplicated but notification side effects can duplicate may lead to this pair of outputs:

**Illustrative handbook passage**

> Event retries are not universally idempotent. Database writes are deduplicated by event ID, while notification side effects can run more than once. The documented manual-replay path suppresses outbound notifications; that mitigation does not automatically apply to other retry paths. See the related incident and implementation references.

**Illustrative agent directive**

```markdown
# Event processing
Do not assume an event handler is fully idempotent because its database writes are deduplicated. Before implementing retries or replays, account for notification and other external side effects. The manual-replay notification suppression applies only to that path.
```

The handbook explains the reasoning. The directive constrains agent behavior in an appropriate context. Both compile from the same evidence and qualifications.

### 6.2 Projection invariants

1. **Same evidentiary basis:** Generated handbook guidance and agent instructions trace to the same knowledge units, source anchors, and committed transformations. A projection is not independent corroboration of the knowledge that produced it.
2. **No invented policy:** Doozers may synthesize what the team has established but must not convert an observation, proposal, or disputed practice into a normative directive merely to fill a file.
3. **Scope is part of meaning:** Instructions inherit the conditions and applicability of their supporting knowledge: repository, code path, environment, workload, risk class, affected consumer, and time where applicable. A scoped exception must not compile into a global rule.
4. **Uncertainty is represented, not hidden:** When guidance is contested, a handbook may explain the disagreement. The directive compiler must either emit a bounded conservative instruction supported by the evidence, retain unaffected prior guidance, or omit the directive. It must not invent certainty or create an artificial approval task.
5. **Diffable, atomic, reversible publication:** Updates show the knowledge change and affected projection changes together; stale output is invalidated, and version control can restore the previous published view.
6. **Terse but discoverable:** Agent instructions should be compact enough to be operationally useful, with stable pointers to the relevant deeper explanation rather than copying entire handbook sections.
7. **No-op is legitimate:** New inputs that do not change current guidance must not trigger spurious handbook edits or agent-instruction churn.

### 6.3 Generated artifacts must not become circular evidence

Handbooks and agent directives may later be ingested as sources, intentionally or through repository integration. This creates a risk of **self-corroboration**: a directive derived from one assertion appears later as a second source, falsely strengthening the same assertion.

A compiled artifact therefore needs derivation metadata identifying its originating knowledge revision and inputs. Re-ingesting an unchanged generated passage is a no-op, not new evidence. **A human-authored edit** to a handbook or directive is different: the edit is a new, attributable observation or expression of intent, to be reconciled against the knowledge base rather than silently made canonical. We should preserve human-owned regions of documents and avoid clobbering them during projection refresh.

This gives us an important round-trip boundary: **knowledge → projection → human/agent activity → new external evidence → knowledge**, not **knowledge → projection → automatic proof of knowledge**.

### 6.4 Projection fixtures for our three working domains

All examples here are synthetic, not statements of any employer's policy or architectural decision.

| Domain | Handbook projection should convey | Agent directive should convey (only when supported) |
|---|---|---|
| **CNPG versus RDS** | Operational capabilities versus team-demonstrated readiness; workload requirements; tested failure modes; remaining uncertainty | Consult current database guidance and verify workload-specific backup, restore, failover, and operational requirements before proposing or changing a deployment. **Do not** emit a blanket “always use CNPG/RDS” rule without an established team convention. |
| **Breaking changes** | Compatibility contracts, consumer assumptions, migration patterns, notable exceptions, and the reasoning behind guidance | Check downstream consumers and behavioral compatibility before changing interfaces; follow the team's documented migration sequence where applicable. Do not assume an additive schema change is harmless for every consumer. |
| **Code review** | Expressed policy, observed practice, risk-specific exceptions, and evolving use of AI assistance | Follow currently established review requirements for the repository and change risk; use AI review as assistance only to the extent the team has authorized. Never infer that AI approval substitutes for human review from tool usage alone. |

The compiler should support **many-to-many** projection dependencies: one knowledge change may affect several handbook sections and a small set of scoped directives; conversely, a single directive may depend on multiple knowledge units. This is an important reason not to make a document or a directive the identity of the underlying knowledge.

### 6.5 Publication and autonomy

Autonomy remains the default for internal reconciliation and low-risk publication. Agent directives have a **higher behavioral impact** than explanatory prose because they can alter subsequent automated code changes. Publication policy should therefore take into account the intended consumer and change impact without introducing a standing Doozer-maintained queue of approvals.

For example, safe wording improvements or link repairs can publish automatically under the host repository's configured controls; a materially new instruction affecting deployment, credentials, production behavior, or review requirements may follow that repository's existing version-control and review path. If a conflict cannot be resolved, Doozers should leave the relevant uncertainty visible and avoid publishing a falsely settled directive. Exact policy and deployment gates remain open engineering choices.

### 6.6 Outcome-sensitive guidance

**Knowledge becomes potentially instructional when it might change an outcome in a particular context.** This is a relevance rule for delivering guidance, not a new kind of canonical node or an automatic command-generation rule. The same kernel may inform a handbook explanation, an agent constraint, a test warning, or nothing in a given interaction.

A guidance compiler should consider the **consumer, goal, action, scope, evidence, temporal applicability, and uncertainty**. It may produce a bounded instruction, a caution, a link to reasoning, a contextual explanation, or no output. It must not transform foggy or disputed understanding into an unconditional requirement. A change to machine-consumed instructions warrants particular care because it may alter subsequent automated behavior.

We should not invent a standing list of directives for every piece of knowledge. Instead, derive relevant guidance when projecting a specific target or answering a contextual request; cache a stable output only when it is useful.

### 6.7 Open-ended consumers

The system's contract is **reliable, scoped access to maintained understanding**, not a fixed roster of export targets. Each consumer specifies its desired presentation and, where relevant, action context; none may manufacture fresh authority by copying compiled text back into the evidence graph. Search/discovery is a native interactive capability (next section), not merely another static export.

## 7. Native discovery and trustworthy answers

Discovery is a **first-class engine capability**, not a handbook export or an optional chatbot feature. It fulfills the PRD's discoverability requirement: people should instinctively start at Doozers, find an appropriate thread to pull, or get an honest account of what the available knowledge does not establish. A graphical knowledge browser is not required for the first version.

### 7.1 Discovery operations

| Operation | User question | Expected behavior |
|---|---|---|
| **Find** | "What is our guidance for potentially breaking changes?" | Retrieve relevant current kernels and scoped explanations, with links to underlying sources and prior references. |
| **Understand / ask** | "Why is retry safety conditional?" | Provide a concise supported answer, key qualifications and counterevidence, and a route to the reasoning. |
| **Explore / why** | "What else relies on our RDS recovery assumptions?" | Traverse meaningful dependencies, qualifications, evidence and related knowledge, not simply similar words. |
| **Admit absence** | "Do we have an established convention for this?" | Distinguish no supported answer, related but insufficient evidence, contested understanding, and an unindexed/unprocessed source window. |

A possible interface is `search`, `ask`, `explore`, and `why`, exposed consistently through CLI/API and later other clients. Names are provisional; **discovery semantics belong in the engine, presentation belongs in the consumer**.

### 7.2 Answer contract

A substantive answer must be able to provide, when applicable:

- **Current scoped understanding:** What is supported, for which environment/consumer/time, and by which evidence.
- **Qualifications and counterevidence:** Material disagreement, exceptions, uncertainty, and temporal validity must not be silently elided for brevity.
- **Provenance:** Reachable source anchors and the relevant history of transformations; stable references survive compaction and relocation.
- **Exploration hooks:** Closely related kernels, assumptions, dependencies, and original conversations worth following.
- **Coverage/freshness:** Whether connected source material has been durably received but is still being processed; what source scope the answer does and does not cover.

An answer may explicitly decline to make a conclusion. **No search hit** means "nothing relevant found in the indexed/processed corpus under these conditions," not "nothing exists anywhere." Similarity scores alone do not establish truth or conflict resolution; evidence assessment happens after candidate retrieval.

### 7.3 Discovery in an eventually consistent system

Once a connector has acknowledged durable receipt, the incoming source may not yet be reflected in reconciled knowledge or search indexes. Search must not silently represent an older view as fully current when a relevant source stream has known unprocessed material.

Maintain minimal **processing positions or watermarks** by source/consumer as operational metadata. These are not knowledge-status flags. A discovery result can indicate a known freshness gap or optionally surface source-only matches clearly labeled *not yet reconciled*. Actual guarantees depend on source capabilities: a disconnected or lossy upstream system cannot be certified complete merely because our queue is empty.

### 7.4 Discovery fixture expectations

For each multi-round fixture, test: (a) find by fuzzy phrasing; (b) explain current scoped conclusions and their counterevidence; (c) follow a retired reference to current or historical knowledge; (d) follow a dependency; (e) return an honest no-answer for absent knowledge; and (f) distinguish a known reconciliation backlog from true absence.

## 8. Time, provenance, and authority

Differentiate **statement time**, **effective/valid time**, and **ingestion/commit time**. A newly ingested old message is not necessarily newer evidence in the real world. The system should understand contextual limits: environment, deployment, client, release, repository, applicable time, and operator assumptions.

Assertions are not votes, and consensus cannot be fabricated by counting paraphrases. An explicit team expression of agreement, rejection, or changed understanding is evidence of what that team expressed, not a universal truth verdict. Independence and relevance matter as much as recency.

The CNPG fixture is deliberately awkward: published features, a successful drill, and a serious recovery gap can all be true at once. Their apparent contradiction may dissolve when related to the failure modes they actually address.

## 9. Reconciliation as compiler-like passes

```text
Observe sources
  ↓
Interpret assertions, scope, and contextual acts
  ↓
Discover potentially affected kernels and evidence
  ↓
Reconcile support, qualification, contradiction, time, and applicability
  ↓
Propose minimal semantic patch (including NO-OP)
  ↓
Validate provenance, preservation, references, and material context
  ↓
Autonomous atomic commit + reversible history
  ↓
Refresh search indexes, query views, and affected projections
```

### 9.1 Retrieval is not adjudication

Lexical, explicit-link, and embedding-based lookup can nominate relevant knowledge. Vector proximity can show that “RDS failover” and “CNPG failover” are worth comparing; it **cannot** establish that their guarantees are equivalent. Similarly, “code review” and “AI review” are semantically close without implying shared policy or authority.

Small fast models may triage candidates; stronger models may evaluate difficult semantic transformations. This is a replaceable execution hypothesis, not an IR dependency.

### 9.2 Small patch vocabulary

| Operation | Effect |
|---|---|
| `no_op` | No material change to the live understanding |
| `attach_evidence` | Associate relevant source/assertion with existing knowledge |
| `amend` | Revise or qualify current understanding in a defined scope |
| `connect` / `disconnect` | Add/remove a meaningful current relationship |
| `merge` / `split` | Consolidate redundancy or preserve a newly revealed distinction |
| `retire` | Remove obsolete live structure while preserving the appropriate audit/history |
| `surface_conflict` | Preserve incompatible evidence as an explicit qualification, without manufacturing a task |

A patch may contain coordinated operations that commit atomically. This vocabulary describes behavior, not a final API.

### 9.3 Preservation checks

Before an autonomous patch commits, evaluate:

- **Semantic coverage:** What important assertions, caveats, scopes, or exceptions would be lost?
- **Conflict fidelity:** Is apparent disagreement real after considering time, conditions, and referents?
- **Source integrity:** Can claims be traced back to the actual supporting or contrary inputs?
- **Discoverability:** Can prior links, aliases, and imprecise searches still reach the relevant current or historical knowledge?
- **Meaningful change:** Does the patch improve understanding, or merely churn prose?

Referential integrity, deterministic deduplication, transactionality, and anchor checks can be tested mechanically. General natural-language equivalence cannot. When meaningful uncertainty persists, a qualified representation is safer than invented certainty. Reversible history is necessary but does not excuse semantically unsafe commits.

## 10. State, conditions, and autonomy

Do **not** begin with a large knowledge-state enum. Statements of agreement, objection, rejection, and correction are meaningful contextual evidence. “Working,” “settled,” “foggy,” and “contested” may be useful reader-facing descriptions, but should usually be **derived** from evidence and relationships rather than separately maintained authoritative fields.

Knowledge state is not revision history. A prior consensus can remain part of history while the active understanding becomes contested or qualified; VCS tracks the transformations.

**Conflict without an obvious resolution:** retain what is genuinely disputed, present it honestly when relevant, and reconsider opportunistically when new information arrives. Avoid task queues, notification storms, and obligatory human approvals for routine maintenance. A question can be raised within an existing relevant interaction, not automatically turned into work.

**Autonomous commits:** Proceed with well-supported reconciliations, merges, splits, retirements, and no-ops. A material unresolved ambiguity constrains *what can be asserted*, not whether the Doozers may continue useful maintenance elsewhere.

## 11. Canonical, derived, and cached

**Persist what cannot reliably be reconstructed:** authorized source content/references and anchors, meaningful attributed assertions, necessary explicit relationships and scope facts, expressions of agreement/rejection, and a reversible change journal.

**Derive where possible:** current explanations, conflict/fogginess indications, relevance, inferred relationships, reader-facing projections, and query answers.

**Cache for speed:** embeddings, search indexes, projections, graph neighborhoods, and computed conditions, with dependency-aware invalidation. Caches are not independent truth.

Because model judgments may differ across versions, the historical record of committed transformations should include triggering inputs, patch, rationale, and relevant evaluator/model metadata. That audit history does not require duplicated current-state columns.

## 12. Event-driven execution and eventual reconciliation

A stream-oriented architecture fits real-time sources, but **an event transport is not the knowledge graph, the evidence archive, or the orchestrator**. Durable events announce that work or a visible result exists. The reconciler decides whether it affects meaning; many events correctly yield no semantic change. This separation allows Doozers to accept chat messages promptly and improve knowledge asynchronously.

### 12.1 Delivery and consistency contract

- **At-least-once, eventual processing within the system's responsibility:** For each successfully and durably ingested source revision, Doozers retries eligible processing until it succeeds or reaches an observable terminal failure. Acknowledgment of receipt is separate from successful reconciliation.
- **Durable-before-ack:** An upstream connector may acknowledge a message only after source identity, content/reference, and its pending-work record have been durably committed. If the upstream and our store lack a shared transaction, duplicates are expected.
- **Idempotent effects, not exactly-once promises:** Retries may duplicate delivery and computation. Deduplicate using stable `(source, item, revision)` identity and operation/patch identity; protect graph commits and external publications from duplicate effects. Successful replay with no new meaning must not expand the graph or regenerate output gratuitously.
- **Independent progression:** Ingestion, semantic reconciliation, discovery indexing, and projection publication are separate progress markers. Reconciliation and downstream projections may lag. A connector outage or dropped upstream notification may require periodic source polling or backfill when the upstream API permits it.
- **Eventual is conditional:** Bounded time to consistency is not guaranteed during permanent upstream loss, unavailable services, a stuck change, or missing permissions. Lag and failures must be observable rather than hidden.

### 12.2 Logical data flow

```text
chat / documents / APIs / external changes
              │
              ▼
 connector → durable source inbox + pending-work record ── ACK upstream
              │
              ▼
      at-least-once dispatch
              │
              ▼
 candidate retrieval → scoped reconciliation → semantic validation
              │                             └─ valid NO-OP
              ▼
 optimistic version check on affected knowledge neighborhood
              │
     ┌────────┴─────────┐
  conflict/rebase   atomic semantic commit + outgoing event/outbox
                         │
                         ├── refresh discovery indexes/cache
                         ├── refresh affected projections
                         └── record positions, provenance, observability
```

This is a **logical** pipeline, not a commitment to microservices, a broker, or one event per sub-operation. The intake event is distinct from a committed knowledge-change event. Use a **transactional outbox** (or equivalent atomic persistence mechanism) so a committed knowledge update cannot lose its downstream invalidation/publication signal.

### 12.3 Concurrency, ordering, and batching

The source message order may not equal statement/effective time, and independent connectors may deliver out of order. Ingestion must preserve those distinctions. Parallel workers may inspect related kernels, but commits that touch an overlapping knowledge neighborhood must verify the revision they read (optimistic concurrency). If it changed, re-read and re-evaluate the patch; never blindly apply a stale LLM-generated proposal.

Related incoming events may be coalesced into a reconciliation batch without discarding individual source anchors. Incremental recomputation should touch the smallest plausible affected neighborhood while allowing relationships discovered later to expand the scope. A specific processing order is not proof of semantic correctness. We should test **convergence** across input orders and **stability** on re-run; semantic equivalence is an evaluated property, not a guaranteed theorem.

### 12.4 Failure handling without task proliferation

| Failure or replay case | Expected system behavior |
|---|---|
| Crash before acknowledging ingestion | Upstream may redeliver; stable source identity collapses duplicate intake. |
| Crash after graph commit but before worker acknowledgment | Redelivery finds already-applied patch/revision and does not duplicate the semantic effect. |
| Outbox publish failure | Retry publication from committed outbox; affected indexes/projections eventually catch up. |
| Invalid model patch / stale knowledge revision | Validate, rebase/reconcile, record reason; never write conflicting authoritative projections. |
| Poison input or unavailable source | Keep a bounded, observable failure state and retry policy; diagnostics are not a new human/bot assignment queue. |
| Projection export partial failure | Retry idempotently, use versioned/conditional writes, and expose which target is stale. |
| Source API misses notifications | Reconcile against upstream cursor/history when supported; do not claim full coverage otherwise. |

An unresolved **semantic** dispute belongs in the graph as uncertainty, not a durable work item that agents repeatedly wake to "resolve." Operational delivery failures can have retry/dead-letter diagnostics, but that is distinct from maintaining a human task backlog.

### 12.5 Stream versus workflow, and a small first stack

Begin with the **stream processing *contract***, not necessarily a dedicated streaming product. A credible learning slice is **PostgreSQL for canonical/inbox/outbox state with a small worker** and lexical retrieval (vector index optional). This permits atomic durable receipt, revision checks, transactionally committed semantic patches, and durable outgoing signals without introducing distributed infrastructure immediately. A lightweight embedded store remains possible for a purely local interpreter, provided we test the same invariants.

A broker such as **NATS JetStream** could later provide durable independent consumers and replay if throughput, separation, or independent scaling warrants it. Kafka or a durable workflow engine such as Temporal are not prerequisites. Workflows become attractive if reconciliation requires long-lived externally resumed processes; a broker primarily transports events, it does not itself solve semantic conflict or orchestration.

**The source of truth remains authorized evidence + current knowledge + versioned change history.** The event transport, caches, embeddings, search index, and projections are replaceable/rebuildable operational artifacts where feasible. Broker retention is not our long-term evidence survivability policy.

### 12.6 Observability and freshness

Track durable ingest position, oldest unprocessed source age, reconciliation lag, retry counts, failed inputs, stale neighborhood retries, outbox age, discovery-index lag, publication lag, semantic no-op rate, and repeated rewrite/churn rate. Expose enough information for a discovery client to say, "I have an answer as of this processed snapshot, but newer received evidence hasn't yet been reconciled." These are operational freshness signals, not additional epistemic state enumerations.

## 13. Proposed MVP vertical slice

A **single-workspace, end-to-end knowledge-maintenance slice** that ingests Markdown and thread-shaped source events, durably acknowledges intake, reconciles asynchronously, exposes native evidence-backed discovery, and exports at least two useful example projections (handbook Markdown and scoped agent-directive Markdown). Its semantic changes are auditable and reversible. No chat server, bespoke UI, dedicated broker, or agent fleet is required.

1. Load the synthetic retry-safety guide and conversation, retaining source anchors.
2. Introduce the code evidence: scope the broad claim to database writes.
3. Introduce the incident: surface the counterexample without declaring all retries unsafe.
4. Introduce the clarification and manual-replay condition: produce the compact scoped explanation.
5. Re-run the same input and paraphrases: verify idempotence and no unnecessary expansion.
6. Apply a one-word correction with a clear referent, then one with an ambiguous referent.
7. Run the CNPG/RDS fixture: distinguish capabilities, demonstrated operation, workload scope, and unanswered requirements.
8. Run breaking-change and code-review fixtures: distinguish contract, observed behavior, stated practice, and contextual exceptions.
9. Compile the settled portions of each fixture into a human handbook page and a scoped agent directive; verify their semantic consistency, applicability, and traceability.
10. Make a claim contested; verify that the handbook can represent the uncertainty without the directive inventing a mandate.
11. Re-ingest an unchanged generated directive: ensure it is not counted as independent evidence; then ingest a human-edited directive as an attributable new input.
12. Merge apparently duplicative prose; retain the important exception, provenance, and useful old discovery routes.
13. Roll back and replay selected changes; check active and historical projections.
14. Query the knowledge before and after reconciliation: find a fuzzy concept, explain its current scope, traverse its relevant evidence, and verify honest absence.
15. Acknowledge a new message after durable receipt but before reconciliation; confirm that discovery exposes a known freshness gap instead of claiming fully current knowledge.
16. Deliver identical messages twice and out of order; crash/restart a worker at ingest, semantic commit, and outbox dispatch boundaries; verify eventual idempotent results.
17. Reconcile overlapping evidence concurrently; reject/rebase stale patches and test whether different event orders converge on materially equivalent understanding.
18. Update knowledge that drives both discovery and exported guidance; confirm that indexes/projections catch up independently and do not self-corroborate.

A **plausible first implementation**, not a locked stack: PostgreSQL with durable source inbox, semantic change journal, transactional outbox, and a small worker; source snapshots/references; lexical retrieval initially and vectors later if they improve retrieval. For purely local IR experiments, an embedded transactional database is still a reasonable substitute. No dedicated graph service, stream broker, workflow platform, or agent fleet is justified yet.

### Minimal observability

Record source spans inspected, candidate kernels, accepted/rejected patch operations, evidence cited, preservation checks, changes committed, cache invalidations, runtime, and model cost. Also record source delivery identity, retry/processing positions, outbox/projection lag, stale commit retries, and discovery freshness gaps. Measure substantive semantic churn rather than document volume alone.

## 14. Evaluation and failure criteria

Test multi-round transformations against expected outcomes and against a naive append-only summarization baseline. The test set should include expected *nonchanges* and unacceptable simplifications.

| Fixture | Required behavior | Catastrophic or material failure |
|---|---|---|
| Retry safety | Separate DB-write deduplication from notification side effects; preserve manual-replay caveat | Blanket “safe/unsafe” answer, lost incident, lost scope |
| CNPG vs RDS | Preserve conditional, workload-specific assessment and evidence gaps | Universal winner, inferred decision, conflated failure modes |
| Breaking changes | Track producer/consumer assumptions, contract scopes, and migration sequence | “Additive = safe everywhere,” lost consumer exception |
| Code review | Distinguish policy, practice, proposals, AI assistance, and high-risk exceptions | Tool usage presented as team policy or blanket consensus |
| One-word reversal | Use reply context to update meaning or retain ambiguity | Dismissed as noise or applied to wrong referent |
| Duplicate with exception | Compact shared claim while preserving nuance | Exception disappears during merge |
| Corroboration/echo | Correctly identify independent sources | Two echoes counted as independent support |
| Repeated ingestion | No duplicate semantic effects or gratuitous rewrites | Unbounded node/document churn |
| Conflict without settlement | Expose uncertainty and revisit as evidence arrives | Hallucinated settlement or generated task queue |
| Merge/retire/history | Retain useful discovery paths and provenance | Orphaned links or unrecoverable explanation |
| Unknown answer | Admit no supported answer was found | Invented facts or unearned claim of global absence |
| Handbook/directive parity | Different presentation, same supported meaning and scope | Handbook says one thing while agent instructions prescribe another |
| Contested guidance | Represent uncertainty; emit only justified, bounded instructions | Provisional speculation becomes mandatory agent policy |
| Projection feedback loop | Generated text remains derived; attributed human edits become new input | Self-corroborating evidence inflation or clobbered manual content |
| Directive publication | Use existing repository controls appropriate to behavior-changing impact | Silent high-impact behavioral rewrite or proliferating human task queues |
| Native discovery | Find, understand, explore; cite evidence and follow old references | Only keyword dumps, unsupported answers, lost exploratory links |
| Honest absence | Distinguish no knowledge, insufficient evidence, conflict, and received-but-unprocessed inputs | Hallucinated answer or false claim of completeness |
| At-least-once ingestion | Duplicates and out-of-order messages converge without duplicated semantic effects | Duplicate nodes/projections or silently lost acknowledged sources |
| Durable commit/outbox | Crash recovery eventually refreshes downstream indexes and projections | Committed knowledge invisible indefinitely because notification was lost |
| Concurrent reconciliation | Stale patches rebase/validate against changed neighborhoods | Last writer silently destroys a newer assertion or caveat |
| Eventual freshness | Reader sees processed snapshot/lag when source events remain pending | Stale current answer presented without qualification |
| Nonengineering procedure | Handle time/condition-specific guidance | Engineering-specific schema distorts ordinary knowledge |

**Primary goal:** Higher quality, more dependable understanding with minimal contributor effort. Node count, document count, and graph density are supporting diagnostics, not optimization targets by themselves.

Set numerical thresholds after constructing a human-reviewed fixture corpus. Loss of counterevidence, invented consensus, broken historical links, and unsupported attribution should block release regardless of compression ratio.

## 15. Open engineering questions

1. **Expressiveness:** How much structure helps reliable reasoning without requiring brittle triples or a universal ontology?
2. **Continuity:** How should references survive renaming, split, consolidation, and retirement, before choosing physical IDs?
3. **Relationship provenance:** When is an inferred connection sufficient for a derived view, and when should it become durable canonical knowledge?
4. **Temporal and conditional scope:** How should validity depend on environment, workload, risk tolerance, and effective dates?
5. **Semantic guardrails:** Which transformations may commit automatically when full equivalence cannot be proven?
6. **Source dependence:** How do we distinguish independent corroboration from repeated citation of one source?
7. **Erasure:** How do deletion/privacy obligations propagate through history, caches, and derived knowledge?
8. **Convergence:** What constitutes a stable normal form when natural language and model outputs are nondeterministic?
9. **Policy versus practice:** How do we reconcile formal guidance, observed behavior, and disputed conventions without inventing authority?
10. **Evaluation:** What fixture diversity and human review yield credible measures of survivability, discovery, and semantic accuracy?
11. **Directive compilation:** Which kinds of understanding justify an imperative agent instruction, versus a handbook explanation or no output?
12. **Projection ownership:** How do generated and manually authored document regions coexist, and how do external edits reenter reconciliation without circular evidence?
13. **Safe publication:** Which directive changes can publish automatically under existing repository controls, and which must follow the repository's established review practices?
14. **Discovery contract:** Which relevance signals and exploration operations yield useful answers without over-answering or inventing knowledge?
15. **Freshness boundaries:** How much unprocessed input can we reveal as a clearly labeled source-only result without contaminating the reconciled view?
16. **Reconciliation scheduling:** When should we process individual events, coalesce source batches, or prioritize high-impact neighborhoods?
17. **Replay and convergence:** How do we compare semantic equivalence across nondeterministic optimization runs and out-of-order arrivals?
18. **Transport scaling:** What observed bottleneck would justify adding JetStream or a durable workflow platform beyond an inbox/outbox worker?
19. **Operational retention:** Which source positions, inbox/outbox records, and diagnostics may be pruned while preserving knowledge and audit survivability?

## 16. Decisions and changes in v0.4

**Retained:** Source/evidence/conclusion separation, primacy of relationships, minimal independently maintained truth, explicit uncertainty, autonomous reversible reconciliation, semantic compaction, and projections that cannot become circular evidence. The CNPG/RDS, breaking-change, code-review, and retry-safety cases remain **synthetic fixtures**, not claims about any team.

**Added:**

- **Native discovery** is a first-class engine contract: find, understand, explore, explain, and honestly report absent/insufficient knowledge; expose provenance and relevant freshness information.
- **Contextual guidance** is potentially instructional when it might change a consumer's outcome, without converting all knowledge into unconditional commands. Handbooks and agent directives are examples, not an exhaustive set of consumers.
- **Event-driven eventual processing** with durable-before-ack ingestion, at-least-once redelivery, idempotent semantic effects, transactional commits/outbox, optimistic concurrency, safe replay, and independently catch-up-able discovery/projection outputs.
- **Freshness/coverage** are operational facts reported to consumers, not independently maintained epistemic status. An unreconciled chat message must not be hidden behind an unjustified claim of current knowledge.
- **Learning-first infrastructure:** a Postgres inbox/outbox and worker is an appealing first implementation; JetStream and workflow engines remain contingent on observed need. The stream contract does not force a stream product.

**Still deferred:** Final physical schema, graph persistence, model/provider choices, dedicated broker, sophisticated workflow engine, multiuser deployment, publication mechanics, and exact consumer interface shape.

### Recommended next step

**Build the smallest vertical slice that goes all the way around the loop.** Start with a machine-readable, multi-round fixture corpus and expected semantic/negative outcomes. Add a durable source inbox, idempotent reconcile/commit, source-backed `search`/`ask`/`explore`, and one or two projections. Test duplicates, out-of-order arrivals, crashing immediately after commit, concurrent related patches, and a known reconciliation backlog. Measure trust/fidelity before optimizing throughput or introducing additional services.

---

**PRD alignment:** The EDD retains survivability → discoverability → compactness, evidence-based understanding, autonomy without artificial human task queues, minimal state, semantic compaction, and user trust as the success criterion. It now addresses both engine responsibilities explicitly: **maintain understanding** and **make understanding accessible**. Event transport is operational infrastructure, never independent truth.
