import streamlit as st
import json
from streamlit_drawable_canvas import st_canvas
from streamlit_ketcher import st_ketcher
from PIL import Image
from rdkit import Chem
from rdkit.Chem import inchi

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="Reactive Intermediates Revision", layout="centered")
st.title("Reactive Intermediates Revision")

# -------------------------
# SIDEBAR (UNCHANGED)
# -------------------------
try:
    st.sidebar.image("images/BNNLab_v3.png")
except:
    st.sidebar.write("🔬 Reactive Intermediate Revision")

st.sidebar.header("Acknowledgements")
st.sidebar.write("This web tool was built to support chemistry learning in Reactive Intermediate topic, University of Leeds.")

st.sidebar.header("Disclaimer")
st.sidebar.write("This software was developed by BNNLab, with all rights reserved. It is offered 'as is', without warranty of any kind, express or implied. The user assumes all risk for any malfunctions, errors, or damages resulting from the use of this software. The creator is not responsible for any direct or indirect loss arising from its use.")

# -------------------------
# LOAD DATA
# -------------------------
with open("questions.json") as f:
    lessons = json.load(f)

# -------------------------
# SESSION STATE
# -------------------------
def init():
    defaults = {
        "lesson_index": None,
        "question_index": 0,
        "xp": 0,
        "hearts": 5,
        "streak": 0,
        "answered": False,
        "show_next": False,
        "lesson_mode": "learn",
        "wrong_topics": [],
        "answered_questions": []
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init()

# -------------------------
# HEADER
# -------------------------
# We're saving these scores and user accounts for later
#col1, col2, col3 = st.columns(3)
#col1.metric("❤️ Hearts", st.session_state.hearts)
#col2.metric("⭐ XP", st.session_state.xp)
#col3.metric("🔥 Streak", st.session_state.streak)

# -------------------------
# LESSON SELECT
# -------------------------
st.subheader("📚 Choose a Lesson")

for i, lesson in enumerate(lessons):
    if st.button(f"Lesson {lesson['level']}: {lesson['lesson']}", key=f"lesson_{i}"):
        st.session_state.lesson_index = i
        st.session_state.question_index = 0
        st.session_state.lesson_mode = "learn"
        st.session_state.answered = False
        st.session_state.show_next = False
        st.session_state.wrong_topics = []
        st.session_state.answered_questions = []

# Stop until lesson is selected
if st.session_state.lesson_index is None:
    st.info("👆 Please choose a lesson to begin.")
    st.stop()

# -------------------------
# HELPER FUNCTION
# -------------------------
def smiles_equal(s1, s2):
    try:
        m1 = Chem.MolFromSmiles(s1)
        m2 = Chem.MolFromSmiles(s2)
        return Chem.MolToInchi(m1) == Chem.MolToInchi(m2)
    except:
        return False

# -------------------------
# CURRENT LESSON
# -------------------------
lesson = lessons[st.session_state.lesson_index]

st.divider()
st.subheader(lesson["lesson"])

# =========================
# LEARNING MODE
# =========================
if st.session_state.lesson_mode == "learn":

    st.header("📘 Quick recap")

    content = lesson.get("content", {})

    for p in content.get("text", []):
        st.write(p)

    for img_path in content.get("images", []):
        try:
            st.image(Image.open(img_path))
        except:
            st.warning(f"Image not found: {img_path}")

    if st.button("🚀 Start Practice"):
        st.session_state.lesson_mode = "practice"
        st.session_state.question_index = 0
        st.session_state.answered = False
        st.session_state.show_next = False
        st.session_state.wrong_topics = []
        st.session_state.answered_questions = []

# =========================
# PRACTICE MODE
# =========================
elif st.session_state.lesson_mode == "practice":

    questions = lesson["questions"]
    q = questions[st.session_state.question_index]

    st.write(f"Q{st.session_state.question_index + 1}/{len(questions)}")
    st.write(q["question_text"])

    if q.get("question_image"):
        try:
            st.image(Image.open(q["question_image"]))
        except:
            st.warning("Image not found")

    unique_key = f"{st.session_state.lesson_index}_{st.session_state.question_index}_{q['id']}"

    user_answer = None

    # INPUT TYPES
    if q["type"] in ["multiple_choice", "image_label"]:
        user_answer = st.radio(
            "Choose:",
            q["options"],
            index=None,
            key=f"radio_{unique_key}",
            disabled=st.session_state.answered
        )

    elif q["type"] == "text_input":
        user_answer = st.text_input(
            "Your answer:",
            key=f"text_{unique_key}",
            disabled=st.session_state.answered
        )

    elif q["type"] == "draw":
        canvas_result = st_canvas(
            height=300,
            width=300,
            drawing_mode="freedraw",
            key=f"canvas_{unique_key}"
        )
        user_answer = "DRAWN"

    elif q["type"] == "smiles_input":
        smiles = st_ketcher(key=f"ketcher_{unique_key}")
        user_answer = smiles

    # SUBMIT
    submit_disabled = (
        st.session_state.answered or
        ((q["type"] in ["multiple_choice", "image_label"]) and user_answer is None) or
        ((q["type"] == "smiles_input") and not user_answer)
    )

    if st.button("✅ Submit", disabled=submit_disabled, key=f"submit_{unique_key}"):

        st.session_state.answered = True
        st.session_state.show_next = True

        # Check answer
        if q["type"] == "draw":
            correct = True
        elif q["type"] == "smiles_input":
            correct = smiles_equal(user_answer, q["correct_answer"])
        else:
            correct = (
                str(user_answer).strip().lower()
                == str(q["correct_answer"]).strip().lower()
            )

        # ✅ FIX: properly store topics
        st.session_state.answered_questions.append(correct)

        if not correct and "topics" in q:
            if isinstance(q["topics"], list):
                st.session_state.wrong_topics.extend(q["topics"])  # ✅ FIXED
            else:
                st.session_state.wrong_topics.append(q["topics"])

        # Feedback
        if correct:
            st.success("✅ Correct!")
            st.session_state.xp += 10
            st.session_state.streak += 1
        else:
            st.error("❌ Incorrect")
            st.session_state.hearts -= 1
            st.session_state.streak = 0

        st.info(q["explanation"])

        if q.get("answer_image"):
            try:
                st.image(Image.open(q["answer_image"]), caption="Model Answer")
            except:
                st.warning("Answer image not found")

    # NEXT
    if st.session_state.show_next:
        if st.button("Next ➡️", key=f"next_{unique_key}"):

            if st.session_state.question_index < len(questions) - 1:
                st.session_state.question_index += 1
            else:
                st.session_state.lesson_mode = "summary"

            st.session_state.answered = False
            st.session_state.show_next = False

# =========================
# SUMMARY MODE
# =========================
elif st.session_state.lesson_mode == "summary":

    st.header("📊 Lesson Summary")

    if len(st.session_state.wrong_topics) == 0:
        st.success("🎉 Congratulations! You have mastered this lesson!")
    else:
        topics_to_review = sorted(set(st.session_state.wrong_topics))

        st.warning("📚 You have done well, padawan! To improve your understanding and performance, you may want to review these topics:")
        st.write(", ".join(topics_to_review))

    if st.button("🔁 Restart Lesson"):
        st.session_state.question_index = 0
        st.session_state.lesson_mode = "learn"
        st.session_state.wrong_topics = []
        st.session_state.answered_questions = []

# -------------------------
# GAME OVER
# -------------------------
if st.session_state.hearts <= 0:
    st.warning("Out of hearts! Restarting.")
    st.session_state.hearts = 5
    st.session_state.question_index = 0
    st.session_state.lesson_mode = "learn"
    st.session_state.answered = False
    st.session_state.wrong_topics = []
    st.stop()
