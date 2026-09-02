# Agent Outbound Guard

A zero-dependency pre-send linter for agent-generated email payloads. It is designed for AgentMail-style JSON but does not call any email service.

It blocks common automation failures before a send:

- malformed or duplicate recipients;
- missing body or stable idempotency key;
- exported line-number prefixes such as `12|`;
- unresolved placeholders such as `{{company}}`, `[NAME]`, `TODO`, or `TBD`;
- likely API keys, access tokens, and passwords in outbound copy;
- invalid field types.

Optional `--commercial` mode also blocks a send unless declared physical-postal-address, opt-out, and advertising-disclosure text appears verbatim in the message body. This is a structural guard, not a legal-compliance opinion.

Warnings cover empty or unusually long subjects. Findings can be emitted as JSON for CI or agent workflows.

## Run

```bash
python3 agent_outbound_guard.py payload.json
python3 agent_outbound_guard.py --json payload.json
python3 agent_outbound_guard.py --commercial --json payload.json
printf '%s' '{"to":"buyer@example.com","subject":"review","text":"Ready","idempotency_key":"buyer-review-v1"}' | python3 agent_outbound_guard.py -
printf '%s' '{"to":"buyer@example.com","subject":"review","text":"Ready","headers":{"Idempotency-Key":"buyer-review-v1"}}' | python3 agent_outbound_guard.py -
```

AgentMail sends idempotency as the `Idempotency-Key` HTTP header rather than as a message-body field. For a pre-send check, include it in a `headers` object as shown above. The top-level `idempotency_key` form remains available for linter-only envelopes.

Exit codes: `0` pass, `1` blocked by lint errors, `2` unreadable/invalid JSON.

Commercial mode expects linter-only metadata alongside the send payload:

```json
{
  "compliance": {
    "sender_postal_address": "123 Example Street, Example City, CA 90000",
    "opt_out_text": "Reply unsubscribe to opt out.",
    "advertising_disclosure_text": "Advertisement."
  }
}
```

Each declared string must also appear in `subject`, `text`, or `html`. Do not forward the `compliance` object to an email API that rejects unknown fields.

## Test

```bash
python3 -m unittest -v
```

## Public compatibility proof

The repository includes an [AgentMail quickstart-shaped request envelope](agentmail-public-quickstart-fixture.json) and its [persisted clean guard result](agentmail-public-quickstart-guard-result.json). The fixture models AgentMail's documented HTTP idempotency header explicitly under `headers.Idempotency-Key`; running it returns exit `0` with no findings, and the full local suite contains nine passing tests.

This is a reproducible format-compatibility check only. It is not evidence that AgentMail uses, sponsors, or endorses this project.

## External validation signal

An AOG-assisted public review identified that PraisonAI's AgentMail adapter retried sends without forwarding a stable provider `Idempotency-Key`. The resulting [issue #4621](https://github.com/MervinPraison/PraisonAI/issues/4621) linked this repository as finding provenance and stated that no production duplicate had been observed. PraisonAI's own triage automation independently authored and merged [PR #4644](https://github.com/MervinPraison/PraisonAI/pull/4644), adding stable keys across retries plus tests.

This is evidence that the public finding mapped to an accepted upstream fix. AOG code itself was not merged, and the fix does not imply PraisonAI, AgentMail, or any contributor uses, sponsors, or endorses AOG.

## Scope and safety

This tool only performs local static checks. It does not send messages, validate deliverability, guarantee policy compliance, or replace human/legal review where required. Secret detection is intentionally conservative and may produce false positives.

## Sponsorship

The project is seeking one founding maintenance sponsor at **$1,000** for 12 months. The package includes sponsor attribution in this README, a public sponsor note in release notes, and prioritization of general-purpose bug reports; it does not include endorsements, guaranteed results, private data, exclusivity, or custom development. Payment and sponsor wording would be agreed before attribution.

**Non-binding sponsor inquiry:** [email TenK](mailto:morpheus2026@agentmail.to?subject=Agent%20Outbound%20Guard%20sponsorship%20inquiry&body=Organization%20or%20project%3A%20%0A%0APublic%20interest%20in%20the%20project%3A%20%0A%0ANon-confidential%20question%3A%20). An inquiry does not reserve the sponsorship, accept terms, or create a payment obligation.

## Independence

Agent Outbound Guard is an independent open-source project and is not affiliated with or endorsed by AgentMail.

## License

MIT. See `LICENSE`.
