import os
import json

class GroqClient:
    def __init__(self, api_key=None):
        """Initialize Groq client with API key"""
        try:
            from groq import Groq
        except ImportError:
            raise ImportError("Groq library not installed. Run: pip install groq")
        
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
        prompt = f"""Generate {num_questions} realistic {interview_type} interview questions for a {role} position.

REQUIREMENTS:
- Questions should be commonly asked in real interviews
- Mix of difficulty: {num_questions//3} Easy, {num_questions//2} Medium, rest Hard
- Questions should be specific and practical
- Avoid overly theoretical or trick questions
- Make them relevant to actual job responsibilities

Return ONLY valid JSON array (no markdown, no extra text):
[
    {{"question": "Tell me about a time when you had to [specific realistic scenario]", "difficulty": "Easy"}},
    {{"question": "How would you approach [practical problem]?", "difficulty": "Medium"}},
    {{"question": "Describe your experience with [specific skill/tool]", "difficulty": "Medium"}}
]

Make questions clear, specific, and interview-appropriate."""
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an experienced hiring manager creating realistic interview questions. Return only valid JSON array, no other text."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.8,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            # Clean up response if it contains markdown
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            if content.startswith("```"):
                content = content.replace("```", "").strip()
            
            questions = json.loads(content)
            return questions
        except Exception as e:
            print(f"Error generating questions: {e}")
            # Fallback questions
            fallback_questions = {
                "Software Engineer": [
                    {"question": "Tell me about a challenging technical problem you solved recently.", "difficulty": "Easy"},
                    {"question": "How do you approach debugging complex issues in production?", "difficulty": "Medium"},
                    {"question": "Describe your experience with version control and collaboration tools.", "difficulty": "Easy"},
                    {"question": "Explain a time when you had to optimize code for better performance.", "difficulty": "Medium"},
                    {"question": "How do you stay updated with new technologies and programming trends?", "difficulty": "Easy"}
                ],
                "Data Scientist": [
                    {"question": "Describe a data analysis project you're proud of.", "difficulty": "Easy"},
                    {"question": "How do you handle missing or messy data in your datasets?", "difficulty": "Medium"},
                    {"question": "Explain your experience with machine learning algorithms.", "difficulty": "Medium"},
                    {"question": "How do you communicate technical findings to non-technical stakeholders?", "difficulty": "Medium"},
                    {"question": "Tell me about a time when your analysis led to actionable business insights.", "difficulty": "Hard"}
                ]
            }
            
            return fallback_questions.get(role, [
                {"question": f"Tell me about your experience in {role} roles.", "difficulty": "Easy"},
                {"question": f"What challenges have you faced in {interview_type} situations?", "difficulty": "Medium"},
                {"question": f"How do you approach problem-solving in your field?", "difficulty": "Medium"},
                {"question": f"Describe a successful project you completed.", "difficulty": "Easy"},
                {"question": f"Where do you see yourself growing in this role?", "difficulty": "Medium"}
            ])[:num_questions]
    
    def evaluate_answer(self, question, answer, role, interview_type):
        """Evaluate user's answer and provide detailed feedback"""
        prompt = f"""You are a professional interview coach evaluating answers for a {role} position ({interview_type} interview).

Question: {question}
Candidate's Answer: {answer}

EVALUATION RULES:
1. Be REALISTIC and FAIR - Real interviews don't expect perfection
2. If the answer addresses the question reasonably, score 75-85+
3. Score 65-74 only if answer is vague or off-topic
4. Score below 65 only if answer is completely wrong
5. Focus on WHAT THEY DID RIGHT first
6. Give SPECIFIC, ACTIONABLE feedback

Return ONLY valid JSON (no markdown, no extra text):
{{
    "clarity_score": 80,
    "confidence_score": 80,
    "content_score": 80,
    "overall_score": 80,
    "strengths": ["Specific strength about their answer", "Another positive point", "Third good aspect"],
    "weaknesses": ["One specific area to improve", "Another constructive point"],
    "improved_answer": "An enhanced version: Start with a brief overview, then provide a specific example: 'In my previous role at [Company], I [specific action] which resulted in [specific outcome]. For instance, [concrete example with numbers/details].' This demonstrates both theoretical knowledge and practical application.",
    "tips": ["Specific actionable tip related to their answer", "Another concrete suggestion", "Third helpful tip"],
    "detailed_feedback": "Great start! You clearly understand the concept. Your answer would be even stronger with: 1) A specific real-world example from your experience, 2) Quantifiable results or metrics, 3) More technical depth. For instance, instead of saying 'I handled data', say 'I processed 10,000 records using Python pandas, reducing processing time by 40%'."
}}

Make feedback ENCOURAGING yet CONSTRUCTIVE. Help them improve, don't discourage them!"""
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an encouraging professional interview coach who provides realistic, fair evaluations. Return ONLY valid JSON with no markdown formatting or extra text."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.7,
                max_tokens=2500
            )
            
            content = response.choices[0].message.content.strip()
            # Clean up response if it contains markdown
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            if content.startswith("```"):
                content = content.replace("```", "").strip()
            
            evaluation = json.loads(content)
            
            # Ensure minimum quality scores for any reasonable answer
            answer_words = len(answer.strip().split())
            if answer_words >= 10:  # If answer has at least 10 words
                # Boost scores to be more realistic
                evaluation['clarity_score'] = max(75, evaluation.get('clarity_score', 75))
                evaluation['confidence_score'] = max(75, evaluation.get('confidence_score', 75))
                evaluation['content_score'] = max(75, evaluation.get('content_score', 75))
                evaluation['overall_score'] = max(75, evaluation.get('overall_score', 75))
            
            return evaluation
        except Exception as e:
            print(f"Error evaluating answer: {e}")
            # Much better fallback evaluation
            answer_words = len(answer.strip().split())
            
            # Calculate base score based on answer quality
            if answer_words >= 30:
                base_score = 80
            elif answer_words >= 15:
                base_score = 78
            else:
                base_score = 75
            
            return {
                "clarity_score": base_score,
                "confidence_score": base_score,
                "content_score": base_score,
                "overall_score": base_score,
                "strengths": [
                    "You directly addressed the question asked",
                    "Your answer demonstrates relevant knowledge",
                    "You showed engagement with the topic"
                ],
                "weaknesses": [
                    "Could add a specific real-world example",
                    "Consider including measurable results or metrics"
                ],
                "improved_answer": f"To enhance your answer, structure it using the STAR method: 'In my role at [Company], I faced [Situation]. My task was to [Task]. I took action by [specific steps with technical details]. This resulted in [measurable outcome - e.g., 30% improvement, $50K savings]. For example, when working on [specific project], I [detailed action] which led to [concrete result].' This format makes your experience tangible and memorable.",
                "tips": [
                    "Add specific numbers and metrics (e.g., '20% increase', '500 users')",
                    "Use concrete examples from your actual experience",
                    "Explain not just WHAT you did, but WHY and HOW",
                    "Practice the STAR method: Situation, Task, Action, Result"
                ],
                "detailed_feedback": f"Good effort! You've demonstrated understanding of the concept. To make your answer stand out: (1) Start with a brief direct answer, (2) Support it with a specific example from your experience, (3) Include quantifiable results, (4) Show the impact of your work. For instance, instead of 'I improved the process,' say 'I streamlined the data pipeline using Python, reducing processing time from 2 hours to 15 minutes, enabling daily reports instead of weekly ones.' Real examples with numbers make your answer 10x more convincing!"
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
            if content.startswith("```"):
                content = content.replace("```", "").strip()
            
            tips = json.loads(content)
            return tips
        except Exception as e:
            print(f"Error generating tips: {e}")
            return {
                "tips": [
                    "Practice answering questions out loud before typing",
                    "Use the STAR method for behavioral questions",
                    "Research the company and role before interviews",
                    "Prepare specific examples from your experience",
                    "Focus on clear, concise communication"
                ],
                "focus_areas": ["Communication", "Preparation"],
                "motivational_message": "Keep practicing! Every interview makes you better. You're making great progress!"
            }
