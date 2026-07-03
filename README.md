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

## Comparison with Existing Tools

### vs. LangChain (`PromptTemplate`)
LangChain constructs prompts using string interpolation (e.g., `ChatPromptTemplate.from_messages(...)`). 
While easy for simple tasks, as your agent grows complex, you end up with "Template Spaghetti."
- **LangChain**: Modifying a prompt means editing a giant f-string. If an agent's output breaks, you have no programmatic way to trace *which specific instruction* caused the regression.
- **Lambda-Prompting**: Prompts are ASTs built by pure functions. You can programmatically diff two prompts (like `git diff`) to see exactly which combinator (e.g., a specific few-shot example or guideline) was added or removed.

### vs. DSPy
DSPy is a fantastic framework that replaces manual prompt engineering with automated prompt optimization using signatures.
- **DSPy**: Treats the prompt as an internal black-box state optimized by a compiler. It's powerful, but developers lose direct control and traceability over the generated context.
- **Lambda-Prompting**: Gives control back to the software engineer. It provides a typesafe, traceable, and modular foundation to build prompts deterministically.

## Getting Started

Make sure you have `uv` installed, then run the demonstration script:

```bash
uv run main.py
```

### Example: Building a Multi-Agent Prompt Tree

To demonstrate how a prompt is built using functional composition, let's walk through the `main.py` example step-by-step.

#### 1. Defining Combinators and Schemas
First, we define our domain-specific models and reusable combinators. Notice how combinators like `with_guidelines` are just higher-order functions that take a context (a `PromptTerm`) and return a new one:

```python
from pydantic import BaseModel, Field
from lambda_prompting import PromptTerm, PromptCombinator, compose

class ReviewResult(BaseModel):
    thinking_process: str = Field(..., description="Step-by-step reasoning")
    bug_found: bool = Field(..., description="Whether a bug was found")
    suggestion: str = Field(..., description="Suggestion for fixing the bug")
    fixed_code: str = Field(..., description="The fixed code snippet")

def with_guidelines(guidelines: list[str]) -> PromptCombinator:
    def _apply(arg: PromptTerm) -> PromptTerm:
        guidelines_str = "\n".join(f"- {g}" for g in guidelines)
        new_text = f"【Review Guidelines】\n{guidelines_str}\n\n{arg.text}"
        # We record exactly which function modified the prompt, and from what parent
        return PromptTerm(text=new_text, origin=f"with_guidelines({len(guidelines)} items)", children=[arg])
    return _apply
```

#### 2. The Initial State and Base Pipeline
We start with the raw user input. Instead of immediately concatenating strings, we define a `base_pipeline`—a composed function containing instructions shared by all our agents.

```python
# A. Initial state
user_input = PromptTerm(
    text="Target code: `def apply_discount(price, pct): return price - (price * pct / 100)`", 
    origin="User Input"
)

# B. Common base prompt (Building blocks reused across agents)
base_pipeline = compose(
    with_guidelines(["Check: Missing type hints", "Check: Division by zero"]),
    with_few_shot(["Input: `def add(a, b): return a+b`\nReview: Missing type hints."])
)
base_term = base_pipeline(user_input)
```

#### 3. Branching into Specialized Agents
From this shared foundation (`base_term`), we can branch out into **three distinct agents** by composing different combinators on top of it. Because evaluation is purely functional, `base_term` remains untouched, and we safely spawn three parallel prompt trees.

```python
# Branch A: Traditional String-based Reviewer
term_a = compose(
    with_json_format('{"bug_found": bool, "suggestion": str}'),
    with_system_role("Standard Code Reviewer"),
)(base_term)

# Branch B: Modern Architect with Chain-of-Thought and Pydantic Schema
term_b = compose(
    with_chain_of_thought(),
    with_pydantic_schema(ReviewResult),
    with_system_role("Senior Python Architect"),
)(base_term)

# Branch C: Security Expert
term_c = compose(
    with_json_format('{"vulnerability_found": bool, "severity": "low|medium|high"}'),
    with_system_role("Cybersecurity Expert"),
)(base_term)
```

#### 4. Visualization and Traceability
Because the system inherently tracks the abstract syntax tree (AST) of how each prompt was generated, it can render a beautifully colored, Git-style `N-ary` tree of the prompt's lineage.

```python
from lambda_prompting import render_tree

branches = {
    "Branch A (Standard)": term_a,
    "Branch B (Advanced)": term_b,
    "Branch C (Security)": term_c
}
print(render_tree(branches))
```

This generates a deterministic trace of our prompt's history:

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
