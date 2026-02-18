import unittest
import time
from reply_intelligence import ReplyIntelligence

class TestReplyIntelligence(unittest.TestCase):
    def setUp(self):
        self.engine = ReplyIntelligence()

    def test_signal_extraction(self):
        thread = [
            {"body": "What is the pricing and timeline?", "timestamp": 1000, "sender": "lead"}
        ]
        result = self.engine.analyze_thread(thread)
        signals = result['signals']
        
        self.assertEqual(signals['pricing'], 1)
        self.assertEqual(signals['timeline'], 1)
        self.assertEqual(signals['question_count'], 1)
        self.assertEqual(signals['budget'], 0)

    def test_scoring_high_intent(self):
        # Active thread, high constraints
        now = time.time()
        thread = [
            {"body": "We need a solution asap.", "timestamp": now - 3600*3, "sender": "lead"},
            {"body": "Here is info.", "timestamp": now - 3600*2, "sender": "agent"},
            {"body": "Great, what is the price? We have budget.", "timestamp": now - 300, "sender": "lead"}
        ]
        result = self.engine.analyze_thread(thread)
        
        print(f"\nHigh Intent Score: {result['score']}")
        print(f"Explanation: {result['explanation']}")
        
        self.assertEqual(result['state'], "Ready Now")
        self.assertGreater(result['score'], 60)
        self.assertTrue("Mentioned pricing" in result['explanation'])
        self.assertTrue("Mentioned budget" in result['explanation'])

    def test_scoring_deprioritize(self):
        # Single message, no signals
        thread = [
            {"body": "ok", "timestamp": 1000, "sender": "lead"}
        ]
        result = self.engine.analyze_thread(thread)
        
        print(f"\nDeprioritize Score: {result['score']}")
        self.assertEqual(result['state'], "Deprioritize")
        self.assertLess(result['score'], 40)

    def test_engagement_cliff(self):
        now = time.time()
        # Thread active but silent for 4 days
        thread = [
            {"body": "msg 1", "timestamp": now - (86400 * 5), "sender": "lead"},
            {"body": "msg 2", "timestamp": now - (86400 * 4), "sender": "agent"},
            {"body": "msg 3", "timestamp": now - (86400 * 4), "sender": "lead"}
        ]
        result = self.engine.analyze_thread(thread)
        
        self.assertEqual(result['cliff_flag'], "Paused or Internal Blocker")

    def test_right_icp_wrong_timing(self):
        # High depth but very slow responses (e.g. 3 days between)
        thread = [
            {"body": "Hi", "timestamp": 1000, "sender": "lead"},
            {"body": "Reply", "timestamp": 1000 + 86400*3, "sender": "lead"}, # 3 days later
            {"body": "Again", "timestamp": 1000 + 86400*6, "sender": "lead"}  # 3 days later
        ]
        result = self.engine.analyze_thread(thread)
        
        # Velocity is high (bad) -> Score impacted
        print(f"\nSlow Response Score: {result['score']} State: {result['state']}")
        
        # Logic might classify as Ready Now if validation logic prioritizes depth too much.
        # My logic: if depth >= 2 and NOT velocity_ok (<48h) -> Right ICP
        # Avg velocity here is 72 hours (3 days).
        
        self.assertEqual(result['state'], "Right ICP Wrong Timing")

if __name__ == '__main__':
    unittest.main()
