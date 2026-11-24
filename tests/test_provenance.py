import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from rdflib import Graph, Literal, Namespace, RDF, URIRef

from scripts import provenance as prov, retry_maintenance, workbench as wb


P = Namespace(prov.CONTEXT["prov"])
D = Namespace(prov.CONTEXT["doozer"])


class ProvenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch("urllib.request.urlopen", side_effect=AssertionError("offline only")):
            cls.experiment = retry_maintenance.run()
        cls.state = cls.experiment["policies"]["maintained"]["state"]

    def export(self, state=None):
        return prov.project(self.state if state is None else state, dataset_id="synthetic-retry-development")

    def nodes(self, result, kind):
        return [n for n in result["@graph"] if n.get("doozer:representationKind") == kind]

    def test_actual_jsonld_parses_as_rdf_without_remote_context(self):
        result = self.export()
        with patch("urllib.request.urlopen", side_effect=AssertionError("no remote context")):
            graph = Graph().parse(data=json.dumps(result), format="json-ld")
        self.assertEqual(len(set(graph.subjects(RDF.type, P.Activity))), len(self.state["journal"]))
        self.assertEqual(len(set(graph.subjects(RDF.type, P.Collection))), len(self.state["journal"]) + 1)
        self.assertFalse(list(graph.subjects(RDF.type, P.Agent)))
        final = [n for n in self.nodes(result, "knowledge-snapshot") if n["doozer:journalPosition"] == len(self.state["journal"])][0]
        self.assertEqual(len(list(graph.objects(URIRef(final["@id"]), P.hadMember))), len(self.state["claims"]))
        self.assertIn((URIRef(final["@id"]), D.localRevision, Literal(self.state["revision"])), graph)

    def test_read_only_deterministic_dataset_scoped_and_closed_references(self):
        before = copy.deepcopy(self.state)
        result = self.export()
        self.assertEqual(result, self.export())
        self.assertEqual(self.state, before)
        changed_scope = prov.project(self.state, dataset_id="other-development-dataset")
        ids = {n["@id"] for n in result["@graph"]}
        self.assertFalse(ids & {n["@id"] for n in changed_scope["@graph"]})
        def check(value):
            if isinstance(value, dict):
                if "@id" in value:
                    self.assertIn(value["@id"], ids)
                for child in value.values():
                    check(child)
            elif isinstance(value, list):
                for child in value:
                    check(child)
        check(result["@graph"])
        result["@context"]["prov"] = "caller mutation"
        self.assertEqual(prov.CONTEXT["prov"], str(P))

    def test_sources_assertions_quotations_and_projections_are_distinct_records(self):
        result = self.export()
        source_nodes = self.nodes(result, "source-record")
        claims = self.nodes(result, "assertion-record")
        self.assertEqual(len(source_nodes), len(self.state["received"]))
        self.assertEqual(len(claims), len(self.state["history"]))
        self.assertEqual(len(self.nodes(result, "projection")), 2)
        lookup = {n["@id"]: n for n in result["@graph"]}
        for node in claims:
            self.assertEqual(json.loads(node["doozer:recordJSON"]), self.state["history"][node["doozer:claimId"]])
            self.assertNotIn("prov:wasQuotedFrom", node)
            self.assertNotIn("prov:wasDerivedFrom", node)  # Mere citation is not verified derivation.
            for citation in node["doozer:cites"]:
                quote = lookup[citation["@id"]]
                original = lookup[quote["prov:wasQuotedFrom"]["@id"]]
                self.assertEqual(original["doozer:representationKind"], "source-record")
                self.assertIn(quote["prov:value"], json.loads(original["doozer:recordJSON"])["text"])
        for node in self.nodes(result, "projection"):
            self.assertEqual(node["doozer:sourceKind"], "projection")
            self.assertEqual(lookup[node["prov:wasDerivedFrom"]["@id"]]["doozer:representationKind"], "knowledge-snapshot")

    def test_contextual_no_is_not_agreement_or_derivation_and_stop_is_retained(self):
        result = self.export()
        sources = {n["doozer:sourceId"]: n for n in self.nodes(result, "source-record")}
        self.assertEqual(sources["no"]["doozer:replyTo"], {"@id": sources["proposal"]["@id"]})
        self.assertNotIn("prov:wasDerivedFrom", sources["no"])
        self.assertIn("Stop.", sources["ambiguous"]["doozer:recordJSON"])
        self.assertTrue(sources["handbook"]["prov:wasDerivedFrom"])
        self.assertEqual(sources["handbook"]["doozer:sourceKind"], "projection")

    def test_receipt_generation_effective_times_and_authors_are_not_invented(self):
        result = self.export()
        self.assertTrue(any("doozer:statementTime" in n for n in self.nodes(result, "source-record")))
        for node in result["@graph"]:
            self.assertNotIn("prov:generatedAtTime", node)
            self.assertNotIn("prov:startedAtTime", node)
            self.assertNotIn("prov:invalidatedAtTime", node)
            self.assertNotIn("prov:wasAttributedTo", node)
            self.assertNotIn("prov:wasAssociatedWith", node)

    def test_every_prefix_has_exact_active_membership_and_retired_entities_survive(self):
        result = self.export()
        claims = {n["doozer:claimId"]: n["@id"] for n in self.nodes(result, "assertion-record")}
        snapshots = sorted(self.nodes(result, "knowledge-snapshot"), key=lambda n: n["doozer:journalPosition"])
        for position, node in enumerate(snapshots):
            view = wb.historical_view(self.state, position)
            self.assertEqual({r["@id"] for r in node["prov:hadMember"]}, {claims[key] for key in view["claims"]})
            self.assertEqual(json.loads(node["doozer:aliasesJSON"]), view["redirects"])
            if position:
                self.assertEqual(node["prov:wasRevisionOf"], {"@id": snapshots[position - 1]["@id"]})
        retired = set(self.state["history"]) - set(self.state["claims"])
        self.assertTrue(retired)
        self.assertTrue(all(claims[key] not in {r["@id"] for r in snapshots[-1]["prov:hadMember"]} for key in retired))
        self.assertTrue(all("prov:wasInvalidatedBy" not in n for n in result["@graph"]))

    def test_restore_and_replay_reuse_immutable_assertions_without_second_generation(self):
        state = self.experiment["recovery"]["state"]
        result = self.export(state)
        originals = {n["doozer:claimId"]: n for n in self.nodes(self.export(), "assertion-record")}
        for node in self.nodes(result, "assertion-record"):
            self.assertEqual(node, originals[node["doozer:claimId"]])
        activities = {n["doozer:journalPosition"]: n for n in result["@graph"] if n["@type"] == "prov:Activity"}
        self.assertTrue(any("doozer:replayOf" in n for n in activities.values()))
        for index, record in enumerate(state["journal"]):
            if record["kind"] == "restore":
                snapshots = {n["doozer:journalPosition"]: n for n in self.nodes(result, "knowledge-snapshot")}
                target = snapshots[record["request"]["targetPosition"]]["@id"]
                self.assertIn({"@id": target}, activities[index]["prov:used"])
                self.assertEqual(snapshots[index + 1]["prov:wasDerivedFrom"], [{"@id": target}])

    def test_processing_noop_is_an_activity_source_free_noop_is_not_new_history(self):
        result = self.export()
        snapshots = sorted(self.nodes(result, "knowledge-snapshot"), key=lambda n: n["doozer:journalPosition"])
        self.assertTrue(any(a["doozer:localRevision"] == b["doozer:localRevision"] and a["@id"] != b["@id"] for a, b in zip(snapshots, snapshots[1:])))
        settings = self.experiment["settings"]["consolidation"]
        unchanged = wb.maintain(self.state, settings["repeatPatch"], settings["analysis"], settings["route"])
        self.assertEqual(result, self.export(unchanged))

    def test_unknown_parent_ids_are_preserved_without_fabricated_entities(self):
        state = wb.new_state()
        wb.receive(state, "reply", {"kind": "conversation", "text": "No.", "replyTo": "missing", "derivedFrom": ["other-missing"], "anchor": "fixture://reply"})
        result = self.export(state)
        source = self.nodes(result, "source-record")[0]
        self.assertEqual(source["doozer:replyToSourceId"], "missing")
        self.assertNotIn("doozer:replyTo", source)
        self.assertEqual(json.loads(source["doozer:declaredDerivationSourceIdsJSON"]), ["other-missing"])
        self.assertEqual(source["prov:wasDerivedFrom"], [])
        self.assertEqual(len(self.nodes(result, "source-record")), 1)

    def test_legacy_history_fabrication_and_projection_corroboration_rejected(self):
        for defect in ("legacy", "claim", "quote", "projection"):
            state = copy.deepcopy(self.state)
            if defect == "legacy":
                del state["journal"][0]["before"]
            elif defect == "claim":
                state["claims"][next(iter(state["claims"]))]["text"] = "rewritten history"
            elif defect == "quote":
                state["history"][next(iter(state["history"]))]["evidence"][0]["quote"] = "fabrication"
            else:
                state["received"]["guide"]["kind"] = "projection"
            before = copy.deepcopy(state)
            with self.assertRaises(ValueError):
                self.export(state)
            self.assertEqual(state, before)
        with self.assertRaises(ValueError):
            prov.project(wb.new_state(), dataset_id=" ")

    def test_malformed_source_metadata_cannot_become_jsonld_objects(self):
        for field, value in (("kind", {"@id": "https://example.invalid/agent"}), ("saidAt", 42), ("replyTo", []), ("derivedFrom", "not-a-list")):
            state = copy.deepcopy(self.state)
            state["received"]["guide"][field] = value
            before = copy.deepcopy(state)
            with self.assertRaises(ValueError):
                self.export(state)
            self.assertEqual(state, before)

    def test_cli_exports_only_state_never_trace_or_evaluator_and_refuses_overwrite(self):
        with TemporaryDirectory() as directory, redirect_stdout(io.StringIO()):
            source, output = Path(directory) / "input.json", Path(directory) / "output.jsonld"
            source.write_text(json.dumps({"state": self.state, "trace": "PRIVATE_TRACE_CANARY", "evaluation": "PRIVATE_EVAL_CANARY"}))
            args = ["--input", str(source), "--output", str(output), "--dataset-id", "synthetic-retry-development"]
            with patch("urllib.request.urlopen", side_effect=AssertionError("offline only")):
                self.assertEqual(prov.main(args), 0)
            self.assertNotIn("CANARY", output.read_text())
            self.assertEqual(json.loads(output.read_text()), self.export())
            with self.assertRaises(ValueError):
                prov.main(args)
            output.unlink()
            source.write_text('{"state": {}, "state": {}}')
            with self.assertRaisesRegex(ValueError, "duplicate"):
                prov.main(args)
            self.assertFalse(output.exists())
