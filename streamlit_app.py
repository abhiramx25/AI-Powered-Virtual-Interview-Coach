import uuid
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import streamlit as st

from groq_client import GroqInterviewClient
import storage


st.set_page_config(page_title="AI Interview Coach", page_icon="🤖", layout="wide")
storage.init_db()


# ---------------- UTILS ----------------
@st.cache_resource
def get_client():
    return GroqInterviewClient()


def init_state():
    st.session_state.setdefault("session_id", None)
    st.session_state.setdefault("questions", [])
    st.session_state.setdefault("answers", {})
    st.session_state.setdefault("finished", False)
    st.session_state.setdefault("evaluation", None)


init_state()


# ---------------- SIDEBAR ----------------
st.sidebar.header("Interview Settings")

job_roles = [
    "Software Engineer",
    "React Developer",
    "Python Developer",
    "Data Scientist",
    "ML Engineer",
    "Backend Engineer",
    "Cloud Engineer",
    "Cybersecurity Analyst",
    "Product Manager",
    "Business Analyst",
    "Other (Custom)",
]

role_sel = st.sidebar.selectbox("Target Role", job_roles)
role = st.sidebar.text_input("Custom Role") if role_sel == "Other (Custom)" else role_sel

seniority = st.sidebar.selectbox(
    "Level", ["Intern", "Junior", "Mid", "Senior", "Lead"], index=2
)

interview_type = st.sidebar.selectbox("Interview Type", ["Technical", "Behavioral", "Mixed"])
n_q = st.sidebar.slider("Number of Questions", 3, 10, 3)

name = st.sidebar.text_input("Your Name")
start = st.sidebar.button("🚀 Start Interview", type="primary")


if start:
    if not name or not role:
        st.sidebar.error("Name and role required.")
    else:
        st.session_state.session_id = storage.create_session(name, role, seniority)
        with st.spinner("Generating questions..."):
            questions = get_client().generate_questions(role, seniority, interview_type, n_q)
        st.session_state.questions = questions
        st.session_state.answers = {}
        st.session_state.finished = False
        st.session_state.evaluation = None
        st.rerun()


# ---------- NO SESSION ----------
if not st.session_state.session_id:
    st.info("Set up your interview in the sidebar to begin.")
    st.stop()


# ---------- QUESTIONS ----------
if not st.session_state.finished:
    st.title("🎤 Interview In Progress")

    for q in st.session_state.questions:
        st.write(f"### ❓ {q['question']}")
        st.session_state.answers[q['id']] = st.text_area(
            f"Answer for Q{q['id']}",
            key=f"answer_{q['id']}",
            height=120,
        )

    finish = st.button("✅ Finish & Submit All Answers", type="primary")

    if finish:
        q_and_a = []
        for q in st.session_state.questions:
            q_and_a.append({
                "question": q["question"],
                "answer": st.session_state.answers.get(q["id"], "")
            })

        with st.spinner("Evaluating all answers..."):
            evaluation = get_client().evaluate_batch(q_and_a, role, seniority)

        st.session_state.evaluation = evaluation
        st.session_state.finished = True
        st.rerun()

else:
    st.title("📊 Interview Results")

    data = st.session_state.evaluation
    feedback = data.get("feedback", [])
    summary = data.get("summary", {})

    overall = summary.get("overall", 0)

    st.metric("Overall Score", f"{overall:.1f}/10")

    # Radar / Spider chart
    radar_df = pd.DataFrame([
        {"skill": "Clarity", "score": f["scores"]["clarity"]} for f in feedback
    ] + [
        {"skill": "Confidence", "score": f["scores"]["confidence"]} for f in feedback
    ] + [
        {"skill": "Content", "score": f["scores"]["content"]} for f in feedback
    ])
    fig = px.bar(radar_df, x="skill", y="score", range_y=[0,10], title="Score Distribution")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📌 Detailed Feedback")
    for f in feedback:
        st.write(f"### Q: {f['question']}")
        st.write(f"**Score:** {f['scores']['overall']}/10")
        st.write("**Strengths:**")
        for s in f["strengths"]:
            st.write("✔", s)
        st.write("**Improvements:**")
        for s in f["improvements"]:
            st.write("⚠", s)
        with st.expander("Suggested Answer"):
            st.write(f["suggested_answer"])

    st.subheader("📌 Summary Recommendations")
    st.write("### Strengths")
    for x in summary.get("strengths_overall", []):
        st.write("✔", x)

    st.write("### Improvements")
    for x in summary.get("improvements_overall", []):
        st.write("⚠", x)

    st.success(f"⭐ Recommended Focus Area: {summary.get('top_skill_focus', 'N/A')}")

    st.markdown("---")
    st.button("🔄 Restart", type="secondary", on_click=lambda: st.session_state.update({"finished": False}))
