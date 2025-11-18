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
        prompt = f"""You are a professional interview coach. A candidate answered an interview question. Your job:

1. EVALUATE their answer quality (is it good, bad, nonsense, or incomplete?)
2. PROVIDE the CORRECT/IDEAL answer to the question
3. Give constructive feedback

Question: {question}
Candidate's Answer: {answer}
Role: {role}
Interview Type: {interview_type}

SCORING RULES:
- Random text/nonsense (like "gjghjgh", "test", etc): 20-30 score
- Very short/vague answer: 40-50 score
- Decent attempt but incomplete: 60-70 score
- Good answer with some details: 75-85 score
- Excellent answer with examples: 85-95 score

Return ONLY valid JSON:
{{
    "clarity_score": 25,
    "confidence_score": 25,
    "content_score": 25,
    "overall_score": 25,
    "strengths": ["If answer is good, list what they did right. If bad/nonsense, say 'N/A - Answer not relevant'"],
    "weaknesses": ["What's wrong with their answer - be specific"],
    "improved_answer": "THE CORRECT/IDEAL ANSWER TO THIS QUESTION: [Provide a complete, professional answer that demonstrates exactly how this question SHOULD be answered. Include specific examples, technical details, and structure using STAR method where appropriate. This should be a MODEL answer that the candidate can learn from.]",
    "tips": ["How to answer this TYPE of question", "What interviewers look for", "Common mistakes to avoid"],
    "detailed_feedback": "First assess if their answer was relevant. If it was nonsense/random text, clearly state that. Then explain what a good answer should include for THIS specific question."
}}

IMPORTANT: The "improved_answer" should be a COMPLETE, CORRECT answer to the question, not just suggestions. Show them exactly what they should have said!"""
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert interview coach. You must provide the CORRECT answer to interview questions, not just evaluate. When candidates give nonsense answers, give them low scores and show them the right answer."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.5,
                max_tokens=3000
            )
            
            content = response.choices[0].message.content.strip()
            # Clean up response if it contains markdown
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            if content.startswith("```"):
                content = content.replace("```", "").strip()
            
            evaluation = json.loads(content)
            
            # Don't boost scores for nonsense answers
            answer_lower = answer.lower().strip()
            answer_words = answer.split()
            
            # Check if answer is likely nonsense (repeated chars, very short, no real words)
            is_nonsense = (
                len(answer_words) <= 2 or 
                len(answer.strip()) < 10 or
                answer_lower in ['test', 'testing', 'abc', 'xyz', 'nothing', 'idk', 'i dont know', 'no idea']
            )
            
            # Only boost scores for legitimate attempts
            if not is_nonsense and len(answer_words) >= 10:
                evaluation['clarity_score'] = max(70, evaluation.get('clarity_score', 70))
                evaluation['confidence_score'] = max(70, evaluation.get('confidence_score', 70))
                evaluation['content_score'] = max(70, evaluation.get('content_score', 70))
                evaluation['overall_score'] = max(70, evaluation.get('overall_score', 70))
            
            return evaluation
        except Exception as e:
            print(f"Error evaluating answer: {e}")
            
            # Check if answer is nonsense
            answer_words = answer.strip().split()
            is_nonsense = len(answer_words) <= 2 or len(answer.strip()) < 10
            
            if is_nonsense:
                # Low score for nonsense answers
                return {
                    "clarity_score": 25,
                    "confidence_score": 25,
                    "content_score": 25,
                    "overall_score": 25,
                    "strengths": ["N/A - Answer not relevant to the question"],
                    "weaknesses": [
                        "Answer appears to be random text or not related to the question",
                        "No meaningful content provided",
                        "Does not demonstrate understanding of the topic"
                    ],
                    "improved_answer": f"CORRECT ANSWER: This question asks about '{question}'. A strong answer should include:\n\n1. **Direct Response**: Start by directly answering what was asked\n2. **Specific Example**: Share a real situation from your experience\n3. **Technical Details**: Include relevant tools, methods, or frameworks you used\n4. **Measurable Results**: Quantify the impact (e.g., '30% improvement', 'saved 10 hours/week')\n5. **Key Learnings**: What you learned or would do differently\n\nExample structured answer: 'To address [the question topic], I would [direct approach]. In my previous role, I [specific example with context]. I used [technical details/methods] which resulted in [quantifiable outcome]. This experience taught me [key insight].'",
                    "tips": [
                        "Always provide a meaningful answer related to the question",
                        "Use the STAR method: Situation, Task, Action, Result",
                        "Include specific examples from your real experience",
                        "Add numbers and metrics to demonstrate impact",
                        "Think before typing - quality over speed"
                    ],
                    "detailed_feedback": "Your answer doesn't appear to address the question. In a real interview, you need to provide relevant, thoughtful responses that demonstrate your knowledge and experience. Take time to understand what the interviewer is asking, think of a relevant example from your background, and structure your answer clearly. Even if you don't know the perfect answer, showing your thought process and problem-solving approach is valuable."
                }
            else:
                # Regular fallback for actual attempts
                base_score = 72
                return {
                    "clarity_score": base_score,
                    "confidence_score": base_score,
                    "content_score": base_score,
                    "overall_score": base_score,
                    "strengths": [
                        "You made an attempt to answer",
                        "You engaged with the question"
                    ],
                    "weaknesses": [
                        "Could provide more specific details and examples",
                        "Answer needs more structure and depth"
                    ],
                    "improved_answer": f"BETTER ANSWER FOR: '{question}'\n\nA comprehensive answer should include:\n\n**Opening**: Briefly state your direct answer or approach\n\n**Example**: 'In my previous role at [Company/Project], I encountered a similar situation where [specific scenario]. My responsibility was to [clear task].'\n\n**Action**: 'I approached this by: 1) [First step with details], 2) [Second step with technical specifics], 3) [Third step showing initiative]'\n\n**Result**: 'This led to [quantifiable outcome - e.g., 40% efficiency gain, $10K cost savings, improved user satisfaction from 3.5 to 4.7 stars]'\n\n**Learning**: 'This experience taught me [key insight] and I've since applied this approach to [related situations].'",
                    "tips": [
                        "Structure answers with clear beginning, middle, and end",
                        "Always include at least one specific, detailed example",
                        "Quantify your impact with numbers whenever possible",
                        "Show don't just tell - use concrete details",
                        "Practice STAR method for consistent structure"
                    ],
                    "detailed_feedback": "You've shown effort in responding. To significantly strengthen your answer: First, provide a direct response to what was asked. Then, support it with a detailed, real example including what you did, how you did it, and what the results were. Use specific numbers and technical details where relevant. Interviewers want to see evidence of your capabilities through concrete examples, not just statements."
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
