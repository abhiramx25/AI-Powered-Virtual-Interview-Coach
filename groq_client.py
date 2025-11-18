import os
import json

class GroqClient:
    def __init__(self, api_key=None):
        """Initialize Groq client with API key from environment or Streamlit"""

        # Import Groq SDK
        try:
            from groq import Groq
        except ImportError:
            raise ImportError("Groq library not installed. Run: pip install groq")

        # Try direct key or environment
        self.api_key = api_key or os.getenv("GROQ_API_KEY")

        # Try Streamlit secrets
        if not self.api_key:
            try:
                import streamlit as st
                self.api_key = st.secrets.get("GROQ_API_KEY")
            except Exception:
                pass

        if not self.api_key:
            raise ValueError("❌ GROQ_API_KEY not found. Please set it in Streamlit Secrets")

        # Initialize client
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"

    # ----------------------------------------------------
    # Question Generator
    # ----------------------------------------------------
    def generate_questions(self, role, interview_type, num_questions=5):
        prompt = f"""
Generate {num_questions} interview questions for a {role} applying for a {interview_type} interview.

Requirements:
- JSON array only
- Each item MUST have: question, difficulty
- Difficulty must be Easy/Medium/Hard
- Mix difficulty levels
- Must be real, practical, interview-relevant questions

Example format:
[
  {{"question": "...", "difficulty": "Easy"}},
  {{"question": "...", "difficulty": "Medium"}}
]
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.7,
                response_format={"type": "json_object"},   # 👈 CRITICAL
                max_tokens=1500,
                messages=[
                    {"role": "system", "content": "Return ONLY a JSON array of questions."},
                    {"role": "user", "content": prompt},
                ]
            )

            # Groq JSON mode always returns valid JSON
            data = json.loads(response.choices[0].message.content)
            return data

        except Exception as e:
            # Debug visibility
            try:
                import streamlit as st
                st.error(f"❌ Groq API Error: Failed to generate questions → {e}")
            except:
                print("Groq error:", e)

            # Fallback
            return [
                {"question": f"What are key responsibilities of a {role}?", "difficulty": "Easy"},
                {"question": f"What challenges commonly occur in {interview_type}?", "difficulty": "Medium"},
                {"question": f"Describe a project related to {role}.", "difficulty": "Medium"},
            ][:num_questions]

    # ----------------------------------------------------
    # Answer Evaluation
    # ----------------------------------------------------
    def evaluate_answer(self, question, answer, role, interview_type):
        prompt = f"""
You are an expert hiring manager. Evaluate this answer and return a JSON response.

Question: {question}
Answer: {answer}
Role: {role}
Type: {interview_type}

Return JSON:
{{
  "clarity_score": number 0-100,
  "confidence_score": number 0-100,
  "content_score": number 0-100,
  "overall_score": number 0-100,
  "strengths": ["..."],
  "weaknesses": ["..."],
  "improved_answer": "FULL CORRECT PERFECT ANSWER (200 words)",
  "tips": ["..."],
  "detailed_feedback": "Specific honest feedback"
}}

Rules:
- If answer is nonsense, give low score but still provide FULL correct answer
- improved_answer MUST BE a complete interview-ready answer
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.6,
                response_format={"type": "json_object"},
                max_tokens=3000,
                messages=[
                    {"role": "system", "content": "Return ONLY valid JSON. No markdown."},
                    {"role": "user", "content": prompt},
                ]
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            try:
                import streamlit as st
                st.error(f"❌ Groq API Error while evaluating: {e}")
            except:
                print("Groq error:", e)

            # Basic fallback
            return {
                "clarity_score": 50,
                "confidence_score": 50,
                "content_score": 50,
                "overall_score": 50,
                "strengths": ["Your answer was processed"],
                "weaknesses": ["The AI failed — this is fallback mode"],
                "improved_answer": f"A correct answer to '{question}' would explain the concept, use real examples, and include measurable impact.",
                "tips": ["Try again later"],
                "detailed_feedback": "AI engine fallback — likely JSON error or invalid API response"
            }

    # ----------------------------------------------------
    # Personalized Tips
    # ----------------------------------------------------
    def generate_personalized_tips(self, user_stats, role):
        prompt = f"""
Provide interview improvement advice for this user applying as {role}.

User Stats:
Clarity: {user_stats.get('avg_clarity', 0):.1f}
Confidence: {user_stats.get('avg_confidence', 0):.1f}
Content: {user_stats.get('avg_content', 0):.1f}
Overall: {user_stats.get('avg_overall', 0):.1f}
Attempts: {user_stats.get('total_questions', 0)}

Return JSON:
{{
  "tips": ["..."],
  "focus_areas": ["..."],
  "motivational_message": "..."
}}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.5,
                response_format={"type": "json_object"},
                max_tokens=1000,
                messages=[
                    {"role": "system", "content": "Return JSON only."},
                    {"role": "user", "content": prompt},
                ]
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            try:
                import streamlit as st
                st.error(f"❌ Groq API Error while generating tips: {e}")
            except:
                print("Groq error:", e)

            return {
                "tips": ["Practice more", "Use STAR method"],
                "focus_areas": ["Communication"],
                "motivational_message": "Keep going — every interview gets you closer!"
            }
