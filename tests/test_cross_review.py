import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "cross_review.py"
SPEC = importlib.util.spec_from_file_location("cross_review", MODULE_PATH)
cross_review = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(cross_review)


class FindingCardTests(unittest.TestCase):
    def test_retracted_own_finding_removes_initial_candidate(self) -> None:
        results = {
            "codex_initial": {
                "ok": True,
                "text": """STATUS: NEEDS_REVISION

## Findings
### P1: Old issue
- File: a.py:10
- Evidence: suspected bug
- Impact: bad
- Suggested fix: fix it

## Questions
- None.""",
            },
            "codex_response": {
                "ok": True,
                "text": """STATUS: PASS

## Still Standing Own Findings
- None.

## Retracted Own Findings
### P1: Old issue
- File: a.py:10
- Evidence: I misread it.

## Confirmed Peer Findings
- None.

## Rejected Peer Findings
- None.

## Needs Human
- None.

## New Findings
- None.""",
            },
        }
        meta = {
            "profile": "normal",
            "mode": "uncommitted",
            "resolved_scope": "diff",
            "review_type": "code",
            "arbiter": "none",
            "diff_truncated": False,
        }

        findings = cross_review.build_findings_data(results, meta)

        self.assertEqual([], findings["merged"])

    def test_same_file_line_bucket_keeps_distinct_titles(self) -> None:
        cards = [
            {
                "id": "raw-1",
                "title": "Drops arbitration result",
                "priority": "P1",
                "review_type": "code",
                "category": "defect",
                "evidence_refs": [{"type": "file", "ref": "scripts/cross_review.py", "line": 10}],
                "evidence_summary": "first",
                "impact": "",
                "suggested_action": "",
                "sources": ["codex_initial"],
                "peer_status": "one_sided",
            },
            {
                "id": "raw-2",
                "title": "Mislabels reviewer timeout",
                "priority": "P1",
                "review_type": "code",
                "category": "defect",
                "evidence_refs": [{"type": "file", "ref": "scripts/cross_review.py", "line": 12}],
                "evidence_summary": "second",
                "impact": "",
                "suggested_action": "",
                "sources": ["claude_initial"],
                "peer_status": "one_sided",
            },
        ]

        merged = cross_review.merge_finding_cards(cards)

        self.assertEqual(2, len(merged))
        self.assertEqual(
            {"Drops arbitration result", "Mislabels reviewer timeout"},
            {card["title"] for card in merged},
        )

    def test_retraction_does_not_remove_other_reviewer_matching_finding(self) -> None:
        cards = [
            {
                "id": "raw-codex-retracted",
                "title": "Shared issue",
                "priority": "P1",
                "review_type": "code",
                "category": "rejected",
                "evidence_refs": [{"type": "file", "ref": "a.py", "line": 10}],
                "evidence_summary": "codex retracted this",
                "impact": "",
                "suggested_action": "",
                "sources": ["codex_response"],
                "peer_status": "retracted",
            },
            {
                "id": "raw-claude-standing",
                "title": "Shared issue",
                "priority": "P1",
                "review_type": "code",
                "category": "defect",
                "evidence_refs": [{"type": "file", "ref": "a.py", "line": 10}],
                "evidence_summary": "claude still believes this is real",
                "impact": "valid finding would be lost",
                "suggested_action": "keep it visible",
                "sources": ["claude_response"],
                "peer_status": "one_sided",
            },
        ]

        merged = cross_review.merge_finding_cards(cards)

        self.assertEqual(1, len(merged))
        self.assertEqual("unresolved", merged[0]["peer_status"])
        self.assertEqual({"codex_response", "claude_response"}, set(merged[0]["sources"]))

    def test_review_summary_records_arbiter_mode(self) -> None:
        summary = cross_review.build_review_summary(
            {},
            {
                "profile": "deep",
                "mode": "uncommitted",
                "resolved_scope": "diff",
                "review_type": "code",
                "arbiter": "codex",
                "diff_truncated": False,
                "created_at": "2026-05-13T00:00:00+08:00",
            },
        )

        self.assertIn("- Arbiter: `codex`", summary)

    def test_claude_pseudo_tool_call_without_status_is_blocked(self) -> None:
        payload = {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": "先检查。<tool_call>\n<function=Bash>\n</function>\n</tool_call>",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            out_raw = Path(tmpdir) / "claude.raw.json"
            result = cross_review.parse_claude_result(
                0,
                json.dumps(payload),
                "",
                out_raw,
            )

        self.assertFalse(result["ok"])
        self.assertIn("STATUS: BLOCKED", result["text"])
        self.assertIn("pseudo tool_call", result["error"])

    def test_deep_profile_keeps_claude_tools_disabled_by_default(self) -> None:
        args = type(
            "Args",
            (),
            {
                "profile": "deep",
                "rounds": None,
                "scope": None,
                "claude_tools": None,
                "max_diff_chars": None,
                "max_full_chars": None,
                "max_full_files": None,
            },
        )()

        cross_review.apply_profile_defaults(args)

        self.assertEqual("none", args.claude_tools)

    def test_confirmed_and_rejected_duplicate_finding_is_unresolved(self) -> None:
        cards = [
            {
                "id": "raw-confirmed",
                "title": "Shared issue",
                "priority": "P1",
                "review_type": "code",
                "category": "defect",
                "evidence_refs": [{"type": "file", "ref": "a.py", "line": 10}],
                "evidence_summary": "confirmed",
                "impact": "",
                "suggested_action": "",
                "sources": ["claude_response"],
                "peer_status": "confirmed",
            },
            {
                "id": "raw-rejected",
                "title": "Shared issue",
                "priority": "P1",
                "review_type": "code",
                "category": "rejected",
                "evidence_refs": [{"type": "file", "ref": "a.py", "line": 10}],
                "evidence_summary": "rejected",
                "impact": "",
                "suggested_action": "",
                "sources": ["codex_response"],
                "peer_status": "rejected",
            },
        ]

        merged = cross_review.merge_finding_cards(cards)

        self.assertEqual(1, len(merged))
        self.assertEqual("unresolved", merged[0]["peer_status"])
        self.assertEqual("medium", merged[0]["confidence"])

    def test_priority_parser_ignores_slash_template_placeholder(self) -> None:
        self.assertEqual("P2", cross_review.priority_from_text("P0/P1/P2: Title", ""))
        self.assertEqual("P1", cross_review.priority_from_text("P1: Real issue", ""))

    def test_explicit_file_field_prevents_body_file_mentions_from_becoming_refs(self) -> None:
        refs = cross_review.evidence_refs_from_body(
            "- File: a.py:10\n"
            "- Evidence: mentions README.md and package.json in explanation."
        )

        self.assertEqual([{"type": "file", "ref": "a.py", "line": 10}], refs)

    def test_file_mentions_are_marked_separately_when_no_explicit_file_field_exists(self) -> None:
        refs = cross_review.evidence_refs_from_body(
            "- Evidence: mentions README.md and package.json in explanation."
        )

        self.assertEqual(
            [
                {"type": "file_mention", "ref": "README.md", "line": None},
                {"type": "file_mention", "ref": "package.json", "line": None},
            ],
            refs,
        )

    def test_claude_tool_call_output_with_review_sections_is_preserved(self) -> None:
        payload = {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": "STATUS: NEEDS_REVISION\n\n## Findings\n### P1: Real issue\n- Evidence: x\n\n<tool_call>",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            out_raw = Path(tmpdir) / "claude.raw.json"
            result = cross_review.parse_claude_result(0, json.dumps(payload), "", out_raw)

        self.assertTrue(result["ok"])
        self.assertIn("P1: Real issue", result["text"])

    def test_claude_tool_call_output_with_sections_but_no_status_is_preserved_as_blocked_notes(self) -> None:
        payload = {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": "## Findings\n### P1: Real issue\n- Evidence: x\n\n<tool_call>",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            out_raw = Path(tmpdir) / "claude.raw.json"
            result = cross_review.parse_claude_result(0, json.dumps(payload), "", out_raw)

        self.assertFalse(result["ok"])
        self.assertIn("STATUS: BLOCKED", result["text"])
        self.assertIn("P1: Real issue", result["text"])


if __name__ == "__main__":
    unittest.main()
