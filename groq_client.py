import os
import json
from typing import Any, Dict, List, Optional

from groq import Groq


DEFAULT_MODEL = "llama-3.3-70b-versatile"  # fast & high quality


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
        api_key = api_key or os.environ.get("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")
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is not set. "
                "Set it as an environment variable or pass api_key explicitly."
            )

        self.client = Groq(api_key=api_key)
        self.model = model
        self.temperature = temperature

    # ---------- internal helpers ----------

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
            # In case the model misbehaves, wrap in a fallback structure.
            return {"raw": content}

    # ---------- public methods ----------

    def generate_questions(
        self,
        role: str,
        seniority: str,
        interview_type: str,
        n_questions: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Returns a list of questions like:
        [
          {"id": 1, "category": "behavioral", "question": "..."},
          ...
        ]
        """
        system_prompt = (
            "You are an expert interviewer and AI interview coach. "
            "Generate realistic interview questions tailored to the candidate. "
            "Return ONLY valid JSON with a top-level key 'questions'. "
            "Each question must have: id (int), category (string), question (string). "
            "Categories can be: 'behavioral', 'technical', or 'situational'."
        )

        user_prompt = f"""
Role: {role}
Seniority: {seniority}
Interview type: {interview_type}
Number of questions: {n_questions}

Constraints:
- Start with easier questions and gradually increase difficulty.
- Mix behavioral and technical if interview_type is 'Mixed'.
- Focus on modern best practices and real-world scenarios.
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
        """
        Evaluate an answer and return a dict like:
        {
          "scores": {"clarity": 8, "confidence": 7, "content": 9, "overall": 8.0},
          "strengths": ["...", "..."],
          "improvements": ["...", "..."],
          "suggested_answer": "...",
          "soft_skills": ["communication", "ownership"],
        }
        """
        system_prompt = (
            "You are an AI interview coach. Your job is to evaluate answers and "
            "provide constructive, encouraging feedback.\n\n"
            "Return ONLY valid JSON with keys:\n"
            "- scores: object with integer fields clarity, confidence, content (1-10) "
            "  and overall (float 1-10)\n"
            "- strengths: list of short bullet strings\n"
            "- improvements: list of short bullet strings\n"
            "- suggested_answer: string with an improved sample answer\n"
            "- soft_skills: list of high-level soft skills to focus on, such as "
            "  'storytelling', 'stakeholder management', 'problem solving', etc."
        )

        user_prompt = f"""
Candidate role: {role}
Seniority: {seniority}

Interview question:
{question}

Candidate answer:
{answer}

Evaluate the answer and respond with the JSON object described above.
Be honest but supportive. Keep all text concise and practical.
"""
        data = self._chat_json(system_prompt, user_prompt)
        return data
