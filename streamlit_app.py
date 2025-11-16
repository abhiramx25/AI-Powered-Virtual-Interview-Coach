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
    st.session_state.setdefault("session_id", None)
    st.session_state.setdefault("questions", [])
    st.session_state.setdefault("current_index", 0)
    st.session_state.setdefault("last_evaluation", None)
    st.session_state.setdefault("session_key", str(uuid.uuid4()))


def safe_normalize_questions(data):
    """Ensures questions are always list of dicts instead of strings"""
    if not isinstance(data, list):
        return []
    final = []
    for i, q in enumerate(data):
        if isinstance(q, str):
            final.append({"id": i+1, "category": "general", "question": q})
        elif isinstance(q, dict):
            final.append(q)
    return final


# ---------- UI ----------
init_state()

st.title("🧠 AI-Powered Virtual Interview Coach")
st.caption("Practice mock interviews and get AI feedback instantly.")


# ----- SIDEBAR -----
st.sidebar.header("👤 Candidate Setup")

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
    "QA Engineer",
    "UI/UX Designer",
    "Other (Custom Role)",
]

role_selection = st.sidebar.selectbox("Target Role / Position", job_roles)

if role_selection == "Other (Custom Role)":
    custom_role = st.sidebar.text_input("Custom Role")
    role = custom_role.strip()
else:
    role = role_selection

seniority = st.sidebar.selectbox(
    "Seniority",
    ["Intern / Fresher", "Junior", "Mid-level", "Senior", "Lead / Manager"],
    index=2,
)

interview_type = st.sidebar.selectbox(
    "Interview focus",
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

if start_clicked:
    if not user_name.strip():
        st.sidebar.error("Please enter your name first.")
    elif not role.strip():
        st.sidebar.error("Please enter a valid role.")
    else:
        st.session_state.session_id = storage.create_session(user_name, role, seniority)
        client = get_groq_client()
        with st.spinner("Generating questions..."):
            raw = client.generate_questions(
                role=role,
                seniority=seniority,
                interview_type=interview_type,
                n_questions=n_questions,
            )
        st.session_state.questions = safe_normalize_questions(raw)
        st.session_state.current_index = 0
        st.session_state.last_evaluation = None
        st.success("Interview started! Scroll down.")
        st.rerun()


# ----- MAIN CONTENT -----
if not st.session_state.session_id:
    st.info("Configure interview settings in the sidebar and click Start.")
    st.stop()

questions = st.session_state.questions
if not questions:
    st.error("No valid questions returned from AI. Try restarting.")
    st.stop()

current_idx = st.session_state.current_index
current_idx = max(0, min(current_idx, len(questions) - 1))
st.session_state.current_index = current_idx
current_question = questions[current_idx]

question_text = current_question.get("question", "")
category = current_question.get("category", "general")

st.markdown("## 🎤 Interview Question")
st.write(f"**Q{current_idx + 1}/{len(questions)} — {category.title()}**")
st.write(question_text)

# answer input
answer_key = f"answer_{st.session_state.session_key}_{current_idx}"
answer = st.text_area("Your Answer (use STAR method)", key=answer_key, height=180)

# buttons
col1, col2 = st.columns(2)
evaluate_clicked = col1.button("🤖 Get AI Feedback", type="primary")
next_clicked = col2.button("➡️ Next Question")

if evaluate_clicked:
    if not answer.strip():
        st.warning("Please enter an answer before submitting.")
    else:
        client = get_groq_client()
        with st.spinner("Evaluating your answer..."):
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
        st.success("Feedback ready below!")


if next_clicked:
    if current_idx < len(questions) - 1:
        st.session_state.current_index += 1
        st.session_state.last_evaluation = None
    else:
        st.info("🎯 Interview completed!")
    st.rerun()


# ---------- FEEDBACK ----------
evaluation = st.session_state.last_evaluation
if evaluation:
    st.markdown("## 📊 AI Feedback")

    scores = evaluation.get("scores", {})
    clarity = scores.get("clarity", 0)
    confidence = scores.get("confidence", 0)
    content = scores.get("content", 0)
    overall = scores.get("overall", 0.0)

    cols = st.columns(4)
    cols[0].metric("Clarity", f"{clarity}/10")
    cols[1].metric("Confidence", f"{confidence}/10")
    cols[2].metric("Content", f"{content}/10")
    cols[3].metric("Overall", f"{overall:.1f}/10")

    st.write("### Strengths")
    for s in evaluation.get("strengths", []):
        st.write("•", s)

    st.write("### Improvements")
    for s in evaluation.get("improvements", []):
        st.write("•", s)

    with st.expander("💡 Suggested Answer"):
        st.write(evaluation.get("suggested_answer", ""))


# ---------- HISTORY ----------
st.markdown("---")
st.header("📚 Your Progress History")

if user_name.strip():
    history = storage.fetch_user_history(user_name.strip())
    if history.empty:
        st.info("Answer some questions to see analytics.")
    else:
        st.write(history)
else:
    st.info("Enter your name to view your progress.")
