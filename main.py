import sys
from pathlib import Path
from pydantic import BaseModel, Field

# Add the src directory to the path so it can be imported
sys.path.insert(0, str(Path(__file__).parent / "src"))

from lambda_prompting import (
    PromptTerm,
    compose,
    print_trace,
    with_few_shot,
    with_json_format,
    with_system_role,
    with_pydantic_schema,
    diff_terms,
)

# Define a Pydantic model
class ReviewResult(BaseModel):
    bug_found: bool = Field(..., description="Whether a bug was found in the code")
    suggestion: str = Field(..., description="Suggestion for fixing the bug or improving the code")


def main():
    # 1. Initial state (e.g., user input)
    user_input = PromptTerm(
        text="Target code: `def add(a, b): return a - b`", 
        origin="User Input"
    )

    # 2. Common base prompt (partial application / reuse)
    base_prompt_builder = compose(
        with_few_shot(["Review check: variable naming", "Review check: return type"])
    )
    base_term = base_prompt_builder(user_input)

    # 3. Branch A: Traditional string-based JSON format specification
    builder_a = compose(
        with_json_format('{"bug_found": bool, "suggestion": str}'),
        with_system_role("Expert Python Reviewer"),
    )
    term_a = builder_a(base_term)

    # 4. Branch B: New Pydantic integration for schema insertion
    builder_b = compose(
        with_pydantic_schema(ReviewResult),
        with_system_role("Friendly Python Assistant"), # Alter the role slightly to clarify the diff
    )
    term_b = builder_b(base_term)

    # 5. Verification (Tree Diff)
    print("▼ Prompt Generation History Diff (Tree Diff)")
    print(diff_terms(term_a, term_b, name_a="Branch A (Manual)", name_b="Branch B (Pydantic)"))
    
    print("\n▼ Final Text Sent to LLM (Branch B)")
    print("-" * 40)
    print(term_b.text)
    print("-" * 40)

if __name__ == "__main__":
    main()
