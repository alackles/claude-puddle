import os
from app.config import settings

LOAD_CHAPTER_TOOL = {
    "name": "load_chapter",
    "description": (
        "Load the content of a textbook chapter. Use this when you need to reference "
        "specific course material to answer a student's question. You may call this "
        "tool multiple times in one turn if the question spans multiple chapters."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "chapter_number": {
                "type": "integer",
                "description": "The chapter number to load (1–16).",
            }
        },
        "required": ["chapter_number"],
    },
}

TOOLS = [LOAD_CHAPTER_TOOL]

CHAPTER_FILENAMES = {
    1: "01_computerprogramming.pdf",
    2: "02_variablesandoperators.pdf",
    3: "03_inputandoutput.pdf",
    4: "04_methodsandtesting.pdf",
    5: "05_conditionalsandlogic.pdf",
    6: "06_loopsandstrings.pdf",
    7: "07_arraysandreferences.pdf",
    8: "08_recursivemethods.pdf",
    9: "09_immutableobjects.pdf",
    10: "10_mutableobjects.pdf",
    11: "11_designingclasses.pdf",
    12: "12_arraysofobjects.pdf",
    13: "13_objectsofarrays.pdf",
    14: "14_extendingclasses.pdf",
    15: "15_arraysofarrays.pdf",
    16: "16_reusingclasses.pdf",
}


def resolve_chapter(chapter_number: int) -> dict:
    """Return an Anthropic tool result content block for the requested chapter."""
    if chapter_number not in CHAPTER_FILENAMES:
        return {
            "type": "text",
            "text": f"Chapter {chapter_number} does not exist. Valid chapters are 1–16.",
        }

    filename = CHAPTER_FILENAMES[chapter_number]
    chapter_path = os.path.join(settings.context_dir, "chapters", filename)

    if not os.path.exists(chapter_path):
        return {
            "type": "text",
            "text": f"Chapter {chapter_number} file not found on disk.",
        }

    # Serve as PDF document block so the Anthropic API can parse it natively
    import base64
    with open(chapter_path, "rb") as f:
        pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")

    return {
        "type": "document",
        "source": {
            "type": "base64",
            "media_type": "application/pdf",
            "data": pdf_data,
        },
    }
