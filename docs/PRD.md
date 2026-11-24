# Doozers — Product Requirements Document

**Version:** 0.7

**Date:** November 24, 2026

**Status:** Working draft

**Project:** Doozers (working name)

**Model:** Open source, self-hostable, extensible

## 1. Executive summary

Doozers is an **autonomous, continuous knowledge-maintenance engine**. It observes conversations, documents, and other artifacts, then reconciles new information with an existing body of shared understanding. It improves the **live representation** by amending, connecting, consolidating, qualifying, and retiring knowledge while keeping its evidence and history recoverable.

Its output is **not another summary or document**. It is a knowledge base that becomes more coherent, discoverable, and trustworthy as people work, without demanding that they become documentation maintainers.

**Working metaphor: an optimizing compiler for collective knowledge.** A compiler simplifies and reorganizes an intermediate representation while preserving program behavior. Doozers should similarly simplify a representation of understanding while preserving its *material meaning*: claims, qualifiers, uncertainty, temporal scope, contradictions, and traceable evidence. Its transformations are **semantic reconciliation**, not merely text compression.

This is an analogy, not a claim that human understanding admits exact algebraic equivalence or mechanically provable correctness. Knowledge is incomplete, contextual, contested, and revisable. The system must make uncertainty visible rather than claim formal proof it does not have.

**Product thesis:** New information should usually improve existing understanding, not create another independent place where an increasingly divergent version of the truth lives. Routine maintenance is autonomous and reversible; genuinely unresolved ambiguity can remain unresolved without producing a human task.

**Priority order:** (1) **survivability** of meaningful knowledge; (2) **discoverability**; (3) **compactness and terseness as far as reasonably parseable**. No meaningful change is too small. The ultimate outcome is trust: people naturally consult Doozers first, can contribute without friction, and take its usefulness for granted.

## 2. Problem

Collective knowledge grows by accretion but rarely receives the equivalent of refactoring. Conversations introduce new facts, exceptions, retractions, decisions, and corrections; documentation is usually added rather than reconciled. Related explanations split apart, stale guidance survives beside newer guidance, and the cost of determining what the team currently understands rises over time.

Conventional summarization can accelerate this decay by generating additional prose without updating or retiring what it overlaps. Excessively conservative systems produce review backlogs and competing sources of truth. Overconfident systems silently flatten disagreements or erase qualifications. Both destroy trust.

The core problem is **coherence decay**: the number of artifacts increases while useful, defensible understanding does not improve proportionally.

Doozers must recognize that **“Stop”** can invalidate a plan, while forty messages of chatter can legitimately result in no knowledge change. It must notice changed meaning, not reward volume.

## 3. Vision and product boundaries

**Vision:** A trusted place to preserve, find, and contribute shared understanding. People can search vaguely and find a thread worth pulling, or get an honest account of what the system does not know. The maintenance work beneath the surface becomes unremarkable.

**Core job:** “As we learn, disagree, revise, and sometimes forget, keep what we know coherent and findable without turning knowledge upkeep into another job.”

### Goals

1. **Survive transformation.** Preserve material meaning, context, and retrievable evidence through normal revision, merging, pruning, and representation changes; support authorized deletion separately.
2. **Remain discoverable.** Make current understanding accessible from imperfect queries, relevant relationships, and source-linked explanations; acknowledge genuine absence and incomplete coverage.
3. **Continuously reconcile.** React to changes of meaning, including tiny signals, newly relevant evidence, changing circumstances, and reopened conclusions.
4. **Minimize representational complexity.** Prefer an edit, meaningful edge, consolidation, or no-op over proliferating nodes, links, pages, and rival accounts.
5. **Operate autonomously.** Perform justified maintenance without constant human approval, with an inspectable, reversible history.
6. **Respect evidence and disagreement.** Reflect what the team knows, claims, and questions; neither decide for the team nor manufacture consensus.
7. **Tolerate uncertainty.** Let unclear or contested knowledge persist and resolve opportunistically; uncertainty is not automatically a ticket.
8. **Stay interoperable.** Offer open exports and replaceable source adapters, models, and projections without requiring a particular chat, wiki, or database.

### Non-goals

- Replacing Slack, Discord, forums, or a document editor.
- Enforcing organizational decisions or resolving every disagreement.
- Requiring human approval for all semantic edits or creating perpetual human/agent task queues.
- Preserving every message as an active knowledge item.
- Proving mathematical equivalence between natural-language statements.
- Building a universal ontology, a custom graph database, or a distributed agent fleet before the behavior is validated.
- Implementing production multi-tenant permissions and federation in the MVP.

The system must be useful for research, community knowledge, procedures, creative collaboration, and other domains, **not just ADRs or software engineering**.

## 4. Users and representative experiences

**Contributor:** Speaks or writes naturally; useful information enters the maintained corpus without a separate authoring ritual.

**Reader:** Searches fuzzily, follows a useful thread, sees meaningful caveats and uncertainty, and can inspect supporting evidence.

**Knowledge steward:** Wants the live corpus to stay coherent without tending to an endless review inbox.

**Participant in a conflict:** Encounters an uncertainty in the context where it matters and can clarify it, without being assigned an artificial backlog item.

**Integrator:** Connects familiar information sources and projects current knowledge to existing tools.

### Representative scenarios

**Routine simplification.** Three guides repeat the same instruction with slightly different wording. Doozers maintains one coherent explanation, redirects relevant access paths, and preserves source history. It should not merely produce a fourth summary.

**Evidence-based update.** James says Project A ships December 12. Later Steven says the date has **moved** to December 20, and Sarah confirms it. The current understanding becomes “Scheduled for December 20,” with the earlier plan and the change in schedule recoverable. If Steven merely says “December 20” without context, the apparent conflict remains visible until the evidence supports interpreting it as a change.

**Tiny, consequential input.** A one-word “Stop” in the right thread suspends or alters an otherwise extensive explanation. Doozers interprets its referent and scope rather than ignoring it as too short.

**Disagreement without obligation.** Two observations cannot yet be reconciled. The affected explanation is visibly qualified or contested. No ticket is opened. When relevant material arrives later, Doozers attempts reconciliation again; a contextual question is appropriate only if someone is already dealing with that uncertainty or intervention is genuinely necessary.

**Successful no-op.** Forty messages of banter do not change any meaningful knowledge, relationship, or evidentiary support. The live corpus stays unchanged.

**Trustworthy retrieval.** A reader asks a vague question and follows an indirect relation to a relevant explanation. If nothing relevant is present, Doozers says so within the limits of what it has indexed and can access.

## 5. Product principles

These are product obligations, **not prescriptions** for schemas, embedding algorithms, or numbers of agents.

1. **No meaningful change is too small.** Impact comes from context, not token count.
2. **Survivability before compactness.** A shorter representation is a regression if it loses an important exception, disagreement, scope, or evidentiary path.
3. **Discoverability before compactness.** Compaction must preserve useful routes to meaning, not merely reduce a graph's size.
4. **Semantic simplification, not summarization.** Seek the simplest representation that retains the material understanding supported by available evidence.
5. **Evidence is relational.** Information is evidence *for something* in a given context; conclusions depend on how sources, claims, and relationships bear on a question.
6. **Reflect, don't decide.** Team language, actions, and evidence may establish a provisional or settled understanding; silence and model confidence are not agreement.
7. **New input reopens old understanding.** Recency earns attention, not automatic correctness. Recognize changes of circumstance and explicit contradictions.
8. **Autonomy by default.** Unnecessary approval gates lead to stagnation and proliferation. Routine edits should happen, with auditability and reversibility.
9. **Uncertainty is not a task.** Foggy or contested understanding can persist without queues, notifications, or demanded intervention; surface it when relevant.
10. **Minimal state, rich relationships.** Store only independently necessary truth; derive conditions and cache them when useful, rather than proliferating maintained status fields.
11. **Meaningful effect or no-op.** A source need not create knowledge unless it changes an assertion, interpretation, relationship, evidence, or another meaningful part of the maintained understanding.
12. **The live corpus is not a museum.** Obsolete structure leaves current navigation while legitimate history remains accessible.
13. **Trust is the product.** A quiet, useful, low-friction system is more successful than a visibly busy one.

## 6. Conceptual model: evidence-based understanding

The graph is a useful mental model, **not a commitment** to graph storage, a fixed ontology, or a particular smallest unit of knowledge.

| Concept | Product-level meaning |
|---|---|
| **Source / observation** | What someone said, wrote, measured, changed, or documented, with available origin, context, and time. |
| **Information / assertion** | A claim or value communicated by a source, not automatically an established fact. |
| **Knowledge kernel** | A question, subject, or proposition around which understanding accumulates, e.g., “What is Project A's release date?”; term provisional. |
| **Evidence relationship** | How information supports, contradicts, qualifies, supersedes, or otherwise bears on a claim or question, including context and time. |
| **Current understanding / conclusion** | The best justified interpretation currently exposed to readers; may be provisional, qualified, or unresolved. |
| **Live representation** | The active, compact, navigable body of understanding and its useful relationships. |
| **Historical record / VCS** | A separate account of what changed, when, why, and on what evidence, allowing reconstruction and rollback. |
| **Projection** | Markdown, a wiki page, an LLP-linked explanation, search answer, or other view of maintained understanding. |

### Evidence, context, and conclusions

Inspired by the discipline of evidence-based historical and genealogical research associated with **Elizabeth Shown Mills**, distinguish the source and its information from how that information becomes *evidence relative to a question*, and from the conclusion drawn by correlating it with other evidence.

An assertion can support one conclusion, qualify another, and be irrelevant to a third. Counting supporting statements is not the same as weighing independent evidence. A source's age, specificity, provenance, reliability, and temporal scope all matter; newer is not necessarily truer.

A **knowledge kernel** need not already contain a settled answer. It can organize competing assertions while allowing the current conclusion to emerge from their relationships and context. An explicit, human-expressed conclusion is itself meaningful information that must not be mistaken for an automatically inferred result.

### Provenance and interoperability

Preserve the distinction between a source version, an assertion about it, the
activity that changed the maintained understanding, and a derived projection.
Where responsible people, organizations, or software actors are known, retain
attribution separately from what authority or evidentiary weight they have.
Unknown identities and times must remain unknown. A citation or traceable lineage
does not prove truth, agreement, independent corroboration, or semantic equivalence.

Use open provenance interchange where it helps explain and recover changes;
W3C PROV is the current engineering vocabulary under evaluation. It must not
become a second independently maintained knowledge base or force the domain
model into a universal ontology. Removing an assertion from current navigation
must not imply that its historical record or source ceased to exist.

### Minimal stored state, derived conditions

- **Canonical or independently necessary:** sources and their context; assertions; material relationships; explicit expressions of agreement, correction, rejection, or uncertainty; temporal facts; and historical edits.
- **Derived:** contested/foggy indications, relevance, certain confidence assessments, current interpretations, and other conditions that can be recovered from the underlying information.
- **Cached:** derived values or projections retained for speed, with reliable invalidation/recomputation.

**State and status, if both are needed, answer different questions:** a minimal *state* may describe the lifecycle of understanding (e.g., working versus settled), while a *status* describes a condition inferred from evidence (e.g., contested or foggy). This distinction is a hypothesis to test, **not an invitation to define a large enum or workflow**. The graph and source context should carry most of the nuance. VCS history is not knowledge state.

The presence of contradictory edges may suggest a contested condition. The absence of such edges does **not** prove consensus, completeness, or correctness. Apparent contradiction may reflect differing dates, scopes, or referents.

### Semantic vectors are an aid, not an arbiter

Embedding vectors may help find passages or claims that concern the same topic despite different wording. They do **not** mathematically establish that two claims agree, contradict, or can be safely merged. Candidate discovery and semantic adjudication are different operations.

## 7. Continuous workflow: the knowledge optimizer

The compiler analogy suggests a useful sequence of behaviors, without requiring a compiler implementation.

Maintenance may be triggered by new evidence **or by an opportunity to improve existing understanding without new source intake**. Source-free consolidation must not invent a receipt, add corroboration, or erase original context. Conversely, no-op is legitimate when no useful, justified change is available; lack of new sources alone is not its justification.

1. **Observe and preserve context.** Capture incoming information, origin, time, and enough conversational context to interpret short, consequential replies.
2. **Locate relevant understanding.** Use explicit links, lexical retrieval, semantic similarity, and context to find what may be affected.
3. **Interpret as evidence.** Identify assertions, qualifiers, changes of circumstance, support, conflict, and whether anything meaningful has changed.
4. **Propose semantic simplifications.** Prefer a no-op, amendment, link correction, consolidation, or retirement; create a new knowledge area only when it truly adds independent understanding.
5. **Check preservation constraints.** Ask whether the transformation would lose material caveats, temporal meaning, contradictions, provenance, or discoverability; reject unsafe simplifications.
6. **Commit justified changes autonomously.** Update the live representation and projections, recording an attributable, reversible change set.
7. **Carry unresolved ambiguity honestly.** Make affected understanding visibly qualified; revisit opportunistically with later input. Do not manufacture a task queue.
8. **Recompute affected dependencies.** Revisit conclusions or projections affected by changed upstream information, without rewriting everything indiscriminately.
9. **Check for convergence and churn.** Repeated equivalent inputs should tend toward the same useful representation, not trigger endless rewrites or oscillation.

### Illustrative optimization analogies

| Compiler technique | Candidate knowledge-maintenance analogue | Necessary caution |
|---|---|---|
| **Common subexpression elimination** | Consolidate truly redundant explanations, keeping all useful access paths. | Similar wording may conceal different scope or exceptions. |
| **Canonicalization** | Bring equivalent expressions of a concept into a coherent current form. | Do not erase a meaningful disagreement or variant. |
| **Constant folding** | Resolve straightforward, well-supported relationships into a simpler current explanation. | “Settled” may be contextual, provisional, or time-bound. |
| **Dead-code elimination** | Retire obsolete live knowledge and invalid current links. | Preserve material history, provenance, and intentional access paths. |
| **Incremental recomputation** | Reevaluate only affected dependent understanding when new evidence arrives. | Dependency links must be sufficiently reliable; missed impacts matter. |
| **Optimization validation** | Check that simplification preserves the supported meaning and discoverability. | Natural-language equivalence is defeasible, not a formal theorem. |

**Key distinction:** The objective is not to literally flatten embedding vectors. It is to simplify *the representation of understanding* while preserving what can justifiably be recovered from the evidence. Some new evidence should make the active knowledge **more complex** because a previously hidden exception or disagreement has become important.

### Semantic preservation contract

A compaction is acceptable only when, within the evaluated context, readers can still recover the material:

- **Current conclusions and uncertainty:** what seems true, provisional, disputed, or unknown.
- **Scope and time:** when and under what circumstances a statement applies, and what changed.
- **Qualifications and counterevidence:** exceptions, objections, and significant unresolved disagreement.
- **Provenance and rationale:** the sources and relationships needed to explain *why* the current understanding is justified.
- **Discovery paths:** ways to reach the understanding from relevant related topics, earlier references, and fuzzy questions.

History need not crowd the live view; a reader should be able to deliberately inspect it. Authorized deletion is a separate requirement and may take precedence over ordinary retention.

**Preserve distinctions, not a prescribed layout.** A material restriction need not remain a separate claim, node, or paragraph if it is explicit in the maintained explanation, reaches the relevant consumer, and retains its source and historical recovery paths. For example, the restriction on extending the documented manual-replay mitigation to automatic retries may be folded into the main retry explanation. Integration must not turn that scoped restriction into a blanket claim that all automatic retries are unsafe. Neither separation nor consolidation is automatically better; assess meaning, useful access, and unnecessary complexity rather than matching an authored node count.

## 8. Functional requirements

| ID | Priority | Requirement |
|---|---|---|
| FR-01 | P0 | Ingest documents and conversation exports with source identity, origin, temporal context, and interpretable references to prior messages. |
| FR-02 | P0 | Represent a navigable body of current understanding connected to its supporting, qualifying, and conflicting evidence, without fixing node size or storage technology. |
| FR-03 | P0 | Distinguish observations/assertions from conclusions; support a question or proposition with competing answers. |
| FR-04 | P0 | Discover potentially equivalent, related, and conflicting knowledge through lexical, semantic, and explicit relationships, without interpreting embedding similarity as proof. |
| FR-05 | P0 | Perform autonomous update, merge, link correction, retirement, qualification, and **no-op** operations, including maintenance of existing understanding without new source intake; prefer reconciliation over new artifacts. |
| FR-06 | P0 | Preserve material meaning, temporal scope, exceptions, disagreement, source paths, and discoverability across simplifications. |
| FR-07 | P0 | Explain current knowledge and its evidence, show what changed, and support inspection and rollback of autonomous edits. |
| FR-08 | P0 | Surface genuine irreconcilable conflicts or fogginess where relevant; tolerate unresolved conditions without generating default human/agent task queues. |
| FR-09 | P0 | Keep the current representation compact and navigable while allowing obsolete nodes/edges to leave the live view and remain accessible through legitimate history. |
| FR-10 | P0 | Support fuzzy retrieval, related-topic navigation, and appropriately qualified no-result behavior. |
| FR-11 | P0 | Test small consequential inputs, noisy no-ops, repeated rounds of compaction, chronology, caveat retention, and reconciliation behavior. |
| FR-12 | P0 | Detect or prevent gratuitous oscillation, duplicate generation, and non-idempotent rewrites on unchanged or equivalent input. |
| FR-13 | P1 | Reconsider downstream understanding when meaningful upstream evidence or relationships change. |
| FR-14 | P1 | Derive and optionally cache conditions such as contested/foggy instead of maintaining redundant current-truth fields wherever reliable derivation is possible. |
| FR-15 | P1 | Support continuous operation through incremental source adapters, while avoiding a required proprietary chat or wiki interface. |
| FR-16 | Later | Support bidirectional LLP-style links, richer projections, and developer integrations. |
| FR-17 | Later | Support source-aware multiuser permissions and permission-safe derivations. |

### Autonomy and intercession

**Default:** Doozers performs justified routine changes and keeps an understandable audit trail. VCS makes corrections possible but is not permission to make reckless semantic edits.

**When uncertain:** The system can leave an affected conclusion qualified or contested and continue. It may resolve the issue from future input. Human intercession is contextual, proportionate, and exceptional; it should not be implemented as a new backlog by default.

**When conflicting:** Doozers must not silently publish mutually exclusive claims as settled or invent a resolution. Its response can be to re-scope the claims temporally, flag uncertainty, or ask an appropriate question in an already active context.

### No-op, pruning, and deletion

No-op means no meaningful change to current knowledge, relationships, or evidentiary support. Source-retention policy is separate. Pruning removes obsolete live structure; audit history remains available subject to legitimate deletion. Deliberate source erasure and its implications for derived knowledge require explicit policy.

## 9. MVP: autonomous local reconciliation workbench

The MVP is **single-workspace, local, and knowledge-first**. It need not be a chat service, document editor, cloud orchestration platform, or multi-agent spectacle.

Given an initial Markdown/text corpus and sequential batches of conversation/documentary inputs, a user can:

1. Ingest material with preserved context, source anchors, and dates.
2. Run semantic reconciliation; clear updates, merges, link changes, and retirement occur without per-change approvals.
3. Examine the current compact knowledge view and follow explanations back to evidence.
4. Inspect an audit trail and roll back a harmful transformation.
5. Encounter a legible unresolved conflict without receiving an automatic task assignment.
6. Search vaguely and get useful paths, or an honest qualified no-result.
7. Execute a repeatable multi-round fixture suite and compare against an append-only summarization baseline.

### Required evaluation fixtures

- **Release-date evolution:** Initial December 12 plan, explicit move to December 20, independent confirmation; preserve both current date and change history.
- **Ambiguous contradiction:** Two incompatible dates with no evidence of rescheduling; retain disagreement rather than silently preferring the newest.
- **Tiny reversal:** A context-dependent “Stop,” “No,” or “We should rethink this” meaningfully alters current understanding.
- **No-op noise:** Long irrelevant discussion leaves the live representation unchanged.
- **Duplicate collapse:** Several explanations reduce to one current explanation without breaking routes to it.
- **Exception protection:** Two nearly identical procedures contain one consequential exception that must survive consolidation.
- **Dormant uncertainty:** A contested point remains unresolved without task generation, then resolves when later evidence appears.
- **Repeated input:** Reprocessing equivalent material does not create repeated changes or churning prose.
- **Trustworthy absence:** A user asks about something not supported by the indexed corpus; Doozers declines to invent an answer.

## 10. Success criteria and evaluation

**North star: earned trust.** People rely on Doozers to keep, find, and improve understanding with minimal friction. A smaller corpus, a denser graph, or more model activity is not success by itself.

Evaluate with evolving, human-reviewed example corpora and realistic reader questions. Establish numerical thresholds from an initial benchmark instead of inventing them now. Treat catastrophic loss of a caveat or unsupported certainty as more severe than a missed minor merge.

| Dimension | What good looks like |
|---|---|
| **Semantic preservation** | Relevant conclusions, caveats, temporal scope, and counterevidence survive repeated simplifications. |
| **Evidence traceability** | Users can follow a current claim to the observations and reasoning that support or challenge it. |
| **Discoverability** | Indirect and fuzzy queries reveal a meaningful thread without requiring precise naming. |
| **Honest absence** | The system distinguishes “nothing relevant indexed here” from an unsupported claim of universal absence. |
| **Safe compaction** | Redundancy falls without measurable loss of material meaning or search access. |
| **Conflict fidelity** | Genuine incompatible claims remain visible; contextual changes are not mistaken for contradiction. |
| **No-op precision** | Irrelevant chatter does not cause pointless corpus growth. |
| **Small-signal sensitivity** | Short statements can cause appropriately scoped, consequential changes. |
| **Autonomy with low friction** | Routine changes occur without review queues; unnecessary prompts and requests are rare. |
| **Convergence / stability** | Repeated inputs and maintenance cycles do not create excessive churn, duplication, or oscillation. |
| **Auditability** | Harmful transformations can be understood and reversed without cluttering active knowledge. |
| **User trust** | In realistic tasks, people elect to consult and contribute to the system, and understand the limits of its confidence. |

Measure **quality-adjusted compactness**, not compression ratio alone: preserving one vital exception is worth more than deleting ten paragraphs. Compare observed behavior against append-only and naïve summarization baselines. Include counterexamples designed to trick overly aggressive merging.

Evaluate the **warrant for change or no-op** separately from mechanical validity. Fewer nodes, preserved citation IDs, successful application, and successful rollback do not establish semantic preservation. A well-formed no-op is not automatically useful, and an alternative meaning-preserving layout is not wrong merely because it differs from an authored target. Include both already-coherent views and views with avoidable redundancy so evaluation does not reward either compulsory rewriting or blanket conservatism. Human review of experimental meanings is evaluation work, not a requirement to approve every routine product edit.

### Longitudinal public corpora and discussion context

Complement synthetic controls with curated, intentionally public standards
lineages: original specifications, successive drafts, review comments, feedback,
conversations, and resulting released documents. These provide real cases of
scope refinement, retained disagreement, adopted changes, and abandoned proposals.
Evaluate the maintained understanding at successive cutoffs, not just a summary
of the final document. Ask separately what was proposed, what published guidance
applied, what remained unresolved, and why an interpretation changed when the
available evidence establishes that reason.

A newer draft does not automatically override a published standard. Publication
is later evidence with release-specific normative scope, not a truth oracle;
obsoleting a document does not make every earlier assertion false. Issue closure,
PR submission, silence, or repeated comments do not establish adoption or consensus.
A proposal omitted from a release is not thereby universally prohibited.

Freeze source versions and reader questions before a run. Withhold future
revisions, later edits, outcomes, and evaluator references from earlier cutoffs.
If the historically visible bytes or reply context cannot be recovered, record
that limitation rather than fabricate a complete conversation. Keep development
families separate from held-out evaluation; human-reviewed references are
provisional evaluation evidence, not a universal semantic oracle. Neither
standards replay nor a provenance graph proves general autonomous correctness.

## 11. Architecture hypotheses (deliberately non-binding)

The product suggests potential components, but no stack decision is made here:

- **Fast, inexpensive models** for triage, novelty detection, candidate ranking, and low-risk maintenance; stronger reasoning for difficult reconciliation. Input length alone must not determine consequence.
- **Lexical and semantic retrieval**, possibly with a vector index, for candidate discovery and fuzzy finding; *not* for mathematical proof of agreement or contradiction.
- **Durable source/artifact storage**, perhaps blobs, to preserve evidence, audit context, and projections within retention policy.
- **Minimal canonical state plus derived views**; a very small lifecycle mechanism, if necessary, distinct from inferred uncertainty/contestation and separate from revision history.
- **A VCS or equivalent journal** for reconstructable, attributable changes, rollback, and historical inspection.
- **An incremental orchestrator** for locating affected understanding, validating maintenance, and revisiting dependencies; not an agent task factory.
- **A relationship representation** with sufficient provenance, scope, and temporal meaning; no presumed requirement for a dedicated graph database.
- **Open projections and LLP-style references** that can link current explanations, source material, and external artifacts without making any document canonical.
- **Standards-aligned provenance interchange**, currently W3C PROV, derived from existing records rather than a parallel canonical graph; domain semantics, storage, and authority assessment remain separate.

The compiler metaphor suggests transformations, validation, and incremental dependency management, but **does not force** an AST, rewrite-rule engine, theorem prover, or compiler architecture. Validate behavior first.

## 12. Safety, privacy, and trust

- Ingested data may be private. Sources and model transmission must respect explicit operator choice; the single-workspace MVP has one trust boundary.
- Source text is untrusted input, never a privileged instruction to the maintenance engine.
- Public availability is not redistribution permission or model-transmission approval. Review rights, applicable notices/attribution, privacy, and historical visibility before incorporating public discussions or excerpts; minimize participant/contact data without erasing material context. Third-party text retains its own terms rather than inheriting the project license.
- Autonomous changes are attributable, inspectable, and reversible; tests should include failures that arise only after multiple rounds of compaction.
- Preserve evidence and historical meaning under ordinary maintenance while providing explicit, policy-governed deletion and addressing derived content after removal.
- Do not infer team agreement from silence, repeated paraphrases, model confidence, or a lack of contradiction edges.
- Do not present a contested or poorly supported claim as settled guidance without qualification.
- Negative search must indicate the limits of indexed/accessible material.
- Avoid automatic interventions that expose private context to a broader audience; multiuser permission-safe derivation is out of scope until designed.

## 13. Primary risks and mitigations

| Risk | Mitigation |
|---|---|
| **Over-compaction / semantic loss** | Material-meaning preservation tests, exception and temporal fixtures, source-linked audits, rollback. |
| **Under-compaction / proliferation** | Default to update/link/merge/no-op; measure redundant active assertions and pages. |
| **False equivalence from vectors** | Use embeddings for candidate retrieval; semantically inspect actual claims, context, and evidence before merging. |
| **Stale or duplicated derived truth** | Prefer derivation and invalidatable caches over separately maintained status fields. |
| **False consensus** | Preserve expressed positions and counterevidence; never treat silence as approval. |
| **Recency masquerading as truth** | Distinguish changed circumstances from unresolved disagreement; weigh source quality and scope. |
| **Uncertainty becoming a backlog** | Permit dormant contested/foggy conditions; contextual questions only when useful. |
| **Endless agent churn** | Convergence, idempotence, no-op, and change-budget evaluations. |
| **Broken discovery after merging** | Preserve meaningful references and navigation paths to surviving understanding. |
| **Misleading negative results** | Expose search coverage and test absent-answer cases. |
| **Privacy leakage / deletion gaps** | Explicit source-retention, removal, and permission-boundary policies. |

## 14. Phased delivery

**Phase 0 — Corpus and benchmark.** Assemble small evolving knowledge corpora with duplicate explanations, hidden exceptions, changing conclusions, temporal scope, one-word reversals, contradictory assertions, and absent answers. Retain synthetic controls and add curated public standards/discussion lineages with reviewed rights, source-version cutoffs, and uncertainty about unavailable history. Define expected preserved meaning and forbidden transformations before model evaluation.

**Phase 1 — Autonomous local optimizer.** Implement ingest, candidate discovery, evidence-aware reconciliation, safe automatic transformations, minimal representation, inspectable VCS history, unresolved-condition handling, export, and retrieval evaluation.

**Phase 2 — Continuous maintenance.** Incremental source adapters, dependency revisits, observability, convergence improvement, contextual intercession, and robust projections.

**Phase 3 — Ecosystem.** LLP-style bidirectional links, richer interfaces, open integrations, and permission-safe multiuser collaboration.

Advance when understanding remains coherent, discoverable, and trustworthy across successive rounds, **not** when the system adds more moving parts.

**Evidence at v0.7:** The local workbench applies authored maintenance plans, preserves historical access, and exercises prefix rollback/exact replay in isolated synthetic state. The first bounded proposer call and both later same-evidence contrast calls chose no-op; useful model-selected maintenance remains undemonstrated and their meaning/usefulness judgments remain pending. A read-only PROV-O projection now describes recorded lineage without inventing actors/times or claiming semantic correctness. The public standards pilot now captures one development arc as separately attributed, unmodified IETF excerpts: 63 indexed source records and seven offline cutoff previews, with scoped reuse/privacy review and explicit historical-version gaps. Recorded source actors can be exported without inferring authority; activity actors remain unknown. The seven reviewed checkpoint meanings are separately user-approved development references, not a blanket policy, model-selected maintenance, or a semantic result. These foundations do not complete Phase 1. Durable continuous operation and dependable autonomous maintenance remain unproven; see the [EDD's current milestone](EDD.md#17-current-evidence-and-next-milestone).

## 15. Remaining product questions

1. **Semantic equivalence:** How does a Doozer distinguish safe consolidation from a meaningful exception, changed scope, or false synonymy? Which evidence must survive every transformation?
2. **Authority and evidence weighting:** How should independent corroboration, human expressions of agreement, time, and source quality bear on current understanding without pretending to calculate truth from a single score?
3. **Minimal state:** Can conditions like foggy/contested be reliably derived from relationships and context? What genuinely requires explicit lifecycle state, if anything?
4. **Intercession threshold:** When is uncertainty safe to leave dormant, when should it be visible in retrieval, and when is a contextual question genuinely valuable?
5. **Convergence:** How stable should repeated reconciliation be when evidence arrives in different orders? How much restructuring is beneficial rather than churn?
6. **Survivability versus deliberate deletion:** What historical evidence and derived content may survive normal retirement, and what must disappear under an explicit deletion request?
7. **Measuring trust:** Which realistic retrieval and maintenance tasks predict that users will reach for Doozers first and keep using it without added friction?

These are behavioral research questions. Node granularity, persistent identity schemes, database choices, embedding models, and orchestration remain subsequent architectural decisions.

## 16. Product litmus test

**After ten new conversations, does the existing body of understanding become simpler where it can, richer where it must, and more useful overall? Can a reader still find what matters, understand why it is believed, discover unresolved disagreement, and recover the meaning that was compacted away from the live view?**

The ideal Doozer is not the one that writes the most. It is the one that **quietly leaves the team with the least complicated truthful representation it can justify**.

## 17. Revision history

The PRD stays at `docs/PRD.md`; prior document contents remain in version-control
history rather than competing version-suffixed copies. Version numbers describe
the product contract, not a declaration that its requirements are implemented.

| Version | Date | Change |
| --- | --- | --- |
| 0.7 | November 24, 2026 | Record the first curated public discussion arc, conditional historical visibility, actual availability events rather than header dates, and known source attribution without authority inference. Offline preparation is not semantic validation or permission for model transmission. |
| [0.6](https://github.com/kolohelios/doozer/blob/535c06d11377db5079b6055e1781d644cc363702/docs/PRD.md) | November 24, 2026 | Add public standards/discussion replay as a complementary evaluation strategy and provenance interchange as an architectural hypothesis. Preserve rights, privacy, historical visibility, and release-specific scope; distinguish the PROV prototype and source inventory from demonstrated semantic autonomy. |
| [0.5](https://github.com/kolohelios/doozer/blob/19860b5cac12b93fa51cc0e3877000c3bf6615e3/docs/PRD.md) | November 24, 2026 | Clarify source-free maintenance, layout-independent preservation, justified no-op versus under-maintenance, and the distinction between experimental mechanics and demonstrated autonomy. Record that the automatic-retry restriction may be integrated, without approving a particular patch or the observed no-op. |
| [0.4](https://github.com/kolohelios/doozer/blob/16ba8f2dc806203d80dace8928b21972e0306bbe/docs/PRD.md) | November 21, 2026 | Baseline product contract: survivability → discoverability → compactness, autonomous local optimization, evidence/history separation, continuous reconciliation, and open projections. |
