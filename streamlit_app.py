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
    # Reads GROQ_API_KEY from environment
    return GroqInterviewClient()


# ---------- helpers ----------

def init_state() -> None:
    default_state = {
        "session_id": None,
        "questions": [],
        "current_index": 0,
        "last_evaluation": None,
        "session_key": str(uuid.uuid4()),
    }
    for k, v in default_state.items():
        if k not in st.session_state:
            st.session_state[k] = v


def compute_badges(history: pd.DataFrame) -> List[str]:
    badges: List[str] = []
    if history.empty:
        return badges

    total_answers = len(history)
    avg_overall = history["overall"].mean()
    avg_clarity = history["clarity"].mean()
    sessions = history["session_id"].nunique()

    if total_answers >= 1:
        badges.append("🎉 First Step – You started practicing")
    if total_answers >= 10:
        badges.append("🔥 Dedicated Learner – 10+ answers logged")
    if sessions >= 3:
        badges.append("📅 Consistency Champ – 3+ sessions")
    if avg_overall >= 8:
        badges.append("⭐ Strong Overall Performer (8+)")
    if avg_clarity >= 8:
        badges.append("🗣️ Clarity Star (8+ clarity)")

    return badges


def render_progress(history: pd.DataFrame) -> None:
    if history.empty:
        st.info("No historical data yet. Finish at least one question to see analytics.")
        return

    st.subheader("📈 Progress Dashboard")

    col1, col2 = st.columns(2)

    with col1:
        # Overall score trend
        history = history.copy()
        history["idx"] = range(1, len(history) + 1)
        fig_line = px.line(
            history,
            x="idx",
            y="overall",
            markers=True,
            labels={"idx": "Answer #", "overall": "Overall Score"},
            title="Overall Score per Answer",
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with col2:
        # Average dimension scores
        avg_scores = history[["clarity", "confidence", "content_score"]].mean()
        score_df = (
            avg_scores.reset_index()
            .rename(columns={"index": "dimension", 0: "score"})
        )
        score_df.columns = ["dimension", "score"]
        fig_bar = px.bar(
            score_df,
            x="dimension",
            y="score",
            range_y=[0, 10],
            title="Average Scores by Dimension (1–10)",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Badges
    badges = compute_badges(history)
    if badges:
        st.markdown("### 🏆 Achievement Badges")
        for b in badges:
            st.success(b)


# ---------- layout ----------

init_state()

st.title("🧠 AI-Powered Virtual Interview Coach")
st.caption(
    "Practice mock interviews, get instant AI feedback, and track your progress over time."
)

# ---------- sidebar config ----------

st.sidebar.header("👤 Candidate Profile")

user_name = st.sidebar.text_input("Your name", value="")
role = st.sidebar.text_input("Target role / position", value="Software Engineer")
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
    "Number of questions in this mock interview",
    min_value=3,
    max_value=10,
    value=5,
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Tips")
st.sidebar.write(
    "- Answer using STAR method (Situation, Task, Action, Result)\n"
    "- Be specific and use real examples\n"
    "- Focus on impact and what **you** did"
)

start_clicked = st.sidebar.button("🚀 Start / Restart Mock Interview", type="primary")


# ---------- new session handling ----------

if start_clicked:
    if not user_name.strip():
        st.sidebar.error("Please enter your name before starting.")
    else:
        st.session_state.session_id = storage.create_session(user_name, role, seniority)
        client = get_groq_client()
        with st.spinner("Generating tailored interview questions with AI..."):
            st.session_state.questions = client.generate_questions(
                role=role,
                seniority=seniority,
                interview_type=interview_type,
                n_questions=n_questions,
            )
        st.session_state.current_index = 0
        st.session_state.last_evaluation = None
        st.success("Mock interview started! Scroll down to answer your first question. ✅")


# ---------- main interview area ----------

if not st.session_state.session_id:
    st.info("Configure your profile in the sidebar and click **Start / Restart**.")
    st.stop()

questions: List[Dict[str, Any]] = st.session_state.questions

if not questions:
    st.warning("No questions were generated yet. Try restarting the mock interview.")
    st.stop()

current_idx: int = st.session_state.current_index
current_idx = max(0, min(current_idx, len(questions) - 1))
st.session_state.current_index = current_idx

current_question = questions[current_idx]
question_text = current_question.get("question", "")
question_category = current_question.get("category", "general")

st.markdown("## 🎤 Current Question")
st.markdown(f"**Q{current_idx + 1}/{len(questions)} – {question_category.title()}**")
st.write(question_text)

answer_key = f"answer_{st.session_state.session_key}_{current_idx}"
answer_text = st.text_area(
    "Type your answer here (use STAR: Situation, Task, Action, Result)",
    key=answer_key,
    height=180,
)

col_left, col_right = st.columns([1, 1])

evaluate_clicked = col_left.button("🤖 Get AI Feedback", type="primary")
next_clicked = col_right.button("➡️ Next Question")


if evaluate_clicked:
    if not answer_text.strip():
        st.warning("Please type an answer before requesting feedback.")
    else:
        client = get_groq_client()
        with st.spinner("Analyzing your answer and generating feedback..."):
            evaluation = client.evaluate_answer(
                question=question_text,
                answer=answer_text,
                role=role,
                seniority=seniority,
            )

        st.session_state.last_evaluation = evaluation
        storage.log_response(
            session_id=st.session_state.session_id,
            question=question_text,
            category=question_category,
            answer=answer_text,
            evaluation=evaluation,
        )
        st.success("Feedback generated! Scroll down to see detailed insights. ✅")


if next_clicked:
    if current_idx < len(questions) - 1:
        st.session_state.current_index += 1
        st.session_state.last_evaluation = None
    else:
        st.info("You’ve reached the end of this mock interview.")
    st.rerun()



# ---------- feedback display ----------

evaluation = st.session_state.last_evaluation
if evaluation:
    st.markdown("## 📊 Instant Feedback")

    scores = evaluation.get("scores", {}) or {}
    clarity = scores.get("clarity", 0) or 0
    confidence = scores.get("confidence", 0) or 0
    content_score = scores.get("content", 0) or 0
    overall = scores.get("overall", 0.0) or 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Clarity", f"{clarity}/10")
    col2.metric("Confidence", f"{confidence}/10")
    col3.metric("Content", f"{content_score}/10")
    col4.metric("Overall", f"{overall:.1f}/10")

    # Visual bar chart
    chart_df = pd.DataFrame(
        {
            "dimension": ["Clarity", "Confidence", "Content"],
            "score": [clarity, confidence, content_score],
        }
    )
    fig = px.bar(
        chart_df,
        x="dimension",
        y="score",
        range_y=[0, 10],
        title="Score Breakdown (1–10)",
    )
    st.plotly_chart(fig, use_container_width=True)

    strengths = evaluation.get("strengths", [])
    improvements = evaluation.get("improvements", [])
    suggested_answer = evaluation.get("suggested_answer", "")
    soft_skills = evaluation.get("soft_skills", [])

    cols_fb = st.columns(2)
    with cols_fb[0]:
        st.markdown("### ✅ Strengths")
        if strengths:
            for s in strengths:
                st.write("•", s)
        else:
            st.write("No strengths returned (try another question).")

    with cols_fb[1]:
        st.markdown("### 🛠️ Improvement Opportunities")
        if improvements:
            for imp in improvements:
                st.write("•", imp)
        else:
            st.write("No specific improvements returned.")

    with st.expander("💡 See an Improved Sample Answer"):
        if suggested_answer:
            st.write(suggested_answer)
        else:
            st.write("No suggested answer generated.")

    if soft_skills:
        st.markdown("### 🌟 Soft Skills Focus")
        st.write(", ".join(soft_skills))


# ---------- history & analytics ----------

st.markdown("---")
st.header("📚 Your Progress Over Time")

if user_name.strip():
    history_df = storage.fetch_user_history(user_name.strip())
    render_progress(history_df)
else:
    st.info("Enter your name in the sidebar to see your progress history.")

