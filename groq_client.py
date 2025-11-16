import os
import json
from typing import Any, Dict, List, Optional
from groq import Groq

DEFAULT_MODEL = "llama-3.3-70b-versatile"

# -------------------------------------------
# 🔥 Your API key here (hardcoded)
# ⚠️ REPLACE THIS VALUE WITH YOUR REAL KEY
# ⚠️ DO NOT COMMIT YOUR REAL KEY TO GITHUB
GROQ_API_KEY = "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"
# -------------------------------------------


class GroqInterviewClient:
    """
    Thin wrapper around Groq chat API for:
    - generating interview questions
    - evaluating answers
    - creating improvement tips
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.3,
    ) -> None:
        # If user passes an API key use it,
        # else use the hardcoded key from above
        self.api_key = api_key or GROQ_API_KEY

        if not self.api_key or self.api_key == "YOUR_GROQ_API_KEY_HERE":
            raise ValueError(
                "Groq API key is missing. Please set GROQ_API_KEY variable "
                "in this file or pass it to GroqInterviewClient()."
            )

        self.client = Groq(api_key=self.api_key)
        self.model = model
        self.temperature = temperature

    # ---------- internal method ----------

    def _chat_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Send a chat completion request that MUST return valid JSON."""
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
        except json.JSONDecodeError:
            return {"raw": content}

    # ---------- public API ----------

    def generate_questions(
        self,
        role: str,
        seniority: str,
        interview_type: str,
        n_questions: int = 5,
    ) -> List[Dict[str, Any]]:
        system_prompt = (
            "You are an expert interviewer and AI interview coach. "
            "Generate realistic interview questions tailored to the candidate. "
            "Return ONLY valid JSON with a top-level key 'questions'."
        )

        user_prompt = f"""
Role: {role}
Seniority: {seniority}
Interview type: {interview_type}
Number of questions: {n_questions}
"""

        data = self._chat_json(system_prompt, user_prompt)
        return data.get("questions", [])

    def evaluate_answer(
        self,
        question: str,
        answer: str,
        role: str,
        seniority: str,
    ) -> Dict[str, Any]:
        system_prompt = (
            "You are an AI interview coach. Your job is to evaluate answers and "
            "provide constructive, supportive feedback.\n"
            "Return ONLY valid JSON."
        )

        user_prompt = f"""
Candidate role: {role}
Seniority: {seniority}

Interview question:
{question}

Candidate answer:
{answer}
"""

        return self._chat_json(system_prompt, user_prompt)
