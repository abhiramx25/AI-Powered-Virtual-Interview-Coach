import streamlit as st
import pandas as pd
import plotly.express as px
from groq_client import GroqInterviewClient
import storage

st.set_page_config(page_title="AI Interview Coach", page_icon="🤖", layout="wide")
storage.init_db()

# ----------- Helpers ----------
def normalize_questions(qs):
    final = []
    if not isinstance(qs, list):
        return []
    for i, q in enumerate(qs):
        if isinstance(q, dict) and "question" in q:
            q["id"] = q.get("id", i+1)
            q["category"] = q.get("category", "general")
            final.append(q)
        elif isinstance(q, str):
            final.append({"id": i+1, "category": "general", "question": q})
    return final

def normalize_feedback(data):
    if not isinstance(data, dict) or "feedback" not in data:
        return [], {"overall":0, "strengths_overall":[], "improvements_overall":[], "top_skill_focus":"N/A"}
    return data.get("feedback", []), data.get("summary", {})

def safe(val, default):
    return val if val is not None else default

# ---------- Init ----------
if "state" not in st.session_state:
    st.session_state.state = "setup"
    st.session_state.questions = []
    st.session_state.answers = {}
    st.session_state.evaluation = None

client = GroqInterviewClient()

# ---------- UI ----------
if st.session_state.state == "setup":
    st.title("🎯 AI Interview Coach")

    name = st.text_input("Your Name")
    role = st.text_input("Target Role")
    seniority = st.selectbox("Level", ["Intern","Junior","Mid","Senior","Lead"])
    interview_type = st.selectbox("Type", ["Technical","Behavioral","Mixed"])
    n = st.slider("Questions", 3, 10, 3)

    if st.button("Start Interview"):
        if not name or not role:
            st.error("Enter name + role")
        else:
            st.session_state.session_id = storage.create_session(name, role, seniority)
            with st.spinner("Generating questions..."):
                qs = client.generate_questions(role, seniority, interview_type, n)
            st.session_state.questions = normalize_questions(qs)
            st.session_state.answers = {}
            st.session_state.state = "interview"
            st.rerun()

# ---------- INTERVIEW ----------
elif st.session_state.state == "interview":
    st.title("📝 Answer All Questions")

    for q in st.session_state.questions:
        st.write(f"### ❓ {q['question']}")
        st.session_state.answers[q["id"]] = st.text_area(f"Your Answer #{q['id']}", key=f"a{q['id']}")

    if st.button("✅ Finish & Evaluate"):
        pairs = [{"question": q["question"], "answer": st.session_state.answers.get(q["id"], "")} for q in st.session_state.questions]
        with st.spinner("Evaluating all answers..."):
            result = client.evaluate_batch(pairs, role, seniority)
        st.session_state.evaluation = result
        st.session_state.state = "results"
        st.rerun()

# ---------- RESULTS ----------
elif st.session_state.state == "results":
    st.title("📊 Interview Results")

    feedback, summary = normalize_feedback(st.session_state.evaluation)

    st.metric("Overall Score", f"{safe(summary.get('overall'),0):.1f}/10")

    if feedback:
        scores = []
        for f in feedback:
            sc = f.get("scores", {})
            scores.append({
                "question": f["question"],
                "clarity": safe(sc.get("clarity"),0),
                "confidence": safe(sc.get("confidence"),0),
                "content": safe(sc.get("content"),0),
                "overall": safe(sc.get("overall"),0),
            })
        df = pd.DataFrame(scores)
        fig = px.bar(df, x="question", y="overall", title="Performance by Question")
        st.plotly_chart(fig, use_container_width=True)

    st.write("## Detailed Breakdown")
    for f in feedback:
        st.write(f"### Q: {f['question']}")
        st.write(f"Score: {safe(f.get('scores',{}).get('overall'),0)}/10")

        st.write("**Strengths:**")
        for s in f.get("strengths",[]):
            st.write("✔", s)

        st.write("**Improvements:**")
        for s in f.get("improvements",[]):
            st.write("⚠", s)

        with st.expander("Suggested Answer"):
            st.write(f.get("suggested_answer",""))

    st.write("## Summary")
    st.write("### Strengths:")
    for s in summary.get("strengths_overall",[]):
        st.write("✔", s)

    st.write("### Improvements:")
    for s in summary.get("improvements_overall",[]):
        st.write("⚠", s)

    st.write("### Top Focus Skill:", summary.get("top_skill_focus","N/A"))

    st.button("🔁 Restart", on_click=lambda: st.session_state.update({"state":"setup"}))
