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
