import os
import json
from typing import Any, Dict, List, Optional
from groq import Groq

DEFAULT_MODEL = "llama-3.3-70b-versatile"

# Update this
GROQ_API_KEY = "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"


class GroqInterviewClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.3,
    ) -> None:
        self.api_key = api_key or GROQ_API_KEY
        if not self.api_key or self.api_key == "YOUR_KEY_HERE":
            raise ValueError("Missing Groq API Key")
        self.client = Groq(api_key=self.api_key)
        self.model = model
        self.temperature = temperature

    def safe_json(self, text: str):
        try:
            return json.loads(text)
        except:
            return None

    def chat_json(self, system_prompt, user_prompt):
        res = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return self.safe_json(res.choices[0].message.content)

    def generate_questions(self, role, seniority, interview_type, n_questions=5):
        sys = """
You generate interview questions. RETURN JSON ONLY structured like:
{
  "questions": [
    {"id": 1, "category": "behavioral", "question": "Tell me about..."}
  ]
}
"""
        user_prompt = f"Role: {role}\nSeniority: {seniority}\nType: {interview_type}\nCount: {n_questions}"

        result = self.chat_json(sys, user_prompt)
        if not result or "questions" not in result:
            # fallback
            return [{"id": i+1, "category": "general", "question": f"Example question {i+1}"} for i in range(n_questions)]
        return result["questions"]

    def evaluate_batch(self, q_and_a, role, seniority):
        sys = """
You evaluate ALL answers at once. RETURN JSON ONLY structured like:
{
  "feedback": [
    {
      "question": "...",
      "scores": {"clarity":7,"confidence":8,"content":6,"overall":7.0},
      "strengths": [...],
      "improvements": [...],
      "suggested_answer": "..."
    }
  ],
  "summary": {
    "overall": 7.5,
    "strengths_overall": [...],
    "improvements_overall": [...],
    "top_skill_focus": "communication"
  }
}
"""
        user = f"""
Role: {role}
Seniority: {seniority}
Answers:
{json.dumps(q_and_a)}
"""

        result = self.chat_json(sys, user)
        if not result:
            return {
                "feedback": [],
                "summary": {"overall": 0, "strengths_overall": [], "improvements_overall": [], "top_skill_focus": "N/A"}
            }
        return result
