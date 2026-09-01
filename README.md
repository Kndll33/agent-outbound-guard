# Agent Outbound Guard

A zero-dependency pre-send linter for agent-generated email payloads. It is designed for AgentMail-style JSON but does not call any email service.

It blocks common automation failures before a send:

- malformed or duplicate recipients;
- missing body or stable idempotency key;
- exported line-number prefixes such as `12|`;
- unresolved placeholders such as `{{company}}`, `[NAME]`, `TODO`, or `TBD`;
- likely API keys, access tokens, and passwords in outbound copy;
- invalid field types.

Warnings cover empty or unusually long subjects. Findings can be emitted as JSON for CI or agent workflows.

## Run

```bash
python3 agent_outbound_guard.py payload.json
python3 agent_outbound_guard.py --json payload.json
printf '%s' '{"to":"buyer@example.com","subject":"review","text":"Ready","idempotency_key":"buyer-review-v1"}' | python3 agent_outbound_guard.py -
```

Exit codes: `0` pass, `1` blocked by lint errors, `2` unreadable/invalid JSON.

## Test

```bash
python3 -m unittest -v
```

## Scope and safety

This tool only performs local static checks. It does not send messages, validate deliverability, guarantee policy compliance, or replace human/legal review where required. Secret detection is intentionally conservative and may produce false positives.

## Sponsorship

The project is seeking one founding maintenance sponsor at **$1,000** for 12 months. The package includes sponsor attribution in this README, a public sponsor note in release notes, and prioritization of general-purpose bug reports; it does not include endorsements, guaranteed results, private data, exclusivity, or custom development. Payment and sponsor wording would be agreed before attribution.

**Non-binding sponsor inquiry:** [email TenK](mailto:morpheus2026@agentmail.to?subject=Agent%20Outbound%20Guard%20sponsorship%20inquiry&body=Organization%20or%20project%3A%20%0A%0APublic%20interest%20in%20the%20project%3A%20%0A%0ANon-confidential%20question%3A%20). An inquiry does not reserve the sponsorship, accept terms, or create a payment obligation.

## Independence

Agent Outbound Guard is an independent open-source project and is not affiliated with or endorsed by AgentMail.

## License

MIT. See `LICENSE`.
