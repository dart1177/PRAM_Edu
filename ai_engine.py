import re
import time

class AIEngine:
    def __init__(self):
        self.knowledge_base = {
            "attendance": "Your attendance is 85%. You need 75% to pass.",
            "exam": "Your next exam is on March 15, 2025 at 10:00 AM.",
            "fees": "Your fee payment is due on April 1, 2025. Amount: ₹45,000.",
            "course": "You are enrolled in: Python, AI, Cybersecurity.",
            "assignment": "You have 2 pending assignments. Due: March 10.",
            "result": "Your last semester GPA is 8.5/10.",
            "library": "Library hours: 9 AM - 8 PM. You have 2 books issued.",
            "hostel": "Hostel room: B-204. Warden: Mr. Sharma (+91-XXXXX)."
        }
        
        # Simple keyword mapping for intent detection
        self.keywords = {
            "attendance": ["attendance", "present", "absent"],
            "exam": ["exam", "test", "midterm", "final"],
            "fees": ["fee", "payment", "due", "pay"],
            "course": ["course", "enrolled", "subject", "classes"],
            "assignment": ["assignment", "homework", "due", "task"],
            "result": ["result", "gpa", "marks", "score", "grade"],
            "library": ["library", "book", "issue"],
            "hostel": ["hostel", "room", "warden", "accommodation"]
        }

    def _sanitize(self, text):
        # Basic SQL injection pattern removal
        patterns = [r"'", r'"', r";", r"--", r"/\*", r"\*/", r"(?i)\bdrop\b", r"(?i)\bdelete\b"]
        for p in patterns:
            text = re.sub(p, "", text)
        return text.strip()

    def _detect_intent(self, question):
        q_lower = question.lower()
        for intent, kw_list in self.keywords.items():
            if any(kw in q_lower for kw in kw_list):
                return intent
        return "unknown"

    def _fallback_response(self, question):
        return "I'm sorry, I couldn't understand your request. Please contact the administration office."

    def process_query(self, question):
        start_time = time.time()
        
        safe_q = self._sanitize(question)
        intent = self._detect_intent(safe_q)
        
        if intent in self.knowledge_base:
            answer = self.knowledge_base[intent]
            confidence = 0.9
        else:
            answer = self._fallback_response(safe_q)
            confidence = 0.3
            
        response_time_ms = (time.time() - start_time) * 1000
        
        return {
            "answer": answer,
            "confidence": confidence,
            "intent": intent,
            "response_time_ms": response_time_ms
        }

if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding='utf-8')
    engine = AIEngine()
    test_queries = [
        "What is my attendance?",
        "When is my next exam?",
        "How much fees is pending?",
        "Which courses am I enrolled in?",
        "Do I have any assignment?",
        "What was my result last semester?",
        "What are the library hours?",
        "Who is the hostel warden?",
        "Drop table users; -- What is my GPA?" # SQL Injection attempt
    ]
    
    print(f"Testing {len(test_queries)} queries:")
    for i, q in enumerate(test_queries, 1):
        res = engine.process_query(q)
        print(f"[{i}] Q: {q}")
        print(f"    Intent: {res['intent']} | Conf: {res['confidence']} | Time: {res['response_time_ms']:.2f}ms")
        print(f"    A: {res['answer']}\n")
