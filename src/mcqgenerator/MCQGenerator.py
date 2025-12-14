# src/mcqgenerator/MCQGenerator.py

import os
import json
import re
from pathlib import Path
from dotenv import load_dotenv

from src.mcqgenerator.utils import read_file, get_table_data

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.callbacks import get_openai_callback


# ----------------------------
# Helpers
# ----------------------------
def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_json(text: str) -> dict:
    """
    Extract the first JSON object from a string and parse it.
    Useful if the model accidentally adds extra text.
    """
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in LLM output.")
    return json.loads(match.group(0))


# ----------------------------
# Main MCQ generator
# ----------------------------
def generate_mcqs(
    input_file_path: str,
    number: int = 5,
    subject: str = "Machine Learning",
    tone: str = "educational",
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.7,
):
    # Load env
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment. Put it in your .env file.")

    # Project root = folder containing 'src'
    # This file is: <root>/src/mcqgenerator/MCQGenerator.py
    project_root = Path(__file__).resolve().parents[2]

    # JSON schema/templates live next to src/
    response_json_path = project_root / "Response.json"
    evaluation_json_path = project_root / "Evaluation_response.json"

    if not response_json_path.exists():
        raise FileNotFoundError(f"Missing file: {response_json_path}")
    if not evaluation_json_path.exists():
        raise FileNotFoundError(f"Missing file: {evaluation_json_path}")

    response_json = load_json(response_json_path)
    evaluation_response_json = load_json(evaluation_json_path)

    # Read input text (via utils.py)
    text = read_file(input_file_path)

    # LLM
    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key,
    )

    # ----------------------------
    # Prompt 1: Quiz generation
    # ----------------------------
    TEMPLATE1 = """
You are an expert at creating multiple-choice questions (MCQs) for educational purposes.

Return ONLY valid JSON. No extra text, no markdown, no code fences.

Requirements:
- Generate exactly {number} MCQs for {subject} students in a {tone} tone.
- Use ONLY the provided text.
- Do not repeat questions.
- Use keys "1"..."{number}" exactly.
- Each question must include options a/b/c/d.
- "correct" must be one of: "a", "b", "c", "d".
- The correct option must NOT always be the same letter; distribute answers across a/b/c/d.

Text:
{text}

### RESPONSE_JSON (structure/template only; values are placeholders)
{response_json}
"""

    quiz_generation_prompt = PromptTemplate(
        input_variables=["text", "number", "subject", "tone", "response_json"],
        template=TEMPLATE1,
    )

    quiz_chain_text = quiz_generation_prompt | llm | StrOutputParser()

    # ----------------------------
    # Prompt 2: Quiz evaluation
    # ----------------------------
    TEMPLATE2 = """
You are an expert in creating and evaluating multiple-choice questions (MCQs) for {subject} students.

Return ONLY valid JSON. No extra text, no markdown, no code fences.

Rules:
- complexity_analysis must be <= 50 words.
- is_appropriate must be true or false (boolean).
- final_quiz must follow the exact quiz format shown in RESPONSE_JSON.
- If is_appropriate is true, final_quiz must be identical to the input quiz.
- If is_appropriate is false, revise ONLY the necessary questions (keep the same keys and structure).
- RESPONSE_JSON is a structure/template only; its values are placeholders.

Input Quiz (JSON):
{quiz}

### RESPONSE_JSON (structure/template only; values are placeholders)
{evaluation_response_json}
"""

    quiz_evaluation_prompt = PromptTemplate(
        input_variables=["subject", "quiz", "evaluation_response_json"],
        template=TEMPLATE2,
    )

    review_chain_text = quiz_evaluation_prompt | llm | StrOutputParser()

    # ----------------------------
    # Combine: generate -> evaluate
    # ----------------------------
    combined_chain_text = (
        RunnablePassthrough.assign(quiz=quiz_chain_text)
        | review_chain_text
    )

    inputs = {
        "text": text,
        "number": number,
        "subject": subject,
        "tone": tone,
        "response_json": json.dumps(response_json),
        "evaluation_response_json": json.dumps(evaluation_response_json),
    }

    with get_openai_callback() as cb:
        final_output_text = combined_chain_text.invoke(inputs)
        token_info = {
            "total_tokens": cb.total_tokens,
            "prompt_tokens": cb.prompt_tokens,
            "completion_tokens": cb.completion_tokens,
            "total_cost_usd": cb.total_cost,
        }

    # Parse final evaluation JSON
    final_output = extract_json(final_output_text)

    # Build table-friendly data using utils.get_table_data()
    # final_output["final_quiz"] is a dict => convert to JSON string for get_table_data()
    quiz_table_data = get_table_data(json.dumps(final_output.get("final_quiz", {})))

    return final_output, quiz_table_data, token_info


# ----------------------------
# CLI runner (optional)
# ----------------------------
if __name__ == "__main__":
    # Example usage (update path)
    result, table_data, tokens = generate_mcqs(
        input_file_path="data/input.pdf",
        number=5,
        subject="Machine Learning",
        tone="educational",
    )

    print("Token usage:", tokens)
    print("\nComplexity:", result.get("complexity_analysis"))
    print("Appropriate?:", result.get("is_appropriate"))
    print("Q1:", result.get("final_quiz", {}).get("1", {}).get("mcq"))

    # table_data is list[dict] (MCQ, Choices, Correct) if your utils.get_table_data returns that
    print("\nTable rows:", len(table_data) if table_data else 0)
