import os
import csv
from datetime import datetime
import streamlit as st
import pandas as pd

# =========================
# CONFIG & SETTINGS
# =========================
EXCEL_PATH = "URDU DATASET.xlsx"
IMAGE_FOLDER = "VQA_RAD Image Folder"
CSV_PATH = "doctor_feedback.txt"

st.set_page_config(page_title="Medical VQA", layout="wide")

# =========================
# REFINED CSS (UNCHANGED)
# =========================
st.markdown("""
<style>
    section[data-testid="stSidebar"] {
        width: 240px !important;
        background-color: #f1f3f6;
    }
    .main .block-container {
        padding-top: 1.5rem;
    }
    .en-label {
        color: #777;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 2px;
    }
    .en-content {
        font-size: 1rem;
        font-weight: 500;
        color: #111;
        margin-bottom: 8px;
    }
    .stTextArea textarea {
        font-family: 'NafeesNastaleeq', 'Arial', serif !important;
        font-size: 22px !important; 
        line-height: 1.5 !important;
        direction: rtl;
        background-color: #ffffff !important;
        border: 1px solid #ccd0d5 !important;
        padding: 8px !important;
        resize: none;
    }
    div.stButton > button {
        height: 40px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    df = pd.read_excel(EXCEL_PATH)
    image_map = {
        f: os.path.join(IMAGE_FOLDER, f)
        for f in os.listdir(IMAGE_FOLDER)
        if f.lower().endswith((".jpg", ".png", ".jpeg"))
    }
    df["image_path"] = df["IMAGEID"].astype(str).apply(
        lambda x: image_map.get(os.path.basename(x))
    )
    return df.dropna(subset=["image_path"]).reset_index(drop=True)

df = load_data()

# =========================
# SESSION STATE
# =========================
if "idx" not in st.session_state:
    st.session_state.idx = 0
    st.session_state.df_view = df.sample(
        n=min(15, len(df)), random_state=42
    ).reset_index(drop=True)

if "edited_q" not in st.session_state:
    st.session_state.edited_q = {}
if "edited_a" not in st.session_state:
    st.session_state.edited_a = {}

df_view = st.session_state.df_view
row = df_view.iloc[st.session_state.idx]

# =========================
# CSV INIT 
# =========================
if not os.path.exists(CSV_PATH):
    with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "QID_linked",
            "IMAGEID",
            "IMAGEORGAN",
            "QUESTION_urdu",
            "ANSWER_urdu",
            "FINAL_QUESTION_urdu",
            "FINAL_ANSWER_urdu",
            "TIMESTAMP"
        ])

# =========================
# SAVE FUNCTION 
# =========================
def save_feedback(row, edited_question, edited_answer):
    with open(CSV_PATH, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            row["QID_linked"],
            row["IMAGEID"],
            row["IMAGEORGAN"],
            row["QUESTION_urdu"],
            row["ANSWER_urdu"],
            edited_question,
            edited_answer,
            datetime.now().strftime("%d-%m-%Y %H:%M")
        ])

# =========================
# SIDEBAR (UNCHANGED)
# =========================
with st.sidebar:
    st.markdown("### 📋 Progress")
    st.progress((st.session_state.idx + 1) / len(df_view))
    st.write(f"Sample {st.session_state.idx + 1} of {len(df_view)}")
    st.divider()
    st.caption("Organ Focus")
    st.markdown(f"**{row['IMAGEORGAN']}**")
    st.markdown(f"<div style='font-size:20px;'>{row['IMAGEORGAN_urdu']}</div>", unsafe_allow_html=True)

# =========================
# MAIN LAYOUT
# =========================
col1, col2 = st.columns([0.8, 1.2], gap="large")

with col1:
    st.image(row["image_path"], width=150)
    st.caption(f"Ref: {row['IMAGEID']}")

with col2:
    st.markdown('<p class="en-label">English Question</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="en-content">{row["QUESTION"]}</p>', unsafe_allow_html=True)

    edited_question = st.text_area(
        label="Urdu Q",
        value=st.session_state.edited_q.get(row["QID_linked"], row["QUESTION_urdu"]),
        height=100,
        key=f"q_{st.session_state.idx}",
        label_visibility="collapsed"
    )

    st.markdown('<p class="en-label">English Answer</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="en-content">{row["ANSWER"]}</p>', unsafe_allow_html=True)

    edited_answer = st.text_area(
        label="Urdu A",
        value=st.session_state.edited_a.get(row["QID_linked"], row["ANSWER_urdu"]),
        height=70,
        key=f"a_{st.session_state.idx}",
        label_visibility="collapsed"
    )

    nav1, nav2 = st.columns(2)

    with nav1:
        if st.button("⬅ Back", disabled=st.session_state.idx == 0):
            st.session_state.edited_q[row["QID_linked"]] = edited_question
            st.session_state.edited_a[row["QID_linked"]] = edited_answer
            save_feedback(row, edited_question, edited_answer)
            st.session_state.idx -= 1
            st.rerun()

    with nav2:
        is_last = st.session_state.idx == len(df_view) - 1
        if st.button("Next ➡" if not is_last else "Finish", type="primary"):
            st.session_state.edited_q[row["QID_linked"]] = edited_question
            st.session_state.edited_a[row["QID_linked"]] = edited_answer
            save_feedback(row, edited_question, edited_answer)
            if not is_last:
                st.session_state.idx += 1
                st.rerun()
            else:
                st.success("Submission Complete!")


