import os
import json
import re
import requests

class GroqClient:
    def __init__(self, api_key: str = None, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize the Groq client.
        You can pass an API key or set it in an environment variable.
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY") or "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"
        if not self.api_key:
            raise ValueError("Groq API key not found.")
        
        self.model = model
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    def generate(self, prompt: str, max_tokens: int = 300, temperature: float = 0.3):
        """
        Generate a text response from Groq’s model.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful AI interview coach."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            response = requests.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"Error: {str(e)}"

    def score_and_improve(self, question: str, user_answer: str, role: str):
        """
        Analyze an interview answer, give scores and feedback as structured JSON.
        """
        prompt = f"""ROLE: {role}
QUESTION: {question}
USER ANSWER: {user_answer}

Analyze this interview answer and respond ONLY with a valid JSON:
{{
    "clarity_score": 8,
    "confidence_score": 7,
    "content_score": 6,
    "critique": "Your answer was clear but lacked specific examples.",
    "improved_answer": "As a {role}, I would approach this by giving specific examples and measurable outcomes.",
    "soft_skills": ["Confidence", "Specificity", "Communication"]
}}"""

        try:
            raw_response = self.generate(prompt, max_tokens=600, temperature=0.4)
            json_match = re.search(r'\{[\s\S]*\}', raw_response)

            if json_match:
                clean_json = json_match.group().replace('\n', ' ').replace('  ', ' ')
                result = json.loads(clean_json)
                return result

            # fallback
            return {
                "clarity_score": 6,
                "confidence_score": 6,
                "content_score": 6,
                "critique": "Provide more structured examples to support your answer.",
                "improved_answer": f"As a {role}, I would provide more details and measurable results.",
                "soft_skills": ["Structure", "Confidence", "Specificity"]
            }

        except Exception as e:
            return {
                "clarity_score": 5,
                "confidence_score": 5,
                "content_score": 5,
                "critique": str(e),
                "improved_answer": "Error occurred while generating feedback.",
                "soft_skills": ["N/A"]
            }

    def generate_questions(self, role: str, n: int = 5):
        """
        Generate professional interview questions for a given role.
        """
        prompt = f"Generate {n} professional interview questions for a {role} position. Return only a JSON array of strings."

        try:
            raw_response = self.generate(prompt, max_tokens=400, temperature=0.3)
            array_match = re.search(r'\[.*\]', raw_response, re.DOTALL)
            if array_match:
                questions = json.loads(array_match.group())
                if isinstance(questions, list):
                    return questions[:n]
            
            # fallback
            return [
                f"Tell me about your experience as a {role}.",
                f"What skills make you suitable for the {role} position?",
                f"Describe a challenging project you handled as a {role}.",
                f"How do you manage deadlines and priorities?",
                f"What are your long-term goals as a {role}?"
            ]
        except Exception as e:
            return [f"Error: {str(e)}"]

