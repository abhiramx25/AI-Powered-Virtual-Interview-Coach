import os
import cohere
import json
import re

class CohereClient:
    def __init__(self, api_key: str = None, model: str = "command-r-plus"):
        # Your actual API key hardcoded
        self.api_key = api_key or os.getenv("COHERE_API_KEY") or "BEEZOGpSnBdlPDxLFJZvrEFJg1rzKLmXNizOctt6"
        if not self.api_key:
            raise ValueError("Cohere API key not found.")
        
        self.client = cohere.Client(self.api_key)
        self.model = model

    def generate(self, prompt: str, max_tokens: int = 300, temperature: float = 0.2):
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.generations[0].text
        except Exception as e:
            return f"Error: {str(e)}"

    def score_and_improve(self, question: str, user_answer: str, role: str):
        prompt = f"""ROLE: {role}
QUESTION: {question}
USER ANSWER: {user_answer}

ANALYZE THIS INTERVIEW ANSWER and provide scores (1-10) and feedback.

CRITIQUE: Provide specific feedback on what was good and what needs improvement
IMPROVED_ANSWER: Write a better version of the answer
SOFT_SKILLS: List 3 soft skills to work on

RETURN AS JSON:
{{
    "clarity_score": 8,
    "confidence_score": 7,
    "content_score": 6,
    "critique": "Your answer was clear but lacked specific examples...",
    "improved_answer": "As a {role}, I would approach this by...",
    "soft_skills": ["Storytelling", "Confidence", "Specific Examples"]
}}"""

        try:
            raw_response = self.generate(prompt, max_tokens=500, temperature=0.3)
            
            # Better JSON extraction
            json_match = re.search(r'\{[^{}]*\{*[^{}]*\}[^{}]*\}', raw_response, re.DOTALL)
            if json_match:
                json_text = json_match.group()
                # Clean the JSON
                json_text = json_text.replace('\n', ' ').replace('  ', ' ')
                result = json.loads(json_text)
                return result
            
            # If JSON parsing fails, try to create meaningful feedback
            return {
                "clarity_score": max(5, min(10, len(user_answer) // 50)),
                "confidence_score": max(5, min(10, len(user_answer) // 40)),
                "content_score": max(5, min(10, len(user_answer) // 45)),
                "critique": "Try to provide more specific examples from your experience. Use the STAR method (Situation, Task, Action, Result).",
                "improved_answer": f"As a {role}, when faced with this situation, I would apply my experience in... [provide specific example]",
                "soft_skills": ["Specific Examples", "Structured Thinking", "Confidence"]
            }
            
        except Exception as e:
            return {
                "clarity_score": 6,
                "confidence_score": 6,
                "content_score": 6,
                "critique": "Focus on providing specific examples and structuring your answer clearly.",
                "improved_answer": f"Based on my experience as a {role}, I would approach this by [specific action] which would lead to [specific outcome].",
                "soft_skills": ["Specificity", "Structure", "Confidence"]
            }

    def generate_questions(self, role: str, n: int = 5):
        prompt = f"Generate {n} professional interview questions for a {role} position. Return as a JSON array."
        
        try:
            raw_response = self.generate(prompt, max_tokens=300, temperature=0.1)
            
            # Try to extract JSON array
            array_match = re.search(r'\[.*\]', raw_response, re.DOTALL)
            if array_match:
                questions = json.loads(array_match.group())
                if isinstance(questions, list):
                    return questions[:n]
            
            # Fallback questions
            default_questions = {
                "Data Analyst": [
                    "How do you clean and validate datasets?",
                    "What SQL techniques do you use for complex queries?",
                    "Describe a time your analysis impacted business decisions.",
                    "How do you handle missing data in your analysis?",
                    "What data visualization tools are you proficient with?"
                ],
                "Software Engineer": [
                    "Explain your approach to debugging production issues.",
                    "How do you ensure code quality and maintainability?",
                    "Describe your experience with version control systems.",
                    "What's your process for code reviews?",
                    "How do you stay updated with new technologies?"
                ],
                "Business Analyst": [
                    "How do you gather and document business requirements?",
                    "Describe your experience with process mapping.",
                    "How do you handle conflicting stakeholder requirements?",
                    "What tools do you use for business analysis?",
                    "How do you measure project success?"
                ],
                "Product Manager": [
                    "How do you prioritize features in a product roadmap?",
                    "Describe a successful product you launched.",
                    "How do you gather and incorporate user feedback?",
                    "What metrics do you track for product success?",
                    "How do you handle conflicts between engineering and design teams?"
                ]
            }
            
            return default_questions.get(role, [
                f"Tell me about your experience as a {role}.",
                f"What skills make you qualified for this {role} position?",
                f"Describe a challenging project you completed.",
                f"How do you handle tight deadlines?",
                f"What are your career goals as a {role}?"
            ])[:n]
            
        except Exception as e:
            return [f"Question {i+1} about {role} role" for i in range(n)]
