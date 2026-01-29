import os
import csv
from datetime import datetime
import streamlit as st
import pandas as pd

# =========================
# CONFIGURATION
# =========================
EXCEL_PATH = "URDU DATASET.xlsx"
IMAGE_FOLDER = "VQA_RAD Image Folder"
CSV_PATH = "doctor_feedback.csv"

st.set_page_config(layout="wide")
st.title("Doctor-in-the-Loop Urdu Medical VQA Validation")

# =========================
# LOAD EXCEL
# =========================
df = pd.read_excel(EXCEL_PATH)

required_cols = ["QID_unique", "IMAGEID", "IMAGEORGAN", "QUESTION", "ANSWER"]
missing_cols = [c for c in required_cols if c not in df.columns]

if missing_cols:
    st.error(f"Missing required columns in Excel: {missing_cols}")
    st.stop()

df = df.dropna(subset=required_cols).copy()

# =========================
# BUILD IMAGE LOOKUP (LOCAL)
# =========================
image_map = {}
for file in os.listdir(IMAGE_FOLDER):
    if file.lower().endswith((".jpg", ".jpeg", ".png")):
        image_map[file] = os.path.join(IMAGE_FOLDER, file)

# =========================
# EXTRACT IMAGE FILE FROM URL
# =========================
df["image_file"] = df["IMAGEID"].astype(str).apply(
    lambda x: os.path.basename(x)
)

df["image_path"] = df["image_file"].map(image_map)

# Drop rows where image not found locally
df = df.dropna(subset=["image_path"]).reset_index(drop=True)

# =========================
# SELECT 15 QUESTIONS ONLY
# =========================
df_view = df.sample(n=min(15, len(df)), random_state=42).reset_index(drop=True)

# =========================
# INITIALIZE CSV (IF NEEDED)
# =========================
if not os.path.exists(CSV_PATH):
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "QID_unique",
            "image_file",
            "IMAGEORGAN",
            "ORIGINAL_QUESTION",
            "ORIGINAL_ANSWER",
            "VERDICT",
            "CORRECTED_QUESTION",
            "CORRECTED_ANSWER",
            "TIMESTAMP"
        ])

# =========================
# UI — SELECT QUESTION
# =========================
st.write(f"Total questions for review: {len(df_view)}")

idx = st.number_input(
    "Select question number",
    min_value=1,
    max_value=len(df_view),
    step=1
) - 1

row = df_view.iloc[idx]

# =========================
# DISPLAY IMAGE + DATA
# =========================
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Medical Image")
    st.image(row["image_path"], use_container_width=True)
    st.caption(row["image_file"])

with col2:
    st.subheader("Organ")
    st.write(row["IMAGEORGAN"])

    st.subheader("Urdu Question")
    st.write(row["QUESTION"])

    st.subheader("Urdu Answer (Model Output)")
    st.write(row["ANSWER"])

# =========================
# VALIDATION SECTION
# =========================
st.markdown("---")
st.subheader("Doctor Validation")

verdict = st.radio(
    "Is the Question & Answer correct?",
    ["Correct", "Incorrect"]
)

# Defaults (used if Correct)
corrected_question = row["QUESTION"]
corrected_answer = row["ANSWER"]

if verdict == "Incorrect":
    st.markdown("### ✍️ Correct the Urdu Question")
    corrected_question = st.text_area(
        "Edited Question:",
        value=row["QUESTION"],
        height=100
    )

    st.markdown("### ✍️ Correct the Urdu Answer")
    corrected_answer = st.text_area(
        "Edited Answer:",
        value=row["ANSWER"],
        height=100
    )

# =========================
# SAVE FEEDBACK
# =========================
if st.button("Submit Feedback"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            row["QID_unique"],
            row["image_file"],
            row["IMAGEORGAN"],
            row["QUESTION"],
            row["ANSWER"],
            verdict,
            corrected_question if verdict == "Incorrect" else "",
            corrected_answer if verdict == "Incorrect" else "",
            timestamp
        ])

    st.success("Doctor feedback saved successfully!")
