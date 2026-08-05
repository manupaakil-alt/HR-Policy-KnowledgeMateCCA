import streamlit as st


st.title("HR Policy KnowledgeMate")

st.write(
    "AI assistant for answering HR policy questions"
)


question = st.text_input(
    "Ask your HR question"
)


if st.button("Ask"):
    st.write(
        "AI answer will appear here"
    )