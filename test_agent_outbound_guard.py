import unittest

from agent_outbound_guard import lint


class GuardTests(unittest.TestCase):
    def test_clean_payload_passes(self):
        payload = {
            "to": "buyer@example.com",
            "subject": "bounded review",
            "text": "Hello — here is the requested review.",
            "idempotency_key": "buyer-review-v1",
        }
        self.assertFalse([f for f in lint(payload) if f.severity == "error"])

    def test_agentmail_header_idempotency_passes(self):
        payload = {
            "to": "recipient@example.com",
            "subject": "Hello from AgentMail",
            "text": "Plain text body",
            "headers": {"Idempotency-Key": "quickstart-send-v1"},
        }
        self.assertFalse([f for f in lint(payload) if f.severity == "error"])

    def test_invalid_headers_block(self):
        payload = {
            "to": "buyer@example.com",
            "subject": "test",
            "text": "body",
            "headers": ["Idempotency-Key: test-send-v3"],
        }
        codes = {f.code for f in lint(payload)}
        self.assertTrue({"invalid_headers", "missing_idempotency_key"}.issubset(codes))

    def test_line_number_placeholder_and_missing_key_block(self):
        payload = {
            "to": "buyer@example.com",
            "subject": "Hello [NAME]",
            "text": "1|This leaked from an exported file.",
        }
        codes = {f.code for f in lint(payload)}
        self.assertTrue({"exported_line_numbers", "unresolved_placeholder", "missing_idempotency_key"}.issubset(codes))

    def test_secret_and_bad_recipient_block(self):
        payload = {
            "to": "not-an-email",
            "subject": "test",
            "text": "api_key = supersecretvalue123",
            "idempotency_key": "test-send-v1",
        }
        codes = {f.code for f in lint(payload)}
        self.assertIn("invalid_email", codes)
        self.assertIn("possible_secret", codes)

    def test_duplicate_recipient_blocks(self):
        payload = {
            "to": ["a@example.com", "A@example.com"],
            "subject": "test",
            "text": "body",
            "idempotency_key": "test-send-v2",
        }
        self.assertIn("duplicate_recipient", {f.code for f in lint(payload)})


if __name__ == "__main__":
    unittest.main()
