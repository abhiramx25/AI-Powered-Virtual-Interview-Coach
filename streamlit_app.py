import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime
import time

# Import custom modules
try:
    from groq_client import GroqClient
    from storage import StorageManager
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="AI Interview Coach",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .question-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .feedback-section {
        background-color: #fff;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
        margin: 0.25rem;
        animation: fadeInScale 0.5s ease-in-out;
    }
    @keyframes fadeInScale {
        from {
            opacity: 0;
            transform: scale(0.8);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }
    .stButton>button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 25px;
        font-weight: bold;
        transition: transform 0.2s;
    }
    .stButton>button:hover {
        transform: scale(1.05);
    }
    .correct-answer-box {
        background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #00838f;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'stage' not in st.session_state:
    st.session_state.stage = 'welcome'
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'current_q_index' not in st.session_state:
    st.session_state.current_q_index = 0
if 'answers' not in st.session_state:
    st.session_state.answers = []
if 'evaluations' not in st.session_state:
    st.session_state.evaluations = []

# Initialize clients
@st.cache_resource
def init_clients():
    try:
        groq = GroqClient()
        storage = StorageManager()
        return groq, storage
    except Exception as e:
        st.error(f"⚠️ Error initializing: {e}")
        st.stop()

groq_client, storage_manager = init_clients()

# Job roles and interview types
JOB_ROLES = [
    "Software Engineer",
    "Data Scientist",
    "Product Manager",
    "Business Analyst",
    "Marketing Manager",
    "UX/UI Designer"
]

INTERVIEW_TYPES = [
    "Technical",
    "Behavioral",
    "Case Study",
    "System Design",
    "Leadership"
]

def create_score_gauge(score, title):
    """Create a gauge chart for scores"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 20}},
        delta={'reference': 75},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': '#ffebee'},
                {'range': [50, 75], 'color': '#fff9c4'},
                {'range': [75, 100], 'color': '#c8e6c9'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 85
            }
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
    return fig

def create_radar_chart(clarity, confidence, content):
    """Create a radar chart for three metrics"""
    categories = ['Clarity', 'Confidence', 'Content']
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=[clarity, confidence, content],
        theta=categories,
        fill='toself',
        name='Your Scores',
        line_color='#667eea'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100])
        ),
        showlegend=False,
        height=400
    )
    return fig

def create_progress_chart(user_stats):
    """Create progress chart from user statistics"""
    if not user_stats['recent_sessions']:
        return None
    
    df = pd.DataFrame(user_stats['recent_sessions'])
    df['date'] = pd.to_datetime(df['date']).dt.date
    
    fig = px.line(df, x='date', y='score', 
                  title='Your Progress Over Time',
                  labels={'score': 'Average Score', 'date': 'Date'},
                  markers=True)
    fig.update_traces(line_color='#667eea', line_width=3)
    fig.update_layout(height=300)
    return fig

# Welcome Stage
if st.session_state.stage == 'welcome':
    st.markdown('<div class="main-header">🎯 AI-Powered Interview Coach</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Master your interview skills with personalized AI feedback</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 👋 Welcome! Let's Get Started")
        
        with st.form("user_info_form"):
            name = st.text_input("What's your name?", placeholder="Enter your full name")
            role = st.selectbox("🎯 What role are you seeking?", JOB_ROLES)
            interview_type = st.selectbox("📋 Type of interview?", INTERVIEW_TYPES)
            num_questions = st.slider("How many questions?", min_value=3, max_value=10, value=5)
            
            submitted = st.form_submit_button("🚀 Start Interview Practice", use_container_width=True)
            
            if submitted:
                if name.strip():
                    with st.spinner("Setting up your personalized interview..."):
                        # Create user and session
                        st.session_state.user_id = storage_manager.create_user(name.strip())
                        st.session_state.session_id = storage_manager.create_session(
                            st.session_state.user_id, role, interview_type, num_questions
                        )
                        st.session_state.name = name.strip()
                        st.session_state.role = role
                        st.session_state.interview_type = interview_type
                        st.session_state.num_questions = num_questions
                        
                        # Generate questions
                        st.session_state.questions = groq_client.generate_questions(
                            role, interview_type, num_questions
                        )
                        st.session_state.current_q_index = 0
                        st.session_state.answers = []
                        st.session_state.evaluations = []
                        st.session_state.stage = 'interview'
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error("Please enter your name to continue.")
        
        # Features showcase
        st.markdown("---")
        st.markdown("### ✨ What You'll Get")
        
        feat_col1, feat_col2, feat_col3 = st.columns(3)
        
        with feat_col1:
            st.markdown("#### 🤖 AI Questions")
            st.write("Role-specific questions tailored to your needs")
        
        with feat_col2:
            st.markdown("#### 📊 Instant Feedback")
            st.write("Detailed analysis with correct answers")
        
        with feat_col3:
            st.markdown("#### 🏆 Track Progress")
            st.write("Monitor improvement over time")

# Interview Stage
elif st.session_state.stage == 'interview':
    # Sidebar with progress
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.name}")
        st.markdown(f"**Role:** {st.session_state.role}")
        st.markdown(f"**Type:** {st.session_state.interview_type}")
        st.markdown("---")
        
        progress = (st.session_state.current_q_index) / st.session_state.num_questions
        st.progress(progress)
        st.markdown(f"**Question {st.session_state.current_q_index + 1} of {st.session_state.num_questions}**")
        
        st.markdown("---")
        st.markdown("### 💡 Tips")
        st.info("Use the STAR method:\n- **S**ituation\n- **T**ask\n- **A**ction\n- **R**esult")
    
    # Main interview area
    st.markdown('<div class="main-header">Interview In Progress</div>', unsafe_allow_html=True)
    
    if st.session_state.current_q_index < len(st.session_state.questions):
        current_question = st.session_state.questions[st.session_state.current_q_index]
        
        # Question display
        st.markdown(f'<div class="question-card">', unsafe_allow_html=True)
        st.markdown(f"### Question {st.session_state.current_q_index + 1}")
        st.markdown(f"**Difficulty:** {current_question.get('difficulty', 'Medium')}")
        st.markdown(f"#### {current_question['question']}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Answer input
        answer = st.text_area(
            "Your Answer:",
            height=200,
            placeholder="Type your answer here... Be specific and use examples.",
            key=f"answer_{st.session_state.current_q_index}"
        )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            if st.button("➡️ Submit Answer", use_container_width=True):
                if answer.strip():
                    st.session_state.answers.append(answer.strip())
                    st.session_state.current_q_index += 1
                    st.rerun()
                else:
                    st.error("Please provide an answer before continuing.")
        
        # Skip option
        with col3:
            if st.button("⏭️ Skip", use_container_width=True):
                st.session_state.answers.append("[Skipped]")
                st.session_state.current_q_index += 1
                st.rerun()
    
    else:
        # All questions answered - evaluate
        st.success("✅ All questions completed! Analyzing your responses...")
        
        with st.spinner("AI is evaluating your answers... This may take a moment."):
            # Evaluate all answers
            for i, (question_data, answer) in enumerate(zip(st.session_state.questions, st.session_state.answers)):
                if answer != "[Skipped]":
                    evaluation = groq_client.evaluate_answer(
                        question_data['question'],
                        answer,
                        st.session_state.role,
                        st.session_state.interview_type
                    )
                    st.session_state.evaluations.append(evaluation)
                    
                    # Save to database
                    storage_manager.save_qa_record(
                        st.session_state.session_id,
                        question_data['question'],
                        question_data.get('difficulty', 'Medium'),
                        answer,
                        evaluation
                    )
                else:
                    st.session_state.evaluations.append(None)
            
            # Update session scores
            storage_manager.update_session_scores(st.session_state.session_id)
            
            # Check for achievements
            new_badges = storage_manager.check_and_award_achievements(st.session_state.user_id)
            st.session_state.new_badges = new_badges
            
            st.session_state.stage = 'results'
            time.sleep(1)
            st.rerun()

# Results Stage
elif st.session_state.stage == 'results':
    st.markdown('<div class="main-header">📊 Your Interview Results</div>', unsafe_allow_html=True)
    
    # Calculate overall scores
    valid_evals = [e for e in st.session_state.evaluations if e is not None]
    
    if valid_evals:
        avg_clarity = sum(e['clarity_score'] for e in valid_evals) / len(valid_evals)
        avg_confidence = sum(e['confidence_score'] for e in valid_evals) / len(valid_evals)
        avg_content = sum(e['content_score'] for e in valid_evals) / len(valid_evals)
        avg_overall = sum(e['overall_score'] for e in valid_evals) / len(valid_evals)
        
        # New badges earned
        if hasattr(st.session_state, 'new_badges') and st.session_state.new_badges:
            st.balloons()
            st.success("🎉 New Achievements Unlocked!")
            badge_cols = st.columns(len(st.session_state.new_badges))
            for i, badge in enumerate(st.session_state.new_badges):
                with badge_cols[i]:
                    st.markdown(f'<div class="badge">{badge}</div>', unsafe_allow_html=True)
            st.markdown("---")
        
        # Overall score cards
        score_cols = st.columns(4)
        
        with score_cols[0]:
            st.markdown('<div class="score-card">', unsafe_allow_html=True)
            st.markdown(f"### {avg_clarity:.1f}")
            st.markdown("**Clarity**")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with score_cols[1]:
            st.markdown('<div class="score-card">', unsafe_allow_html=True)
            st.markdown(f"### {avg_confidence:.1f}")
            st.markdown("**Confidence**")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with score_cols[2]:
            st.markdown('<div class="score-card">', unsafe_allow_html=True)
            st.markdown(f"### {avg_content:.1f}")
            st.markdown("**Content**")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with score_cols[3]:
            st.markdown('<div class="score-card">', unsafe_allow_html=True)
            st.markdown(f"### {avg_overall:.1f}")
            st.markdown("**Overall**")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Visual analytics
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.plotly_chart(create_radar_chart(avg_clarity, avg_confidence, avg_content), use_container_width=True)
        
        with chart_col2:
            st.plotly_chart(create_score_gauge(avg_overall, "Overall Performance"), use_container_width=True)
        
        st.markdown("---")
        
        # Detailed feedback for each question
        st.markdown("### 📝 Detailed Feedback & Correct Answers")
        
        for i, (question_data, answer, evaluation) in enumerate(zip(
            st.session_state.questions, 
            st.session_state.answers, 
            st.session_state.evaluations
        )):
            if evaluation:
                with st.expander(f"Question {i+1}: {question_data['question'][:80]}...", expanded=(i==0)):
                    st.markdown('<div class="feedback-section">', unsafe_allow_html=True)
                    
                    # Scores
                    q_cols = st.columns(4)
                    q_cols[0].metric("Clarity", f"{evaluation['clarity_score']:.0f}")
                    q_cols[1].metric("Confidence", f"{evaluation['confidence_score']:.0f}")
                    q_cols[2].metric("Content", f"{evaluation['content_score']:.0f}")
                    q_cols[3].metric("Overall", f"{evaluation['overall_score']:.0f}")
                    
                    st.markdown("**❓ Question:**")
                    st.info(question_data['question'])
                    
                    st.markdown("**Your Answer:**")
                    st.warning(answer)
                    
                    st.markdown("**💬 Feedback:**")
                    st.write(evaluation.get('detailed_feedback', ''))
                    
                    # Strengths and Weaknesses
                    strength_col, weakness_col = st.columns(2)
                    
                    with strength_col:
                        st.markdown("**✅ Strengths:**")
                        for strength in evaluation.get('strengths', []):
                            st.markdown(f"- {strength}")
                    
                    with weakness_col:
                        st.markdown("**⚠️ Areas to Improve:**")
                        for weakness in evaluation.get('weaknesses', []):
                            st.markdown(f"- {weakness}")
                    
                    # CORRECT ANSWER - Highlighted
                    st.markdown("---")
                    st.markdown('<div class="correct-answer-box">', unsafe_allow_html=True)
                    st.markdown("### ✅ **CORRECT / IDEAL ANSWER:**")
                    st.markdown(evaluation.get('improved_answer', ''))
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Tips
                    st.markdown("**🎯 Tips:**")
                    for tip in evaluation.get('tips', []):
                        st.markdown(f"- {tip}")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Personalized recommendations
        st.markdown("### 🎓 Personalized Recommendations")
        
        user_stats = storage_manager.get_user_stats(st.session_state.user_id)
        personalized_tips = groq_client.generate_personalized_tips(user_stats, st.session_state.role)
        
        st.info(personalized_tips.get('motivational_message', ''))
        
        tip_cols = st.columns(2)
        with tip_cols[0]:
            st.markdown("**📚 Focus Areas:**")
            for area in personalized_tips.get('focus_areas', []):
                st.markdown(f"- {area}")
        
        with tip_cols[1]:
            st.markdown("**💪 Action Items:**")
            for tip in personalized_tips.get('tips', [])[:3]:
                st.markdown(f"- {tip}")
        
        # Action buttons
        st.markdown("---")
        action_col1, action_col2, action_col3 = st.columns(3)
        
        with action_col1:
            if st.button("🔄 Practice Again", use_container_width=True):
                st.session_state.stage = 'welcome'
                st.session_state.questions = []
                st.session_state.answers = []
                st.session_state.evaluations = []
                st.session_state.current_q_index = 0
                st.rerun()
        
        with action_col2:
            if st.button("📈 View Progress", use_container_width=True):
                st.session_state.stage = 'dashboard'
                st.rerun()
        
        with action_col3:
            if st.button("🏠 Home", use_container_width=True):
                st.session_state.stage = 'welcome'
                st.rerun()

# Dashboard Stage
elif st.session_state.stage == 'dashboard':
    st.markdown('<div class="main-header">📈 Your Progress Dashboard</div>', unsafe_allow_html=True)
    
    user_stats = storage_manager.get_user_stats(st.session_state.user_id)
    
    # Summary statistics
    stat_cols = st.columns(4)
    
    with stat_cols[0]:
        st.metric("Total Sessions", user_stats['total_sessions'])
    with stat_cols[1]:
        st.metric("Questions Answered", user_stats['total_questions'])
    with stat_cols[2]:
        st.metric("Average Score", f"{user_stats['avg_overall']:.1f}")
    with stat_cols[3]:
        achievements = storage_manager.get_user_achievements(st.session_state.user_id)
        st.metric("Badges Earned", len(achievements))
    
    st.markdown("---")
    
    # Progress chart
    if user_stats['recent_sessions']:
        st.markdown("### 📊 Performance Trend")
        progress_chart = create_progress_chart(user_stats)
        if progress_chart:
            st.plotly_chart(progress_chart, use_container_width=True)
    
    # Score breakdown
    score_col1, score_col2 = st.columns(2)
    
    with score_col1:
        st.markdown("### 🎯 Score Breakdown")
        scores_df = pd.DataFrame({
            'Metric': ['Clarity', 'Confidence', 'Content', 'Overall'],
            'Score': [
                user_stats['avg_clarity'],
                user_stats['avg_confidence'],
                user_stats['avg_content'],
                user_stats['avg_overall']
            ]
        })
        fig = px.bar(scores_df, x='Metric', y='Score', color='Metric',
                     color_discrete_sequence=['#667eea', '#764ba2', '#f093fb', '#4facfe'])
        fig.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    with score_col2:
        st.markdown("### 🏆 Achievements")
        if achievements:
            for achievement in achievements:
                st.markdown(f"**{achievement['name']}**")
                st.caption(achievement['description'])
        else:
            st.info("Complete more interviews to earn badges!")
    
    # Recent sessions
    st.markdown("### 📚 Recent Sessions")
    if user_stats['recent_sessions']:
        recent_df = pd.DataFrame(user_stats['recent_sessions'])
        recent_df['score'] = recent_df['score'].round(1)
        st.dataframe(recent_df[['date', 'role', 'interview_type', 'score']], use_container_width=True)
    
    st.markdown("---")
    
    if st.button("🏠 Back to Home", use_container_width=True):
        st.session_state.stage = 'welcome'
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <p>🎯 AI Interview Coach | Powered by Groq AI | Made with ❤️ using Streamlit</p>
    </div>
""", unsafe_allow_html=True)
