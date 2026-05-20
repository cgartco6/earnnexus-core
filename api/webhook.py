# file: api/webhook.py
import json
import os
import hmac
import hashlib
import time
from http.server import BaseHTTPRequestHandler
from api.ledger import commit_transaction_to_db

class handler(BaseHTTPRequestHandler):
    """
    Production-hardened Serverless transaction routing processor featuring
    cryptographic signature verification and atomic state ledger sync.
    """
    def log_structured(self, level: str, message: str, context: dict = None):
        """Outputs standardized JSON log metrics for production stack tracing."""
        log_packet = {
            "timestamp": time.time(),
            "level": level,
            "message": message,
            "context": context or {}
        }
        print(json.dumps(log_packet))

    def verify_webhook_signature(self, raw_body: str, received_signature: str) -> bool:
        """Validates incoming payload authenticity using high-security HMAC-SHA256 tokens."""
        secret = os.environ.get("PAYMENT_GATEWAY_WEBHOOK_SECRET")
        if not secret:
            # Secure Fallback: In clean local dev environments, allow verification if explicitly stated
            return os.environ.get("SYSTEM_ENVIRONMENT") == "development"
            
        computed_sig = hmac.new(
            secret.encode('utf-8'),
            raw_body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(computed_sig, received_signature)

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        raw_payload = self.rfile.read(content_length).decode('utf-8')
        signature = self.headers.get('X-Webhook-Signature', '')

        # 1. Access Authentication Boundary: Deny unsigned/untrusted payloads
        if not self.verify_webhook_signature(raw_payload, signature):
            self.send_response(401)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Unauthorized: Invalid cryptographic signature hash."}).encode('utf-8'))
            return

        try:
            # 2. Extract Data Packets
            data = json.loads(raw_payload)
            reference = data.get("reference")
            gross_cents = data.get("amount_cents")

            # Validate structural integer types explicitly
            if not reference or not isinstance(gross_cents, int) or gross_cents <= 0:
                self.send_response(422)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Unprocessable Entity: Validation rules violated."}).encode('utf-8'))
                return

            # 3. High-Precision Mathematical Core Allocation Engine (40% / 50% / 10%)
            cushion_split = int(gross_cents * 0.40)
            secondary_split = int(gross_cents * 0.50)
            # Reconstruct trailing decimals via balance subtraction to eliminate any structural software drift
            banking_split = gross_cents - (cushion_split + secondary_split)

            # 4. Attempt State Synchronization via Persistence Pipeline
            db_result = commit_transaction_to_db(
                reference=reference, 
                gross=gross_cents,
                cushion=cushion_split, 
                secondary=secondary_split, 
                banking=banking_split
            )

            # 5. Formulate Response Matrices based on Database Resolution Engine
            if db_result["success"]:
                self.send_response(200)
                status_code = "SUCCESS_REVENUE_ROUTED"
            elif db_result["strategy"] == "REJECTED_DUPLICATE":
                self.send_response(409)  # HTTP 409 Conflict
                status_code = "DUPLICATE_TRANSACTION_IGNORED"
            else:
                self.send_response(500)
                status_code = "DATABASE_COMMIT_FAILED"

            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            self.wfile.write(json.dumps({
                "status": status_code,
                "strategy_executed": db_result["strategy"],
                "error": db_result["error"]
            }).encode('utf-8'))

        except Exception as fatal_exception:
            self.log_structured("CRITICAL", f"Pipeline crashed: {str(fatal_exception)}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Critical Internal Pipeline Crash: {str(fatal_exception)}"}).encode('utf-8'))
