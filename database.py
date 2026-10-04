import sqlite3
import hashlib
import time
import os
from datetime import datetime, timedelta

class Database:
    def __init__(self, db_path="data/pram_edu.db"):
        self.db_path = db_path
        # When creating memory db for tests, no need for dir
        if self.db_path != ":memory:":
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self._mem_conn = None
        else:
            # Use URI to share the memory db across connections
            self.db_path = "file::memory:?cache=shared"
            self.uri = True
            
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path, uri=True) if self.db_path.startswith("file::memory:") else sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'student',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    question TEXT NOT NULL,
                    ai_response TEXT NOT NULL,
                    response_time_ms REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                );
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    endpoint TEXT,
                    ip TEXT,
                    status_code INTEGER,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                );
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                CREATE INDEX IF NOT EXISTS idx_queries_user_id ON queries(user_id);
                CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
            """)
            conn.commit()

    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, name, email, password, role="student"):
        password_hash = self.hash_password(password)
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                    (name, email, password_hash, role)
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def get_user_by_email(self, email):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_by_id(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def verify_login(self, email, password):
        user = self.get_user_by_email(email)
        if user and user['password_hash'] == self.hash_password(password):
            return user
        return None

    def save_query(self, user_id, question, ai_response, response_time_ms):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO queries (user_id, question, ai_response, response_time_ms) VALUES (?, ?, ?, ?)",
                (user_id, question, ai_response, response_time_ms)
            )
            conn.commit()
            return cursor.lastrowid

    def get_user_history(self, user_id, limit=20):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM queries WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
                (user_id, limit)
            )
            return [dict(row) for row in cursor.fetchall()]

    def log_action(self, user_id, action, endpoint, ip, status_code, details):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO audit_logs (user_id, action, endpoint, ip, status_code, details) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, action, endpoint, ip, status_code, details)
            )
            conn.commit()

    def get_suspicious_users(self):
        # Users with >5 failed logins in last hour
        one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, COUNT(*) as failed_attempts 
                FROM audit_logs 
                WHERE action = 'LOGIN_FAILED' AND timestamp >= ? 
                GROUP BY user_id 
                HAVING failed_attempts > 5
            """, (one_hour_ago,))
            return [dict(row) for row in cursor.fetchall()]

    def get_ai_performance(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    date(timestamp) as date,
                    COUNT(*) as query_count,
                    AVG(response_time_ms) as avg_time,
                    MIN(response_time_ms) as min_time,
                    MAX(response_time_ms) as max_time
                FROM queries
                GROUP BY date(timestamp)
                ORDER BY date DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_total_stats(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM users")
            users_count = cursor.fetchone()['cnt']
            cursor.execute("SELECT COUNT(*) as cnt FROM queries")
            queries_count = cursor.fetchone()['cnt']
            cursor.execute("SELECT COUNT(*) as cnt FROM audit_logs")
            logs_count = cursor.fetchone()['cnt']
            return {
                "total_users": users_count,
                "total_queries": queries_count,
                "total_logs": logs_count
            }

if __name__ == "__main__":
    if os.path.exists("data/test_db.sqlite"):
        os.remove("data/test_db.sqlite")
    db = Database("data/test_db.sqlite")
    tests_passed = 0
    # 1. Register user
    uid = db.register_user("Test User", "test@example.com", "password123")
    assert uid is not None, "Failed to register user"
    tests_passed += 1

    # 2. Duplicate email
    uid2 = db.register_user("Test User 2", "test@example.com", "password123")
    assert uid2 is None, "Failed to prevent duplicate email"
    tests_passed += 1

    # 3. Login success
    user = db.verify_login("test@example.com", "password123")
    assert user is not None and user['email'] == "test@example.com", "Failed to login"
    tests_passed += 1

    # 4. Login failure
    bad_user = db.verify_login("test@example.com", "wrongpassword")
    assert bad_user is None, "Failed to reject bad password"
    tests_passed += 1

    # 5. Save query
    qid = db.save_query(uid, "What is my GPA?", "Your GPA is 8.5.", 120.5)
    assert qid is not None, "Failed to save query"
    tests_passed += 1

    # 6. History
    history = db.get_user_history(uid)
    assert len(history) == 1 and history[0]['question'] == "What is my GPA?", "Failed to fetch history"
    tests_passed += 1

    # 7. Suspicious users
    for _ in range(6):
        db.log_action(uid, "LOGIN_FAILED", "/api/login", "127.0.0.1", 401, "Bad password")
    suspicious = db.get_suspicious_users()
    assert len(suspicious) == 1 and suspicious[0]['user_id'] == uid, "Failed to detect suspicious user"
    tests_passed += 1

    # 8. AI performance
    perf = db.get_ai_performance()
    assert len(perf) == 1 and perf[0]['query_count'] == 1, "Failed to get AI performance"
    tests_passed += 1

    # 9. Total stats
    stats = db.get_total_stats()
    assert stats['total_users'] == 1 and stats['total_queries'] == 1 and stats['total_logs'] == 6, "Failed to get total stats"
    tests_passed += 1

    # 10. SQL Injection Safety
    inj_user = db.get_user_by_email("admin@test.com' OR '1'='1")
    assert inj_user is None, "Failed SQL Injection test"
    tests_passed += 1

    if tests_passed == 10:
        print("ALL 10 TESTS PASSED")
    else:
        print(f"{tests_passed}/10 TESTS PASSED")
