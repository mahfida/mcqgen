import os
import json
import traceback
from pypdf import PdfReader


def read_file(file_path: str) -> str:
    """
    Reads text from a PDF or TXT file given its path.
    """
    if file_path.lower().endswith(".pdf"):
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted
            return text
        except Exception as e:
            raise Exception(f"Error reading PDF file: {e}")

    elif file_path.lower().endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    else:
        raise ValueError("Unsupported file format. Please upload a PDF or TXT file.")


def get_table_data(quiz_str: str):
    """
    Converts quiz JSON string into table-friendly data.
    """
    try:
        quiz_data = json.loads(quiz_str)
        quiz_table_data = []

        # iterate through the quiz_data to create table data
        for key, value in quiz_data.items():
            mcq = value.get("mcq", "")
            options = ".||.".join(
                [f"{opt}) {opt_val}" for opt, opt_val in value.get("options", {}).items()]
            )
            correct = value.get("correct", "")

            quiz_table_data.append({
                "MCQ": mcq,
                "Choices": options,
                "Correct": correct
            })

        return quiz_table_data

    except Exception as e:
        traceback.print_exception(type(e), e, e.__traceback__)
        return False

def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
