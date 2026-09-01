#!/usr/bin/env python3
"""Pre-send linting for agent-generated email payloads.

Reads an AgentMail-style JSON payload from a file or stdin and exits non-zero
when it finds defects that should block an automated send.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
LINE_NUMBER_RE = re.compile(r"(?m)^\s*\d+\|")
PLACEHOLDER_RES = [
    re.compile(r"\{\{[^{}]+\}\}"),
    re.compile(r"\[\s*(?:name|company|email|price|date|insert[^]]*)\s*\]", re.I),
    re.compile(r"\b(?:TODO|TBD|FIXME)\b"),
]
SECRET_RES = [
    re.compile(r"\b(?:sk|pk)_(?:live|test)_[A-Za-z0-9]{12,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\b(?:api[_ -]?key|access[_ -]?token|password)\s*[:=]\s*[^\s]{8,}"),
]


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str


def _addresses(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list) and all(isinstance(x, str) for x in value):
        return value
    return []


def lint(payload: dict[str, Any], *, commercial: bool = False) -> list[Finding]:
    findings: list[Finding] = []
    recipients: list[str] = []
    for field in ("to", "cc", "bcc"):
        value = payload.get(field)
        values = _addresses(value)
        if value is not None and not values:
            findings.append(Finding("error", f"invalid_{field}_type", f"{field} must be a string or list of strings"))
        for address in values:
            bare = re.sub(r"^.*<([^>]+)>$", r"\1", address).strip()
            if not EMAIL_RE.match(bare):
                findings.append(Finding("error", "invalid_email", f"invalid {field} address: {address}"))
            recipients.append(bare.lower())

    if not recipients:
        findings.append(Finding("error", "missing_recipient", "at least one recipient is required"))
    if len(recipients) != len(set(recipients)):
        findings.append(Finding("error", "duplicate_recipient", "a recipient appears more than once"))

    subject = payload.get("subject", "")
    text = payload.get("text", "")
    html = payload.get("html", "")
    if subject is not None and not isinstance(subject, str):
        findings.append(Finding("error", "invalid_subject", "subject must be a string"))
        subject = ""
    if text is not None and not isinstance(text, str):
        findings.append(Finding("error", "invalid_text", "text must be a string"))
        text = ""
    if html is not None and not isinstance(html, str):
        findings.append(Finding("error", "invalid_html", "html must be a string"))
        html = ""
    if not text.strip() and not html.strip():
        findings.append(Finding("error", "missing_body", "text or html body is required"))
    if not subject.strip():
        findings.append(Finding("warning", "missing_subject", "subject is empty"))

    combined = "\n".join((subject, text, html))
    if LINE_NUMBER_RE.search(combined):
        findings.append(Finding("error", "exported_line_numbers", "body contains read/export line-number prefixes such as '12|'"))
    for pattern in PLACEHOLDER_RES:
        match = pattern.search(combined)
        if match:
            findings.append(Finding("error", "unresolved_placeholder", f"unresolved placeholder: {match.group(0)}"))
            break
    for pattern in SECRET_RES:
        if pattern.search(combined):
            findings.append(Finding("error", "possible_secret", "body may contain a credential or secret"))
            break

    if commercial:
        compliance = payload.get("compliance")
        if not isinstance(compliance, dict):
            findings.append(Finding("error", "missing_commercial_compliance", "commercial mode requires a compliance object"))
        else:
            required = {
                "sender_postal_address": "physical postal address",
                "opt_out_text": "opt-out text",
                "advertising_disclosure_text": "advertising disclosure text",
            }
            folded_body = combined.casefold()
            for field, label in required.items():
                value = compliance.get(field)
                if not isinstance(value, str) or not value.strip():
                    findings.append(Finding("error", f"missing_{field}", f"commercial mode requires {label} in compliance.{field}"))
                elif value.strip().casefold() not in folded_body:
                    findings.append(Finding("error", f"{field}_not_in_body", f"compliance.{field} must appear verbatim in the message body"))

    headers = payload.get("headers", {})
    if headers is None:
        headers = {}
    if not isinstance(headers, dict):
        findings.append(Finding("error", "invalid_headers", "headers must be an object when provided"))
        headers = {}
    header_key = next(
        (value for name, value in headers.items() if isinstance(name, str) and name.lower() == "idempotency-key"),
        None,
    )
    key = payload.get("idempotency_key") or payload.get("Idempotency-Key") or header_key
    if not isinstance(key, str) or len(key.strip()) < 8:
        findings.append(Finding("error", "missing_idempotency_key", "provide a stable idempotency key of at least 8 characters at top level or in headers.Idempotency-Key"))
    if len(subject) > 120:
        findings.append(Finding("warning", "long_subject", "subject exceeds 120 characters"))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Block unsafe or malformed agent-generated email payloads before send")
    parser.add_argument("payload", nargs="?", help="JSON payload path; omit or use - for stdin")
    parser.add_argument("--json", action="store_true", dest="json_output", help="emit machine-readable JSON")
    parser.add_argument("--commercial", action="store_true", help="require declared postal-address, opt-out, and advertising-disclosure text to appear in the body")
    args = parser.parse_args()
    try:
        raw = sys.stdin.read() if not args.payload or args.payload == "-" else Path(args.payload).read_text(encoding="utf-8")
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("payload must be a JSON object")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"ok": False, "findings": [{"severity": "error", "code": "invalid_json", "message": str(exc)}]}))
        return 2

    findings = lint(payload, commercial=args.commercial)
    errors = [f for f in findings if f.severity == "error"]
    result = {"ok": not errors, "error_count": len(errors), "warning_count": len(findings) - len(errors), "findings": [asdict(f) for f in findings]}
    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        for finding in findings:
            print(f"{finding.severity.upper()} {finding.code}: {finding.message}")
        print("PASS" if not errors else "BLOCK")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
