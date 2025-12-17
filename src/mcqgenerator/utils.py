import json
import traceback
from typing import Dict, Any, List
from pypdf import PdfReader


def read_file(file_path: str) -> str:
    """Read text from a local PDF/TXT file path."""
    if file_path.lower().endswith(".pdf"):
        try:
            reader = PdfReader(file_path)
            parts = []
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    parts.append(extracted)
            return "\n".join(parts)
        except Exception as e:
            raise Exception(f"Error reading PDF file: {e}")

    if file_path.lower().endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    raise ValueError("Unsupported file format. Please upload a PDF or TXT file.")


def load_json(path: str) -> Dict[str, Any]:
    """Load a JSON file from disk."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def quiz_dict_to_table(quiz_dict: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Convert quiz dict (keys '1'..'N') to table rows for Streamlit/DataFrame.
    """
    try:
        rows = []
        for _, value in quiz_dict.items():
            mcq = value.get("mcq", "")
            options_dict = value.get("options", {}) or {}
            choices = ".||.".join([f"{k}) {v}" for k, v in options_dict.items()])
            correct = value.get("correct", "")
            rows.append({"MCQ": mcq, "Choices": choices, "Correct": correct})
        return rows
    except Exception as e:
        traceback.print_exception(type(e), e, e.__traceback__)
        return []
