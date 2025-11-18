import json

class GroqClient:
    def __init__(self):
        """Initialize Groq client with a hard-coded API key."""

        # 🚨 WARNING: Do NOT commit your real keys to public code!
        self.api_key = "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"  # <-- Replace this with your actual key

        try:
            from groq import Groq
        except ImportError:
            raise ImportError("❌ Groq library not installed. Run: pip install groq")

        if not self.api_key or not self.api_key.startswith("gsk_"):
            raise ValueError("❌ Invalid or missing Groq API key. Add your key in groq_client.py")

        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"

    # -----------------------------
    # Question Generation
    # -----------------------------
    def generate_questions(self, role, interview_type, num_questions=5):
        prompt = f"""
Generate {num_questions} realistic interview questions for a {role} applying for a {interview_type} interview.

Rules:
- RETURN ONLY JSON array
- Each item must have: question, difficulty
- Difficulty = Easy / Medium / Hard
- No markdown, no explanations
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.7,
                response_format={"type": "json_object"},
                max_tokens=1500,
                messages=[
                    {"role": "system", "content": "Return ONLY a JSON array."},
                    {"role": "user", "content": prompt}
                ]
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            print("❌ Groq API Error (question generation):", e)
            return [
                {"question": f"What are key responsibilities of a {role}?", "difficulty": "Easy"},
                {"question": f"What challenges occur in a {interview_type} interview?", "difficulty": "Medium"},
                {"question": f"Describe an important skill required for a {role}.", "difficulty": "Hard"},
            ][:num_questions]

    # -----------------------------
    # Answer Evaluation
    # -----------------------------
    def evaluate_answer(self, question, answer, role, interview_type):
        prompt = f"""
Interview Question: {question}
Candidate Response: {answer}

You must:
- Score the answer
- Provide a full correct example answer (~200 words)
- Return JSON only

Return JSON:
{{
  "clarity_score": number,
  "confidence_score": number,
  "content_score": number,
  "overall_score": number,
  "strengths": ["..."],
  "weaknesses": ["..."],
  "improved_answer": "FULL CORRECT ANSWER HERE",
  "tips": ["..."],
  "detailed_feedback": "Explain what was missing and how to improve"
}}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.6,
                response_format={"type": "json_object"},
                max_tokens=3000,
                messages=[
                    {"role": "system", "content": "Return ONLY valid JSON. No markdown."},
                    {"role": "user", "content": prompt}
                ]
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            print("❌ Groq API Error (evaluation):", e)
            return {
                "clarity_score": 50,
                "confidence_score": 50,
                "content_score": 50,
                "overall_score": 50,
                "strengths": ["Fallback mode used"],
                "weaknesses": ["AI failed to generate response"],
                "improved_answer": "(AI ERROR: Fallback summary only)",
                "tips": ["Try again"],
                "detailed_feedback": "The AI failed to run. Check your API key or network."
            }

    # -----------------------------
    # Personalized Tips
    # -----------------------------
    def generate_personalized_tips(self, user_stats, role):
        prompt = f"""
Role: {role}
User performance statistics:
{user_stats}

Return JSON like:
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
                    {"role": "user", "content": prompt}
                ]
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            print("❌ Groq API Error (tips):", e)
            return {
                "tips": ["Practice more", "Use real examples", "Apply STAR method"],
                "focus_areas": ["Clarity"],
                "motivational_message": "You're improving. Keep going!"
            }
