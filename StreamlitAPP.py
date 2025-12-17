import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from src.mcqgenerator.MCQGenerator import generate_mcqs
from src.mcqgenerator.utils import quiz_dict_to_table
from src.mcqgenerator.logger import logger


st.set_page_config(page_title="MCQ Generator", layout="wide")
st.title("MCQ Generator App")

with st.form("mcq_form"):
    uploaded_file = st.file_uploader("Upload a PDF or TXT file", type=["pdf", "txt"])
    number_of_mcqs = st.number_input("Number of MCQs", min_value=1, max_value=50, value=5)
    subject = st.text_input("Subject (any topic)", value="Machine Learning")
    tone = st.selectbox("Tone", options=["educational", "casual", "formal"], index=0)
    submit_button = st.form_submit_button("Generate MCQs")

if submit_button:
    if uploaded_file is None:
        st.error("Please upload a PDF or TXT file.")
        st.stop()

    suffix = Path(uploaded_file.name).suffix.lower()

    try:
        with st.spinner("Generating MCQs..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name

            quiz_dict, info = generate_mcqs(
                input_file_path=tmp_path,
                number=int(number_of_mcqs),
                subject=subject,
                tone=tone,
            )

        logger.info(f"MCQs generated. Info: {info}")

        st.success("MCQs generated successfully!")
        st.caption(f"Questions returned: {len(quiz_dict)}")

        rows = quiz_dict_to_table(quiz_dict)
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)

        with st.expander("Raw JSON"):
            st.json(quiz_dict)

    except Exception as e:
        logger.exception("Streamlit app failed")
        st.error(f"Error: {e}")
