import sys
from pathlib import Path
from pydantic import BaseModel, Field

# Add the src directory to the path so it can be imported
sys.path.insert(0, str(Path(__file__).parent / "src"))

from lambda_prompting import (
    PromptTerm,
    PromptCombinator,
    compose,
    print_trace,
    with_few_shot,
    with_json_format,
    with_system_role,
    with_pydantic_schema,
    diff_terms,
    render_tree,
)

# ---------------------------------------------------------
# 1. Define Domain Specific Models and Combinators
# ---------------------------------------------------------
class ReviewResult(BaseModel):
    thinking_process: str = Field(..., description="Step-by-step reasoning before making a conclusion")
    bug_found: bool = Field(..., description="Whether a bug or issue was found in the code")
    suggestion: str = Field(..., description="Suggestion for fixing the bug or improving the code")
    fixed_code: str = Field(..., description="The completely fixed code snippet")

# You can easily define custom combinators for your project
def with_guidelines(guidelines: list[str]) -> PromptCombinator:
    def _apply(arg: PromptTerm) -> PromptTerm:
        guidelines_str = "\n".join(f"- {g}" for g in guidelines)
        new_text = f"【Review Guidelines】\n{guidelines_str}\n\n{arg.text}"
        return PromptTerm(text=new_text, origin=f"with_guidelines({len(guidelines)} items)", children=[arg])
    return _apply

def with_chain_of_thought() -> PromptCombinator:
    def _apply(arg: PromptTerm) -> PromptTerm:
        new_text = f"{arg.text}\n\n【Instructions】\nPlease think step-by-step before providing the final answer."
        return PromptTerm(text=new_text, origin="with_chain_of_thought", children=[arg])
    return _apply

# ---------------------------------------------------------
# 2. Execution Pipeline
# ---------------------------------------------------------
def main():
    # A. Initial state (e.g., user input or retrieved code)
    user_input = PromptTerm(
        text="Target code: `def apply_discount(price, pct): return price - (price * pct / 100)`", 
        origin="User Input"
    )

    # B. Common base prompt (Building blocks reused across agents)
    base_pipeline = compose(
        with_guidelines(["Check: Missing type hints", "Check: Division by zero", "Check: Negative percentages"]),
        with_few_shot(["Input: `def add(a, b): return a+b`\nReview: Missing type hints for `a` and `b`."])
    )
    base_term = base_pipeline(user_input)

    # C. Branch A: Traditional String-based Reviewer
    term_a = compose(
        with_json_format('{"bug_found": bool, "suggestion": str}'),
        with_system_role("Standard Code Reviewer"),
    )(base_term)

    # D. Branch B: Modern Architect with CoT and Pydantic Schema
    term_b = compose(
        with_chain_of_thought(),
        with_pydantic_schema(ReviewResult),
        with_system_role("Senior Python Architect"),
    )(base_term)

    # E. Branch C: Security Expert
    term_c = compose(
        with_json_format('{"vulnerability_found": bool, "severity": "low|medium|high"}'),
        with_system_role("Cybersecurity Expert"),
    )(base_term)

    # ---------------------------------------------------------
    # 3. Visualization and Results
    # ---------------------------------------------------------
    print("▼ Prompt Generation History (N-ary Tree)")
    branches = {
        "Branch A (Standard)": term_a,
        "Branch B (Advanced)": term_b,
        "Branch C (Security)": term_c
    }
    print(render_tree(branches))
    
    print("\n▼ Final Text Sent to LLM (Branch B - Advanced)")
    print("=" * 60)
    print(term_b.text)
    print("=" * 60)

if __name__ == "__main__":
    main()

