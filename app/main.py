import html
import os
import logging
from dotenv import load_dotenv

load_dotenv()

import streamlit as st
import requests


LOG_DIR = os.getenv("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

log_path = os.path.join(LOG_DIR, "ui.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[logging.FileHandler(log_path), logging.StreamHandler()],
)
logger = logging.getLogger("knowledge-mate.ui")

API_URL = os.getenv("API_URL", "http://localhost:8000/chat")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "180"))

st.set_page_config(
    page_title="NovaCare HR Knowledgebase",
    page_icon="N",
    layout="centered",
)

st.markdown(
    """
    <style>
    :root {
        --navy: #173f5f;
        --teal: #187c7a;
        --mint: #e5f4ef;
        --blue-wash: #eaf2ff;
        --ink: #243746;
        --muted: #5f7180;
    }
    .stApp {
        background: linear-gradient(135deg, #f8fbfc 0%, #eef7f5 52%, #fff8ee 100%);
    }
    .block-container {
        max-width: 780px;
        padding-top: 3.5rem;
        padding-bottom: 4rem;
    }
    .brand-mark {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 2.8rem;
        height: 2.8rem;
        border-radius: 14px;
        background: #f2b134;
        color: #173f5f;
        font-size: 1.35rem;
        font-weight: 800;
        box-shadow: 0 8px 18px rgba(23, 63, 95, 0.14);
        margin-top: 0.8rem;
        margin-bottom: 0.7rem;
        margin-left: auto;
        margin-right: auto;
    }
    .main-title {
        color: var(--navy);
        font-size: 2.7rem;
        font-weight: 700;
        letter-spacing: 0;
        margin-bottom: 0.15rem;
        text-align: center;
    }
    .sub-title {
        color: var(--teal);
        font-size: 1.35rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
        text-align: center;
    }
    .description {
        color: var(--muted);
        font-size: 1rem;
        line-height: 1.6;
        max-width: 680px;
        margin-bottom: 2rem;
        margin-left: auto;
        margin-right: auto;
        text-align: center;
    }
    .header-rule {
        width: 100%;
        height: 5px;
        border-radius: 5px;
        background: linear-gradient(90deg, #187c7a 0 58%, #f2b134 58% 78%, #ef8354 78%);
        margin: 1.25rem 0 2rem;
    }
    .conversation-card {
        border: 1px solid #d9e6e5;
        border-left: 5px solid #187c7a;
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.88);
        padding: 1rem 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 7px 18px rgba(23, 63, 95, 0.07);
    }
    .question-text {
        color: #1d4ed8;
        line-height: 1.5;
    }
    .answer-text {
        color: #18794e;
        line-height: 1.6;
        margin-top: 0.75rem;
    }
    .question-label {
        color: #123b9b;
        font-weight: 700;
    }
    .answer-label {
        color: #0f5c3a;
        font-weight: 700;
    }
    div[data-testid="stForm"] {
        margin-top: 2rem;
        padding: 1.25rem 1.3rem 1rem;
        border: 1px solid #cfe2df;
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.9);
        box-shadow: 0 9px 22px rgba(23, 63, 95, 0.08);
    }
    div[data-testid="stTextInput"] label {
        color: #9a6700;
        font-weight: 700;
    }
    div[data-testid="stTextInput"] input {
        border: 2px solid #b9d8d4;
        border-radius: 10px;
        background: #ffffff;
        color: #172b3a;
        caret-color: #172b3a;
    }
    div[data-testid="stTextInput"] input::placeholder {
        color: #5f7180;
        opacity: 1;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #187c7a;
        box-shadow: 0 0 0 2px rgba(24, 124, 122, 0.15);
    }
    div[data-testid="stFormSubmitButton"] button {
        width: 100%;
        border: 0;
        border-radius: 9px;
        background: #187c7a;
        color: #ffffff;
        font-weight: 700;
    }
    div[data-testid="stFormSubmitButton"] button:hover {
        background: #12605f;
    }
    </style>
    <div class="brand-mark">N</div>
    <div class="main-title">NovaCare (Pvt) Ltd.</div>
    <div class="sub-title">HR Knowledgebase</div>
    <div class="description">
        Find clear answers from NovaCare's HR policies and workplace documents
        in one place.
    </div>
    <div class="header-rule"></div>
    """,
    unsafe_allow_html=True,
)

if "conversations" not in st.session_state:
    st.session_state.conversations = []
if st.session_state.pop("clear_question", False):
    st.session_state.question_input = ""

for conversation in st.session_state.conversations:
    question_text = html.escape(conversation["question"])
    answer_text = html.escape(conversation["answer"]).replace("\n", "<br>")
    st.markdown(
        f'''<div class="conversation-card">
        <div class="question-text"><span class="question-label">Question:</span> {question_text}</div>
        <div class="answer-text"><span class="answer-label">Answer:</span> {answer_text}</div>
        </div>''',
        unsafe_allow_html=True,
    )

with st.form("question_form"):
    question = st.text_input(
        "Ask a question",
        placeholder="For example: What is the leave policy?",
        key="question_input",
    )
    submitted = st.form_submit_button("Ask")


if submitted:
    if not question:
        st.warning("Please enter a question.")
    else:
        with st.spinner("Asking backend..."):
            try:
                logger.info("Sending question to backend")
                logger.debug("Question: %s", question)
                resp = requests.post(
                    API_URL,
                    json={"question": question},
                    timeout=REQUEST_TIMEOUT,
                )
                resp.raise_for_status()
                data = resp.json()
                answer = data.get("answer") if isinstance(data, dict) else None
                if answer:
                    logger.info("Received answer from backend")
                    st.session_state.conversations.append(
                        {"question": question, "answer": answer}
                    )
                    st.session_state.clear_question = True
                    st.rerun()
                else:
                    logger.warning("Backend returned no answer")
                    st.error("No answer returned from backend.")
            except requests.exceptions.RequestException as e:
                logger.exception("Request to backend failed")
                st.error(f"Request failed: {e}")
            except Exception as e:
                logger.exception("Unexpected error in UI")
                st.error(f"Unexpected error: {e}")