# lambda-prompting

*Ah, greetings, fellow traveler of the computational cosmos!*

Have you ever looked at the state of modern "prompt engineering" and felt a profound sense of despair? We spend our days concatenating massive, fragile strings in natural language, hoping the LLM will parse our intent correctly. It is an approach completely divorced from the elegant paradigms of modern software engineering. We lack type safety, we lack modularity, and perhaps worst of all—we lack *traceability*. When you tweak a prompt, can you really tell exactly how the causal chain of instructions changed?

If you share this frustration, you are not alone. 

Let us step back and look at a simple truth: the autoregressive generation of an LLM can be elegantly formalized as **Lambda Calculus**.

$$M = \lambda c. \text{next\_token}(c)$$

When we append a system role or provide a few-shot example, what we are really doing is *currying* and *partial application*, ultimately culminating in a glorious $\beta$-reduction. 

**Lambda-Prompting** is an architecture born from this realization. Instead of passing around static strings, we construct prompts as higher-order functions (combinators) that take a context and return a new context. This preserves the abstract syntax tree (AST) of the prompt, allowing us to track exactly how it was built, visualize differences in an A/B test with Git-like tree diffs, and ensure our prompts are robust, composable components rather than a chaotic soup of text.

For the rigorous theoretical underpinnings and detailed architectural decisions, I invite you to peruse the [Project Manifest](PROJECT_MANIFEST.md).

Happy hacking!

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

Take a look at `main.py` for a demonstration of how a prompt is built from a common ancestor and branched into two variations.

## Core Concepts

- `PromptTerm`: A node containing the generated text, its origin, and pointers to its history.
- `PromptCombinator`: A function taking a `PromptTerm` and returning a new `PromptTerm`.
- `compose`: The engine of our $\beta$-reduction, linking combinators sequentially.
