import os
import json
import re
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.mcqgenerator.utils import read_file, load_json


def _extract_json(text: str) -> Dict[str, Any]:
    """
    Extract and parse the first JSON object found in model output.
    """
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in LLM output.")
    return json.loads(match.group(0))


def _validate_quiz(quiz: Dict[str, Any], number: int) -> None:
    """
    Validate structure:
    - keys "1"..."{number}"
    - each has mcq, options a/b/c/d, correct in a/b/c/d
    """
    expected_keys = [str(i) for i in range(1, number + 1)]
    actual_keys = list(quiz.keys())

    if actual_keys != expected_keys:
        # allow if keys exist but are unordered; normalize check
        if sorted(actual_keys, key=lambda x: int(x)) != expected_keys:
            raise ValueError(f"Expected keys {expected_keys}, got {actual_keys}")

    for k in expected_keys:
        item = quiz.get(k, {})
        if "mcq" not in item or "options" not in item or "correct" not in item:
            raise ValueError(f"Question {k} missing required fields.")

        options = item.get("options") or {}
        for opt in ["a", "b", "c", "d"]:
            if opt not in options:
                raise ValueError(f"Question {k} missing option '{opt}'.")

        correct = item.get("correct")
        if correct not in ["a", "b", "c", "d"]:
            raise ValueError(f"Question {k} has invalid correct answer: {correct}")


def _maybe_summarize(llm: ChatOpenAI, text: str, max_chars: int = 18000) -> str:
    """
    Keep prompts under control. If text is too long, summarize to study notes.
    (Char-based control; simple and effective for avoiding token overflow.)
    """
    if len(text) <= max_chars:
        return text

    summary_prompt = PromptTemplate(
        input_variables=["text"],
        template="""
Summarize the following content into concise study notes for exam prep.
Keep the summary under ~1200 words. Preserve key definitions, steps, distinctions, and important facts.
Return plain text only.

CONTENT:
{text}
""".strip(),
    )
    chain = summary_prompt | llm | StrOutputParser()
    return chain.invoke({"text": text})


def generate_mcqs(
    input_file_path: str,
    number: int = 5,
    subject: str = "General",
    tone: str = "educational",
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.3,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Generate MCQs from a PDF/TXT file path.

    Returns:
        quiz_dict: {"1": {...}, "2": {...}, ...}
        token_info: dict (if you track tokens outside, you can ignore this)
    """
    load_dotenv(override=True)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found. Put it in .env or environment variables.")

    project_root = Path(__file__).resolve().parents[2]
    response_json_path = project_root / "Response.json"
    if not response_json_path.exists():
        raise FileNotFoundError(f"Missing Response.json at: {response_json_path}")

    response_json = load_json(str(response_json_path))

    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key,
    )

    raw_text = read_file(input_file_path)
    text = _maybe_summarize(llm, raw_text)

    TEMPLATE = """
You are an expert at creating multiple-choice questions (MCQs) for educational purposes.

Return ONLY valid JSON. No extra text, no markdown, no code fences.

Rules:
- Generate exactly {number} MCQs for {subject} students in a {tone} tone.
- Use ONLY the provided text.
- Do not repeat questions.
- Use keys "1"..."{number}" exactly (all keys must be present).
- Each question must include options a/b/c/d.
- "correct" must be one of: "a", "b", "c", "d".
- RESPONSE_JSON shows the structure for ONE question only. Replicate it to produce keys "1"..."{number}".
- Avoid always choosing the same correct letter; spread answers across a/b/c/d.

TEXT:
{text}

### RESPONSE_JSON (structure/template only; values are placeholders)
{response_json}
""".strip()

    prompt = PromptTemplate(
        input_variables=["text", "number", "subject", "tone", "response_json"],
        template=TEMPLATE,
    )

    chain = prompt | llm | StrOutputParser()

    inputs = {
        "text": text,
        "number": number,
        "subject": subject,
        "tone": tone,
        "response_json": json.dumps(response_json),
    }

    # Try once, then retry once if parsing/validation fails
    last_error: Optional[Exception] = None
    for attempt in range(2):
        try:
            output_text = chain.invoke(inputs)
            quiz = _extract_json(output_text)
            _validate_quiz(quiz, number)
            return quiz, {"attempts": attempt + 1}
        except Exception as e:
            last_error = e
            # strengthen the instruction a bit on retry
            inputs["tone"] = tone
            inputs["subject"] = subject
            inputs["text"] = text
            # Add a nudge without changing the schema
            inputs["response_json"] = json.dumps(response_json)

    raise RuntimeError(f"Failed to generate a valid quiz after retries. Last error: {last_error}")
