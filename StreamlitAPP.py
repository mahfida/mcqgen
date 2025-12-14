import json
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st
from langchain_community.callbacks import get_openai_callback

from src.mcqgenerator.MCQGenerator import generate_mcqs
from src.mcqgenerator.logger import logging  # preferred (if your logger.py exposes `logger`)

st.set_page_config(page_title="MCQ Generator", layout="wide")
st.title("MCQ Generator App")

with st.form("mcq_form"):
    uploaded_file = st.file_uploader("Upload a PDF or TXT file", type=["pdf", "txt"])
    number_of_mcqs = st.number_input("Number of MCQs to generate", min_value=1, max_value=50, value=5)
    subject = st.text_input("Subject", value="Machine Learning")
    tone = st.selectbox("Tone", options=["educational", "casual", "formal"], index=0)
    submit_button = st.form_submit_button("Generate MCQs")

if submit_button:
    if uploaded_file is None:
        st.error("Please upload a PDF or TXT file.")
        st.stop()

    suffix = Path(uploaded_file.name).suffix.lower()

    try:
        with st.spinner("Generating MCQs..."):
            # Save upload to a temp file path (so your path-based pipeline works)
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name

            with get_openai_callback() as cb:
                final_output, quiz_table_data, token_info = generate_mcqs(
                    input_file_path=tmp_path,
                    number=int(number_of_mcqs),
                    subject=subject,
                    tone=tone,
                )

            logger.info(f"Tokens: {token_info}")

        st.success("MCQs generated successfully!")

        # Show evaluation summary
        st.subheader("Evaluation")
        st.write({
            "complexity_analysis": final_output.get("complexity_analysis"),
            "is_appropriate": final_output.get("is_appropriate"),
        })

        # Show table of MCQs
        st.subheader("Generated MCQs")
        if quiz_table_data:
            df = pd.DataFrame(quiz_table_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No table data produced. Showing raw output:")
            st.json(final_output)

        # Token usage
        st.subheader("Token usage")
        st.json(token_info)

    except Exception as e:
        logger.exception("Streamlit app failed")
        st.error(f"Error: {e}")
