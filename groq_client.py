import os
from groq import Groq
import json

class GroqClient:
    def __init__(self, api_key=None):
        """Initialize Groq client with API key"""
        # Try to get API key from multiple sources
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        
        # If no key yet, try Streamlit secrets
        if not self.api_key:
            try:
                import streamlit as st
                self.api_key = st.secrets.get("GROQ_API_KEY")
            except:
                pass
        
        if not self.api_key:
            raise ValueError("⚠️ GROQ_API_KEY not found. Please add it in Streamlit Secrets.")
        
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
        prompt = f"""As an expert and ENCOURAGING interviewer, evaluate this answer for a {role} position in a {interview_type} interview.

Question: {question}
Answer: {answer}

IMPORTANT GUIDELINES:
- Be POSITIVE and CONSTRUCTIVE in your evaluation
- Recognize good points in the answer
- If the answer demonstrates understanding, score it fairly (75-85+ range)
- Only give low scores (below 70) if the answer is completely off-topic or very poor
- Focus on what the candidate did RIGHT, then suggest improvements
- Be realistic - most interview answers are good enough, not perfect

Provide evaluation in JSON format:
{{
    "clarity_score": <0-100>,
    "confidence_score": <0-100>,
    "content_score": <0-100>,
    "overall_score": <0-100>,
    "strengths": ["specific strength 1", "specific strength 2", "specific strength 3"],
    "weaknesses": ["constructive area 1", "constructive area 2"],
    "improved_answer": "An enhanced version that builds on their answer with more detail and structure...",
    "tips": ["actionable tip 1", "actionable tip 2", "actionable tip 3"],
    "detailed_feedback": "Start with what they did well, then provide constructive suggestions for improvement. Be encouraging!"
}}

Remember: Be fair, encouraging, and recognize the effort. Most decent answers should score 75-85+."""
        
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
            
            # Ensure scores are reasonable - boost low scores if answer has substance
            if len(answer.strip()) > 50:  # If answer has decent length
                if evaluation['overall_score'] < 70:
                    evaluation['overall_score'] = min(75, evaluation['overall_score'] + 10)
                if evaluation['clarity_score'] < 70:
                    evaluation['clarity_score'] = min(75, evaluation['clarity_score'] + 10)
                if evaluation['confidence_score'] < 70:
                    evaluation['confidence_score'] = min(75, evaluation['confidence_score'] + 10)
                if evaluation['content_score'] < 70:
                    evaluation['content_score'] = min(75, evaluation['content_score'] + 10)
            
            return evaluation
        except Exception as e:
            print(f"Error evaluating answer: {e}")
            # Improved fallback evaluation based on answer length and quality
            answer_length = len(answer.strip())
            base_score = 75 if answer_length > 50 else 65
            
            return {
                "clarity_score": base_score,
                "confidence_score": base_score,
                "content_score": base_score,
                "overall_score": base_score,
                "strengths": [
                    "You attempted to answer the question",
                    "Your response shows effort and engagement"
                ],
                "weaknesses": [
                    "Could expand with more specific examples",
                    "Consider adding more technical details"
                ],
                "improved_answer": "Consider structuring your answer with: 1) Direct response to the question, 2) Specific example from your experience, 3) Results or lessons learned. This makes your answer more impactful and memorable.",
                "tips": [
                    "Use the STAR method (Situation, Task, Action, Result)",
                    "Practice speaking out loud before typing",
                    "Include specific numbers and metrics when possible"
                ],
                "detailed_feedback": "You've made a good start! Your answer shows understanding of the question. To make it even stronger, try adding specific examples from your experience and concrete details. Remember, interviewers love to hear real stories and measurable results."
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
