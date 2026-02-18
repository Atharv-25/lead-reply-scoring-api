import unittest
import json
import time
from server import app, LEAD_DB

class TestDashboardIntegration(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        LEAD_DB.clear()

    def test_webhook_to_dashboard_flow(self):
        """Send webhook reply -> Verify dashboard shows lead."""
        res = self.app.post('/webhook/reply', json={
            "email": "buyer@acme.com",
            "body": "We have the budget approved. What is the pricing? We need to launch next week.",
            "timestamp": time.time(),
            "sender": "lead"
        })
        self.assertEqual(res.status_code, 200)
        
        self.assertIn("buyer@acme.com", LEAD_DB)
        lead = LEAD_DB["buyer@acme.com"]
        self.assertIn("score", lead)
        self.assertIn("state", lead)
        self.assertIn("momentum", lead)
        
        res = self.app.get('/api/dashboard')
        data = json.loads(res.data)
        self.assertGreater(data['stats']['total_analyzed'], 0)

    def test_full_constraint_ready_now(self):
        """Full constraint + depth must reach Ready Now (61+)."""
        now = time.time()
        
        self.app.post('/webhook/reply', json={
            "email": "vip@example.com",
            "body": "We have the budget approved and need to launch ASAP.",
            "timestamp": now - 7200, "sender": "lead"
        })
        self.app.post('/webhook/reply', json={
            "email": "vip@example.com",
            "body": "Here are our options.",
            "timestamp": now - 5400, "sender": "agent"
        })
        self.app.post('/webhook/reply', json={
            "email": "vip@example.com",
            "body": "What is the pricing? We are comparing vendors. Can your API integrate?",
            "timestamp": now - 3600, "sender": "lead"
        })
        self.app.post('/webhook/reply', json={
            "email": "vip@example.com",
            "body": "Our team approved. How do we deploy?",
            "timestamp": now, "sender": "lead"
        })

        # Cold lead
        self.app.post('/webhook/reply', json={
            "email": "cold@example.com",
            "body": "ok",
            "timestamp": now, "sender": "lead"
        })

        res = self.app.get('/api/dashboard')
        data = json.loads(res.data)
        
        ready = data['sections']['ready_now']
        depri = data['sections']['deprioritize']
        
        self.assertTrue(len(ready) >= 1, "VIP should be Ready Now")
        self.assertTrue(len(depri) >= 1, "Cold should be Deprioritize")
        self.assertGreaterEqual(ready[0]['score'], 61)
        self.assertIn('momentum', ready[0])

    def test_comparative_layer(self):
        """Two Ready Now leads should produce comparative explanation."""
        now = time.time()
        
        # Lead A: Full constraint
        for body in [
            "Budget approved. Need to launch ASAP.",
            "What is pricing? Comparing with competitors. Can API integrate?",
            "Team approved. How to deploy?"
        ]:
            self.app.post('/webhook/reply', json={
                "email": "leadA@example.com", "body": body,
                "timestamp": now, "sender": "lead"
            })
        
        # Lead B: Budget + timeline only
        for body in [
            "We have budget for this.",
            "When can we start? What are next steps?",
            "Need this by end of month."
        ]:
            self.app.post('/webhook/reply', json={
                "email": "leadB@example.com", "body": body,
                "timestamp": now, "sender": "lead"
            })

        res = self.app.get('/api/dashboard')
        data = json.loads(res.data)
        
        if len(data['sections']['ready_now']) >= 2:
            self.assertGreater(len(data.get('comparative', [])), 0,
                             "Should have comparative explanation")
            reason = data['comparative'][0]['reason']
            print(f"\nComparative: {reason}")
            self.assertIn("leadA@example.com", reason)

    def test_shallow_penalty_applied(self):
        """'Sounds good' in 1 min should get penalized."""
        now = time.time()
        self.app.post('/webhook/reply', json={
            "email": "shallow@example.com",
            "body": "Hi there",
            "timestamp": now - 120, "sender": "agent"
        })
        self.app.post('/webhook/reply', json={
            "email": "shallow@example.com",
            "body": "Ok",
            "timestamp": now - 60, "sender": "lead"
        })
        
        lead = LEAD_DB["shallow@example.com"]
        self.assertLessEqual(lead['score'], 20, "Shallow fast reply should be penalized")
        self.assertEqual(lead['state'], "Deprioritize")

if __name__ == '__main__':
    unittest.main()
