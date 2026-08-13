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

st.title("HR Policy KnowledgeMate")

st.write(
    "AI assistant for answering HR policy questions"
)


question = st.text_input(
    "Ask your HR question"
)


if st.button("Ask"):
    if not question:
        st.warning("Please enter a question.")
    else:
        with st.spinner("Asking backend..."):
            try:
                logger.info("Sending question to backend")
                logger.debug("Question: %s", question)
                resp = requests.post(API_URL, json={"question": question}, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                answer = data.get("answer") if isinstance(data, dict) else None
                if answer:
                    logger.info("Received answer from backend")
                    st.write(answer)
                else:
                    logger.warning("Backend returned no answer")
                    st.error("No answer returned from backend.")
            except requests.exceptions.RequestException as e:
                logger.exception("Request to backend failed")
                st.error(f"Request failed: {e}")
            except Exception as e:
                logger.exception("Unexpected error in UI")
                st.error(f"Unexpected error: {e}")