import sqlite3
from datetime import datetime
import json

class StorageManager:
    def __init__(self, db_name="interview_coach.db"):
        """Initialize database connection"""
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Create necessary tables if they don't exist"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT NOT NULL,
                interview_type TEXT NOT NULL,
                num_questions INTEGER,
                avg_clarity REAL,
                avg_confidence REAL,
                avg_content REAL,
                avg_overall REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Questions and Answers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qa_records (
                qa_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                question TEXT NOT NULL,
                difficulty TEXT,
                answer TEXT NOT NULL,
                clarity_score REAL,
                confidence_score REAL,
                content_score REAL,
                overall_score REAL,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        """)
        
        # Achievements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                badge_name TEXT NOT NULL,
                badge_description TEXT,
                earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_user(self, name):
        """Create a new user or return existing user ID"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT user_id FROM users WHERE name = ?", (name,))
        result = cursor.fetchone()
        
        if result:
            user_id = result[0]
        else:
            cursor.execute("INSERT INTO users (name) VALUES (?)", (name,))
            user_id = cursor.lastrowid
            conn.commit()
        
        conn.close()
        return user_id
    
    def create_session(self, user_id, role, interview_type, num_questions):
        """Create a new interview session"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sessions (user_id, role, interview_type, num_questions)
            VALUES (?, ?, ?, ?)
        """, (user_id, role, interview_type, num_questions))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return session_id
    
    def save_qa_record(self, session_id, question, difficulty, answer, evaluation):
        """Save question-answer record with evaluation scores"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO qa_records 
            (session_id, question, difficulty, answer, clarity_score, confidence_score, 
             content_score, overall_score, feedback)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            question,
            difficulty,
            answer,
            evaluation.get('clarity_score', 0),
            evaluation.get('confidence_score', 0),
            evaluation.get('content_score', 0),
            evaluation.get('overall_score', 0),
            json.dumps(evaluation)
        ))
        
        conn.commit()
        conn.close()
    
    def update_session_scores(self, session_id):
        """Calculate and update average scores for a session"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT AVG(clarity_score), AVG(confidence_score), 
                   AVG(content_score), AVG(overall_score)
            FROM qa_records
            WHERE session_id = ?
        """, (session_id,))
        
        averages = cursor.fetchone()
        
        if averages:
            cursor.execute("""
                UPDATE sessions
                SET avg_clarity = ?, avg_confidence = ?, 
                    avg_content = ?, avg_overall = ?
                WHERE session_id = ?
            """, (*averages, session_id))
            
            conn.commit()
        
        conn.close()
        return averages
    
    def get_session_results(self, session_id):
        """Get all QA records for a session"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT question, difficulty, answer, clarity_score, confidence_score,
                   content_score, overall_score, feedback
            FROM qa_records
            WHERE session_id = ?
            ORDER BY qa_id
        """, (session_id,))
        
        records = cursor.fetchall()
        conn.close()
        
        results = []
        for record in records:
            results.append({
                'question': record[0],
                'difficulty': record[1],
                'answer': record[2],
                'clarity_score': record[3],
                'confidence_score': record[4],
                'content_score': record[5],
                'overall_score': record[6],
                'feedback': json.loads(record[7]) if record[7] else {}
            })
        
        return results
    
    def get_user_stats(self, user_id):
        """Get comprehensive statistics for a user"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Get session stats
        cursor.execute("""
            SELECT COUNT(*), AVG(avg_clarity), AVG(avg_confidence),
                   AVG(avg_content), AVG(avg_overall)
            FROM sessions
            WHERE user_id = ?
        """, (user_id,))
        
        session_stats = cursor.fetchone()
        
        # Get total questions answered
        cursor.execute("""
            SELECT COUNT(*)
            FROM qa_records qr
            JOIN sessions s ON qr.session_id = s.session_id
            WHERE s.user_id = ?
        """, (user_id,))
        
        total_questions = cursor.fetchone()[0]
        
        # Get recent sessions
        cursor.execute("""
            SELECT session_id, role, interview_type, avg_overall, created_at
            FROM sessions
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        """, (user_id,))
        
        recent_sessions = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_sessions': session_stats[0] or 0,
            'avg_clarity': session_stats[1] or 0,
            'avg_confidence': session_stats[2] or 0,
            'avg_content': session_stats[3] or 0,
            'avg_overall': session_stats[4] or 0,
            'total_questions': total_questions,
            'recent_sessions': [
                {
                    'session_id': s[0],
                    'role': s[1],
                    'interview_type': s[2],
                    'score': s[3],
                    'date': s[4]
                }
                for s in recent_sessions
            ]
        }
    
    def add_achievement(self, user_id, badge_name, badge_description):
        """Award an achievement badge to user"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Check if already earned
        cursor.execute("""
            SELECT achievement_id FROM achievements
            WHERE user_id = ? AND badge_name = ?
        """, (user_id, badge_name))
        
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO achievements (user_id, badge_name, badge_description)
                VALUES (?, ?, ?)
            """, (user_id, badge_name, badge_description))
            conn.commit()
            conn.close()
            return True
        
        conn.close()
        return False
    
    def get_user_achievements(self, user_id):
        """Get all achievements for a user"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT badge_name, badge_description, earned_at
            FROM achievements
            WHERE user_id = ?
            ORDER BY earned_at DESC
        """, (user_id,))
        
        achievements = cursor.fetchall()
        conn.close()
        
        return [
            {
                'name': a[0],
                'description': a[1],
                'earned_at': a[2]
            }
            for a in achievements
        ]
    
    def check_and_award_achievements(self, user_id):
        """Check user stats and award appropriate achievements"""
        stats = self.get_user_stats(user_id)
        new_badges = []
        
        # First Interview
        if stats['total_sessions'] == 1:
            if self.add_achievement(user_id, "🎯 First Steps", "Completed your first mock interview"):
                new_badges.append("🎯 First Steps")
        
        # Consistent Practice
        if stats['total_sessions'] >= 5:
            if self.add_achievement(user_id, "🔥 On Fire", "Completed 5 interview sessions"):
                new_badges.append("🔥 On Fire")
        
        if stats['total_sessions'] >= 10:
            if self.add_achievement(user_id, "⭐ Rising Star", "Completed 10 interview sessions"):
                new_badges.append("⭐ Rising Star")
        
        # High Performance
        if stats['avg_overall'] >= 85:
            if self.add_achievement(user_id, "💎 Excellence", "Achieved 85+ average score"):
                new_badges.append("💎 Excellence")
        
        # Question Master
        if stats['total_questions'] >= 25:
            if self.add_achievement(user_id, "📚 Question Master", "Answered 25+ questions"):
                new_badges.append("📚 Question Master")
        
        if stats['total_questions'] >= 50:
            if self.add_achievement(user_id, "🏆 Interview Pro", "Answered 50+ questions"):
                new_badges.append("🏆 Interview Pro")
        
        return new_badges
