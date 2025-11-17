import os
from groq import Groq
import json

class GroqClient:
    def __init__(self, api_key=None):
        """Initialize Groq client with API key"""
        # Add your Groq API key here
        GROQ_API_KEY = "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"  # Replace with your actual API key
        
        self.api_key = api_key or GROQ_API_KEY or os.getenv("GROQ_API_KEY")
        if not self.api_key or self.api_key == "your_groq_api_key_here":
            raise ValueError("GROQ_API_KEY not found. Please add your API key in groq_client.py")
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"
    
    def generate_questions(self, role, interview_type, num_questions=5):
        """Generate interview questions based on role and type"""
        prompt = f"""Generate {num_questions} {interview_type} interview questions for a {role} position.
        
        Return ONLY a JSON array of questions with this exact format:
        [
            {{"question": "Question text here", "difficulty": "Easy/Medium/Hard"}},
            {{"question": "Question text here", "difficulty": "Easy/Medium/Hard"}}
        ]
        
        Make questions realistic, relevant, and progressively challenging."""
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert interviewer. Return only valid JSON, no other text."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.7,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            # Clean up response if it contains markdown
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            
            questions = json.loads(content)
            return questions
        except Exception as e:
            print(f"Error generating questions: {e}")
            # Fallback questions
            return [
                {"question": f"Tell me about your experience with {role} responsibilities.", "difficulty": "Easy"},
                {"question": f"What challenges have you faced in {interview_type} scenarios?", "difficulty": "Medium"},
                {"question": f"How would you handle a complex {role} situation?", "difficulty": "Hard"}
            ]
    
    def evaluate_answer(self, question, answer, role, interview_type):
        """Evaluate user's answer and provide detailed feedback"""
        prompt = f"""As an expert interviewer, evaluate this answer for a {role} position in a {interview_type} interview.

Question: {question}
Answer: {answer}

Provide a detailed evaluation in the following JSON format:
{{
    "clarity_score": <0-100>,
    "confidence_score": <0-100>,
    "content_score": <0-100>,
    "overall_score": <0-100>,
    "strengths": ["strength1", "strength2"],
    "weaknesses": ["weakness1", "weakness2"],
    "improved_answer": "A better version of the answer...",
    "tips": ["tip1", "tip2", "tip3"],
    "detailed_feedback": "Comprehensive feedback paragraph..."
}}

Be constructive, specific, and encouraging. Scores should reflect actual quality."""
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert interview coach providing constructive feedback. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.5,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            
            evaluation = json.loads(content)
            return evaluation
        except Exception as e:
            print(f"Error evaluating answer: {e}")
            # Fallback evaluation
            return {
                "clarity_score": 70,
                "confidence_score": 70,
                "content_score": 70,
                "overall_score": 70,
                "strengths": ["Good attempt at answering"],
                "weaknesses": ["Could provide more details"],
                "improved_answer": "Consider expanding on your points with specific examples.",
                "tips": ["Practice more", "Use STAR method", "Be more specific"],
                "detailed_feedback": "Your answer shows understanding but could benefit from more concrete examples."
            }
    
    def generate_personalized_tips(self, user_stats, role):
        """Generate personalized improvement tips based on user's performance"""
        prompt = f"""Based on this user's interview performance statistics for a {role} position, provide personalized advice:

Average Scores:
- Clarity: {user_stats.get('avg_clarity', 0):.1f}
- Confidence: {user_stats.get('avg_confidence', 0):.1f}
- Content: {user_stats.get('avg_content', 0):.1f}
- Overall: {user_stats.get('avg_overall', 0):.1f}

Total Sessions: {user_stats.get('total_sessions', 0)}
Total Questions: {user_stats.get('total_questions', 0)}

Provide 5 specific, actionable tips to improve their interview performance. Return as JSON:
{{
    "tips": ["tip1", "tip2", "tip3", "tip4", "tip5"],
    "focus_areas": ["area1", "area2"],
    "motivational_message": "Encouraging message..."
}}"""
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a supportive career coach. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.6,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            
            tips = json.loads(content)
            return tips
        except Exception as e:
            print(f"Error generating tips: {e}")
            return {
                "tips": [
                    "Practice answering questions out loud",
                    "Use the STAR method for behavioral questions",
                    "Research the company before interviews",
                    "Prepare specific examples from your experience",
                    "Focus on clear, concise communication"
                ],
                "focus_areas": ["Communication", "Preparation"],
                "motivational_message": "Keep practicing! Every interview makes you better."
            }

