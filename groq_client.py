import os
import json
from typing import Any, Dict, List, Optional
from groq import Groq

DEFAULT_MODEL = "llama-3.3-70b-versatile"

# Replace with your real key
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

    def _chat_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except Exception:
            return {"raw": content}

    def generate_questions(
        self,
        role: str,
        seniority: str,
        interview_type: str,
        n_questions: int = 5,
    ) -> List[Dict[str, Any]]:
        sys = """
You are an expert technical interviewer. Generate tailored interview questions.
Return JSON ONLY with:
{
  "questions": [
    { "id": 1, "category": "...", "question": "..."},
    ...
  ]
}
"""
        user = f"""
Role: {role}
Seniority: {seniority}
Type: {interview_type}
Count: {n_questions}
"""
        data = self._chat_json(sys, user)
        return data.get("questions", [])

    def evaluate_batch(
        self,
        q_and_a: List[Dict[str, str]],
        role: str,
        seniority: str,
    ) -> Dict[str, Any]:
        """
        Takes a list like:
        [{"question": "...", "answer": "..."}]
        and returns:
        {
          "feedback": [
            {
              "question": "...",
              "scores": {...},
              "strengths": [...],
              "improvements": [...],
              "suggested_answer": "..."
            }
          ],
          "summary": {
            "overall": 8.4,
            "strengths_overall": [...],
            "improvements_overall": [...],
            "top_skill_focus": "communication"
          }
        }
        """
        sys = """
You are an AI interview coach. Evaluate ALL answers together.
Return JSON ONLY.

Return structure:
{
  "feedback": [... individual feedback per question ...],
  "summary": {
    "overall": float,
    "strengths_overall": [...],
    "improvements_overall": [...],
    "top_skill_focus": string
  }
}
"""
        user = f"""
Role: {role}
Seniority: {seniority}

Answers:
{json.dumps(q_and_a, indent=2)}
"""
        return self._chat_json(sys, user)
