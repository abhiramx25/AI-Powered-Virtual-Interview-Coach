import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Import local modules
from groq_client import GroqClient  # ✅ changed from cohere_client
import storage

# Initialize database
storage.init_db()

# Page configuration
st.set_page_config(
    page_title="Abhiram's AI Interview Coach",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #1f77b4;
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #28a745;
    }
    .info-box {
        background-color: #d1ecf1;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #17a2b8;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Initialize Groq client
    if "groq_client" not in st.session_state:
        try:
            st.session_state.groq_client = GroqClient()  # ✅ using Groq now
            st.session_state.client_ready = True
        except Exception as e:
            st.session_state.client_ready = False
            st.error(f"Failed to initialize AI: {e}")

    # Header
    st.markdown('<h1 class="main-title">🎯 Abhiram's AI Virtual Interview Coach</h1>', unsafe_allow_html=True)
    st.markdown("### Practice interviews with instant AI feedback and progress tracking")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        role = st.selectbox(
            "Select Target Role:",
            ["Data Analyst", "Software Engineer", "Business Analyst", "Product Manager", 
             "Data Scientist", "Finance Analyst", "Marketing Manager", "Project Manager"]
        )
        
        num_questions = st.slider("Number of Questions:", 1, 10, 5)
        
        st.markdown("---")
        st.header("📊 Dashboard")
        
        if st.button("View Progress Dashboard", use_container_width=True):
            st.session_state.show_dashboard = True
        
        if st.button("New Interview Session", use_container_width=True):
            st.session_state.questions = []
            st.session_state.current_question = 0
            st.session_state.answers = {}
            st.session_state.show_dashboard = False
    
    # Main content
    if not st.session_state.get("client_ready", False):
        st.error("❌ AI service not available. Please check API configuration.")
        return
    
    # Question Generation
    if not st.session_state.get("questions"):
        st.info("🚀 Ready to start your interview practice! Click the button below to generate questions.")
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            if st.button("🎯 Generate Interview Questions", use_container_width=True, type="primary"):
                with st.spinner("🤖 AI is generating role-specific questions..."):
                    try:
                        questions = st.session_state.groq_client.generate_questions(role, num_questions)  # ✅ updated
                        st.session_state.questions = questions
                        st.session_state.current_question = 0
                        st.session_state.answers = {}
                        st.success(f"✅ Generated {len(questions)} questions for {role}!")
                    except Exception as e:
                        st.error(f"Failed to generate questions: {e}")
    
    # Interview Session
    if st.session_state.get("questions"):
        questions = st.session_state.questions
        current_idx = st.session_state.current_question
        
        # Display progress
        st.progress((current_idx + 1) / len(questions))
        st.subheader(f"💬 Question {current_idx + 1} of {len(questions)}")
        
        # Current question
        st.markdown(f'<div class="info-box"><h4>{"📝 " + questions[current_idx]}</h4></div>', unsafe_allow_html=True)
        
        # Answer input
        answer = st.text_area(
            "**Your Answer:**",
            height=200,
            placeholder="Type your detailed answer here...",
            key=f"answer_{current_idx}",
            value=st.session_state.answers.get(f"answer_{current_idx}", "")
        )
        
        st.session_state.answers[f"answer_{current_idx}"] = answer
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎯 Get AI Feedback", use_container_width=True):
                if not answer.strip():
                    st.warning("Please write your answer before getting feedback.")
                else:
                    with st.spinner("🔍 Analyzing your answer..."):
                        try:
                            feedback = st.session_state.groq_client.score_and_improve(  # ✅ updated
                                questions[current_idx], answer, role
                            )
                            
                            # Save to database
                            session_data = {
                                "role": role,
                                "question": questions[current_idx],
                                "user_answer": answer,
                                "clarity": feedback.get("clarity_score", 0),
                                "confidence": feedback.get("confidence_score", 0),
                                "content": feedback.get("content_score", 0),
                                "critique": feedback.get("critique", ""),
                                "improved_answer": feedback.get("improved_answer", ""),
                                "soft_skills": feedback.get("soft_skills", [])
                            }
                            
                            storage.save_result(session_data)
                            st.session_state.last_feedback = session_data
                            st.success("✅ Feedback saved!")
                            
                        except Exception as e:
                            st.error(f"Feedback generation failed: {e}")
        
        with col2:
            if st.button("📊 Show Feedback", use_container_width=True):
                if st.session_state.get("last_feedback"):
                    st.rerun()
                else:
                    st.info("Get AI feedback first to see results.")
        
        with col3:
            if current_idx < len(questions) - 1:
                if st.button("➡️ Next Question", use_container_width=True):
                    st.session_state.current_question += 1
                    st.rerun()
            else:
                if st.button("🏁 Finish Session", use_container_width=True, type="primary"):
                    st.balloons()
                    st.success("🎉 Interview session completed! Check your progress below.")
    
    # Display Feedback
    if st.session_state.get("last_feedback"):
        st.markdown("---")
        st.subheader("📈 Feedback Results")
        
        feedback = st.session_state.last_feedback
        
        # Scores
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🗣️ Clarity", f"{feedback['clarity']}/10")
        with col2:
            st.metric("💪 Confidence", f"{feedback['confidence']}/10")
        with col3:
            st.metric("📚 Content", f"{feedback['content']}/10")
        
        # Detailed feedback
        st.subheader("📝 AI Critique")
        st.write(feedback["critique"])
        
        st.subheader("💡 Improved Answer Example")
        st.info(feedback["improved_answer"])
        
        if feedback["soft_skills"]:
            st.subheader("🌟 Soft Skills Focus")
            for skill in feedback["soft_skills"]:
                st.write(f"• {skill}")
    
    # Progress Dashboard
    if st.session_state.get("show_dashboard", False):
        st.markdown("---")
        st.subheader("📊 Progress Dashboard")
        
        data = storage.load_all()
        
        if not data.empty:
            # Convert timestamp
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            
            # Score trends
            st.subheader("📈 Performance Over Time")
            fig = px.line(
                data, 
                x='timestamp', 
                y=['clarity', 'confidence', 'content'],
                title='Your Interview Scores Trend',
                labels={'value': 'Score', 'variable': 'Metric'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Achievements
            st.subheader("🏆 Achievements")
            avg_scores = data[['clarity', 'confidence', 'content']].mean()
            
            cols = st.columns(4)
            with cols[0]:
                if avg_scores['clarity'] >= 7: st.success("🗣️ Clear Communicator")
            with cols[1]:
                if avg_scores['confidence'] >= 7: st.success("💪 Confident Speaker")
            with cols[2]:
                if avg_scores['content'] >= 7: st.success("📚 Knowledge Expert")
            with cols[3]:
                if all(score >= 8 for score in avg_scores): st.success("🏆 Interview Pro")
            
            # Recent sessions
            st.subheader("📋 Recent Practice Sessions")
            st.dataframe(data.head(8), use_container_width=True)
            
            # Export
            csv_data = data.to_csv(index=False)
            st.download_button(
                "📥 Download Progress Report",
                data=csv_data,
                file_name="interview_progress.csv",
                mime="text/csv"
            )
        else:
            st.info("No practice data yet. Complete some interview sessions to see your progress!")

if __name__ == "__main__":
    main()


