# lambda-prompting

*Ah, greetings, fellow traveler of the computational cosmos!*

Have you ever looked at the state of modern "prompt engineering" and felt a profound sense of despair? We spend our days concatenating massive, fragile strings in natural language, hoping the LLM will parse our intent correctly. It is an approach completely divorced from the elegant paradigms of modern software engineering. We lack type safety, we lack modularity, and perhaps worst of all—we lack *traceability*. When you tweak a prompt, can you really tell exactly how the causal chain of instructions changed?

If you share this frustration, you are not alone. 

Truth be told, in this day and age, it is often faster to simply breathe life into an idea with the help of an AI than to turn the library upside down searching for prior art. So, trusting the vibes and the power of modern tooling, I simply went ahead and built it. 

Let us step back and look at a simple truth: the autoregressive generation of an LLM can be elegantly formalized as **Lambda Calculus**.

$$
M = \lambda c. \text{next-token}(c)
$$

When we append a system role or provide a few-shot example, what we are really doing is *currying* and *partial application*, ultimately culminating in a glorious $\beta$-reduction. 

**Lambda-Prompting** is an architecture born from this realization. Instead of passing around static strings, we construct prompts as higher-order functions (combinators) that take a context and return a new context. This preserves the abstract syntax tree (AST) of the prompt, allowing us to track exactly how it was built, visualize differences in an A/B test with Git-like tree diffs, and ensure our prompts are robust, composable components rather than a chaotic soup of text.

For the rigorous theoretical underpinnings and detailed architectural decisions, I invite you to peruse the [Project Manifest](PROJECT_MANIFEST.md).

## Features

- **Prompt as AST**: Track the entire genealogy of your prompts. No more mysterious string mutations.
- **Combinators**: Use and compose reusable functions (like `with_system_role`, `with_few_shot`).
- **Pydantic Integration**: Effortlessly inject robust JSON schemas directly into your prompt constraints via `with_pydantic_schema`.
- **Tree Diffing**: Compare two prompt branches and visualize their divergence with a Git-like tree diff.

## Getting Started

Make sure you have `uv` installed, then run the demonstration script:

```bash
uv run main.py
```

### Example: Building a Multi-Agent Prompt Tree

If you run the script, you will see a demonstration of how a prompt is built using functional composition. In `main.py`, we define a starting context (`User Input`) and a common foundation (`base_pipeline`) consisting of guidelines and a few-shot example.

From this shared foundation, we branch out into **three distinct agents**:
1. **Branch A (Standard Reviewer)**: A basic reviewer outputting a simple JSON format.
2. **Branch B (Advanced Architect)**: Adds Step-by-Step reasoning (Chain of Thought) and a robust Pydantic Schema constraint.
3. **Branch C (Security Expert)**: Specifically tuned for finding vulnerabilities with a customized JSON output.

Here is the actual implementation of this multi-agent prompt construction in `main.py`:

```python
import sys
from pathlib import Path
from pydantic import BaseModel, Field

# Add the src directory to the path so it can be imported
sys.path.insert(0, str(Path(__file__).parent / "src"))

from lambda_prompting import (
    PromptTerm,
    PromptCombinator,
    compose,
    with_few_shot,
    with_json_format,
    with_system_role,
    with_pydantic_schema,
    render_tree,
)

# 1. Define Domain Specific Models and Combinators
class ReviewResult(BaseModel):
    thinking_process: str = Field(..., description="Step-by-step reasoning before making a conclusion")
    bug_found: bool = Field(..., description="Whether a bug or issue was found in the code")
    suggestion: str = Field(..., description="Suggestion for fixing the bug or improving the code")
    fixed_code: str = Field(..., description="The completely fixed code snippet")

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

def main():
    # A. Initial state
    user_input = PromptTerm(
        text="Target code: `def apply_discount(price, pct): return price - (price * pct / 100)`", 
        origin="User Input"
    )

    # B. Common base prompt
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

    # 3. Visualization
    branches = {
        "Branch A (Standard)": term_a,
        "Branch B (Advanced)": term_b,
        "Branch C (Security)": term_c
    }
    print(render_tree(branches))

if __name__ == "__main__":
    main()
```

Because the system tracks the abstract syntax tree of how each prompt was generated, it can render a beautifully colored, Git-style `N-ary` tree of the prompt's lineage:

```text
▼ Prompt Generation History (N-ary Tree)
[User Input]
└── [with_guidelines(3 items)]
    └── [with_few_shot(1 items)]
        ├── [with_json_format]
        │   └── [with_system_role('Standard Code Reviewer')] (Branch A (Standard))
        ├── [with_chain_of_thought]
        │   └── [with_pydantic_schema('ReviewResult')]
        │       └── [with_system_role('Senior Python Architect')] (Branch B (Advanced))
        └── [with_json_format]
            └── [with_system_role('Cybersecurity Expert')] (Branch C (Security))
```

And for Branch B, the final text sent to the LLM neatly organizes the system role, examples, target code, and JSON schema constraints into an optimal prompt structure:

```text
▼ Final Text Sent to LLM (Branch B - Advanced)
============================================================
【System Role: Senior Python Architect】
【Examples】
- Input: `def add(a, b): return a+b`
Review: Missing type hints for `a` and `b`.

【Review Guidelines】
- Check: Missing type hints
- Check: Division by zero
- Check: Negative percentages

Target code: `def apply_discount(price, pct): return price - (price * pct / 100)`

【Instructions】
Please think step-by-step before providing the final answer.

【Output Rules】
Return valid JSON matching the following schema:
{
  "properties": {
    "thinking_process": {
      "description": "Step-by-step reasoning before making a conclusion",
      "title": "Thinking Process",
      "type": "string"
    },
    ...
  },
  "required": [
    "thinking_process",
    "bug_found",
    "suggestion",
    "fixed_code"
  ],
  "title": "ReviewResult",
  "type": "object"
}
============================================================
```

## Core Concepts

- `PromptTerm`: A node containing the generated text, its origin, and pointers to its history.
- `PromptCombinator`: A function taking a `PromptTerm` and returning a new `PromptTerm`.
- `compose`: The engine of our $\beta$-reduction, linking combinators sequentially.
