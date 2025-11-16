import uuid
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import streamlit as st

from groq_client import GroqInterviewClient
import storage


# ---------- page config ----------
st.set_page_config(
    page_title="AI Virtual Interview Coach",
    page_icon="🧠",
    layout="wide",
)

storage.init_db()


@st.cache_resource(show_spinner=False)
def get_groq_client() -> GroqInterviewClient:
    return GroqInterviewClient()


# ---------- helpers ----------
def init_state() -> None:
    default = {
        "session_id": None,
        "questions": [],
        "current_index": 0,
        "last_evaluation": None,
        "session_key": str(uuid.uuid4()),
    }
    for key, val in default.items():
        st.session_state.setdefault(key, val)


def compute_badges(history: pd.DataFrame) -> List[str]:
    badges = []
    if history.empty:
        return badges

    total = len(history)
    avg = history["overall"].mean()
    clarity = history["clarity"].mean()
    sessions = history["session_id"].nunique()

    if total >= 1:
        badges.append("🎉 First Answer Logged")
    if total >= 10:
        badges.append("🔥 10+ Answers Completed")
    if sessions >= 3:
        badges.append("📅 Consistency Champion")
    if avg >= 8:
        badges.append("⭐ Strong Interview Performance")
    if clarity >= 8:
        badges.append("🗣️ Excellent Clarity")

    return badges


def render_progress(history: pd.DataFrame) -> None:
    if history.empty:
        st.info("Complete at least one question to unlock analytics.")
        return

    st.subheader("📈 Performance Dashboard")

    col1, col2 = st.columns(2)

    with col1:
        history = history.copy()
        history["id"] = range(1, len(history) + 1)
        fig_line = px.line(
            history,
            x="id",
            y="overall",
            markers=True,
            title="Overall Score Trend",
            labels={"id": "Answer #"},
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with col2:
        avg_scores = history[["clarity", "confidence", "content_score"]].mean()
        df = (
            avg_scores.reset_index()
            .rename(columns={"index": "dimension", 0: "score"})
        )
        df.columns = ["dimension", "score"]
        fig_bar = px.bar(
            df,
            x="dimension",
            y="score",
            range_y=[0, 10],
            title="Average Score by Dimension",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    badges = compute_badges(history)
    if badges:
        st.markdown("### 🏆 Achievement Badges")
        for b in badges:
            st.success(b)


# ---------- UI ----------
init_state()

st.title("🧠 AI-Powered Virtual Interview Coach")
st.caption("Practice realistic mock interviews and get instant AI feedback.")

# ---------- sidebar ----------
st.sidebar.header("👤 Candidate Setup")

# NEW: Role selection dropdown
job_roles = [
    "Software Engineer",
    "Data Scientist",
    "React Developer",
    "Backend Engineer",
    "DevOps Engineer",
    "Product Manager",
    "Machine Learning Engineer",
    "Business Analyst",
    "Cybersecurity Analyst",
    "Cloud Engineer",
    "QA / Test Engineer",
    "UI/UX Designer",
    "Other (Custom Role)",
]

selected_role = st.sidebar.selectbox("Target Role / Position", job_roles)

if selected_role == "Other (Custom Role)":
    custom_role = st.sidebar.text_input("Enter Custom Role")
    role = custom_role.strip()
else:
    role = selected_role


seniority = st.sidebar.selectbox(
    "Seniority Level",
    ["Intern / Fresher", "Junior", "Mid-level", "Senior", "Lead / Manager"],
    index=2,
)

interview_type = st.sidebar.selectbox(
    "Interview Format",
    ["Behavioral", "Technical", "Mixed"],
)

n_questions = st.sidebar.slider(
    "Number of Questions",
    min_value=3,
    max_value=10,
    value=5,
)

user_name = st.sidebar.text_input("Your Name")

start_clicked = st.sidebar.button("🚀 Start / Restart Interview", type="primary")

# ---------- start / restart ----------
if start_clicked:
    if not user_name.strip():
        st.sidebar.error("Please enter your name before starting.")
    elif not role.strip():
        st.sidebar.error("Please enter a valid role.")
    else:
        st.session_state.session_id = storage.create_session(user_name, role, seniority)
        client = get_groq_client()
        with st.spinner("Generating personalized questions..."):
            st.session_state.questions = client.generate_questions(
                role=role,
                seniority=seniority,
                interview_type=interview_type,
                n_questions=n_questions,
            )
        st.session_state.current_index = 0
        st.session_state.last_evaluation = None
        st.success("Interview Started! Scroll down to begin.")

# ---------- main logic ----------
if not st.session_state.session_id:
    st.info("Configure your interview in the sidebar and click Start.")
    st.stop()

questions: List[Dict[str, Any]] = st.session_state.questions
if not questions:
    st.error("No questions received from the AI. Try restarting.")
    st.stop()

current_idx = st.session_state.current_index
current_idx = max(0, min(current_idx, len(questions) - 1))
st.session_state.current_index = current_idx

current_question = questions[current_idx]
question_text = current_question.get("question", "")
category = current_question.get("category", "general")

st.markdown("## 🎤 Current Question")
st.write(f"**Q{current_idx + 1}/{len(questions)} — {category.title()}**")
st.write(question_text)

answer_key = f"answer_{st.session_state.session_key}_{current_idx}"
answer = st.text_area("Your Answer", key=answer_key, height=180)

col1, col2 = st.columns(2)
evaluate_clicked = col1.button("🤖 Get Feedback", type="primary")
next_clicked = col2.button("➡️ Next")

if evaluate_clicked:
    if not answer.strip():
        st.warning("Write an answer before submitting.")
    else:
        client = get_groq_client()
        with st.spinner("Evaluating answer..."):
            evaluation = client.evaluate_answer(
                question=question_text,
                answer=answer,
                role=role,
                seniority=seniority,
            )
        st.session_state.last_evaluation = evaluation
        storage.log_response(
            st.session_state.session_id,
            question_text,
            category,
            answer,
            evaluation,
        )
        st.success("Feedback Ready! Scroll down ↓")

if next_clicked:
    if current_idx < len(questions) - 1:
        st.session_state.current_index += 1
        st.session_state.last_evaluation = None
    else:
        st.info("🎯 Interview completed!")
    st.rerun()  # UPDATED FIX

# ---------- feedback ----------
evaluation = st.session_state.last_evaluation
if evaluation:
    st.markdown("## 📊 AI Feedback & Review")
    scores = evaluation.get("scores", {})
    clarity = scores.get("clarity", 0)
    confidence = scores.get("confidence", 0)
    content_score = scores.get("content", 0)
    overall = scores.get("overall", 0.0)

    cols = st.columns(4)
    cols[0].metric("Clarity", f"{clarity}/10")
    cols[1].metric("Confidence", f"{confidence}/10")
    cols[2].metric("Content", f"{content_score}/10")
    cols[3].metric("Overall", f"{overall:.1f}/10")

    # Strengths & improvements
    colA, colB = st.columns(2)
    with colA:
        st.markdown("### 🌟 Strengths")
        for s in evaluation.get("strengths", []):
            st.write("•", s)

    with colB:
        st.markdown("### 🔧 Improvements")
        for s in evaluation.get("improvements", []):
            st.write("•", s)

    with st.expander("💡 Suggested Answer"):
        st.write(evaluation.get("suggested_answer", ""))

# ---------- history ----------
st.markdown("---")
st.header("📚 Your Progress")

if user_name.strip():
    history = storage.fetch_user_history(user_name.strip())
    render_progress(history)
else:
    st.info("Enter your name to view previous results.")
