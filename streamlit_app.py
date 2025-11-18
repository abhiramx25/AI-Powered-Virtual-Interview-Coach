import os
import json

# API KEY - Add your Groq API key here
GROQ_API_KEY = "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"

class GroqClient:
    def __init__(self, api_key=None):
        """Initialize Groq client with API key"""
        try:
            from groq import Groq
        except ImportError:
            raise ImportError("Groq library not installed. Run: pip install groq")
        
        # Use provided key, or the one defined above, or from environment, or from Streamlit secrets
        self.api_key = api_key or GROQ_API_KEY or os.getenv("GROQ_API_KEY")
        
        # If still no key, try Streamlit secrets
        if not self.api_key:
            try:
                import streamlit as st
                self.api_key = st.secrets.get("GROQ_API_KEY")
            except:
                pass
        
        if not self.api_key:
            raise ValueError("⚠️ GROQ_API_KEY not found. Please add it in groq_client.py or Streamlit Secrets.")
        
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
        prompt = f"""You are an expert interview coach. You must:

1. Evaluate the candidate's answer honestly
2. Provide the COMPLETE, CORRECT answer to the question (not suggestions, but the ACTUAL full answer)

Interview Question: {question}
Candidate's Answer: {answer}
Role: {role}
Type: {interview_type}

SCORING:
- Random/nonsense text: 15-30 score
- Very short/incomplete: 40-60 score  
- Decent attempt: 65-75 score
- Good with examples: 75-85 score
- Excellent detailed answer: 85-95 score

Return ONLY this JSON format:
{{
    "clarity_score": <number>,
    "confidence_score": <number>,
    "content_score": <number>,
    "overall_score": <number>,
    "strengths": ["What was good, or 'N/A' if nonsense"],
    "weaknesses": ["What was wrong/missing"],
    "improved_answer": "THE COMPLETE CORRECT ANSWER TO THE QUESTION: [Write the full, proper answer here as if YOU are answering the interview question perfectly. Include definitions, examples, technical details, real-world scenarios, and specific numbers. Make this a FULL answer that demonstrates mastery of the topic, not just tips or suggestions. This should be 100-200 words of actual content answering the question.]",
    "tips": ["General tips for this question type"],
    "detailed_feedback": "Honest assessment of their answer and what the correct answer should contain"
}}

CRITICAL: The "improved_answer" must be a COMPLETE, STANDALONE answer that fully addresses the question with specific details, examples, and technical depth. Write it as if you are the candidate giving a perfect answer in an interview."""
        
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert interviewer who provides COMPLETE, CORRECT answers to questions. When evaluating, you must write out the full proper answer, not just give suggestions. Be honest with scoring - give low scores for nonsense answers."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.6,
                max_tokens=3500
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
            
            # Fallback - provide complete correct answer
            answer_words = answer.strip().split()
            is_nonsense = len(answer_words) <= 3 or len(answer.strip()) < 15
            
            if is_nonsense:
                base_score = 20
            elif len(answer_words) < 10:
                base_score = 50
            else:
                base_score = 70
            
            # Generate a proper answer based on the question keywords
            question_lower = question.lower()
            
            # Create context-aware correct answer
            if "difference" in question_lower or "compare" in question_lower:
                correct_answer_template = f"To answer '{question}': The key differences are: (1) First aspect - [Definition and example with specific details], (2) Second aspect - [Contrasting approach with real-world application], (3) Third aspect - [Practical implications]. For instance, in my experience working on [specific project], I used [specific approach] which resulted in [quantifiable outcome like 40% improvement or $50K savings]. The main distinction is [core differentiator with technical explanation]."
            elif "how would you" in question_lower or "how do you" in question_lower:
                correct_answer_template = f"To answer '{question}': My approach would be: (1) First, I would [specific action with reasoning], (2) Then, I'd [detailed next step with tools/methods], (3) Finally, [completion strategy with metrics]. For example, when I faced a similar situation at [Company/Project], I [specific detailed action taken], using [specific tools/technologies], which achieved [measurable result - e.g., reduced time by 60%, increased efficiency by 35%]. This systematic approach ensures [key benefit]."
            elif "what is" in question_lower or "define" in question_lower or "explain" in question_lower:
                correct_answer_template = f"To answer '{question}': This refers to [clear definition with technical accuracy]. In practice, it works by [mechanism/process explanation with details]. The key characteristics are: [3-4 specific points with examples]. For instance, in a real-world scenario, [concrete example with company/project context], this was implemented by [specific implementation details], resulting in [quantifiable outcomes like performance metrics, user impact, or business value]. The significance is [why this matters in professional context]."
            elif "experience" in question_lower or "tell me about" in question_lower:
                correct_answer_template = f"To answer '{question}': In my previous role at [Company/Project name], I encountered [specific situation that relates to the question]. My responsibility was to [clear task description]. I approached this by: (1) [First detailed action], (2) [Second specific step with tools used], (3) [Third implementation detail]. This resulted in [specific measurable outcomes - e.g., 45% performance improvement, processed 10,000+ records daily, saved 15 hours weekly]. The key learning was [professional insight], which I've since applied to [related situations with outcomes]."
            else:
                correct_answer_template = f"To answer '{question}': The comprehensive answer includes: (1) [Core concept explanation with technical details], (2) [Practical application with real-world example], (3) [Specific outcomes or benefits with metrics]. For example, when working on [specific project context], I implemented [detailed approach] using [specific tools/technologies], which led to [quantifiable results like 30% efficiency gain or improved accuracy from 75% to 92%]. This demonstrates [key professional competency] through [concrete evidence]."
            
            return {
                "clarity_score": base_score,
                "confidence_score": base_score,
                "content_score": base_score,
                "overall_score": base_score,
                "strengths": ["N/A - Answer not adequate"] if is_nonsense else ["You attempted to address the topic"],
                "weaknesses": [
                    "Answer is not relevant to the question" if is_nonsense else "Lacks specific details and examples",
                    "Missing technical depth and concrete examples",
                    "No measurable outcomes or real-world context provided"
                ],
                "improved_answer": correct_answer_template,
                "tips": [
                    "Always structure your answer with: Definition → Example → Result",
                    "Include specific numbers and metrics (e.g., '40% increase', '500 users')",
                    "Use the STAR method for behavioral questions",
                    "Mention specific tools, technologies, or frameworks",
                    "Quantify your impact with measurable outcomes"
                ],
                "detailed_feedback": f"{'Your answer appears to be random text or incomplete.' if is_nonsense else 'Your answer needs more substance.'} For this question, you should provide: (1) A clear, direct response to what's being asked, (2) A specific example from your real experience with detailed context, (3) Technical specifics or methodologies used, (4) Quantifiable results that demonstrate impact. Strong answers in interviews always combine theoretical knowledge with practical evidence. See the improved answer above for a complete response to this question."
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
