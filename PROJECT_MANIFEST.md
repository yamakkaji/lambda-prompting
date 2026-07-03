# Project Context: Lambda-Prompting Architecture

## 1. The Problem
Prompt engineering in current LLMs relies heavily on massive "string concatenation" in natural language, which critically deviates from the paradigms of modern software development (Code Writing).
* Lack of Type Safety: Text editor autocompletion and static analysis (Linters) do not work.
* Untrackable History: When a prompt is rewritten, the cause-and-effect relationship (Diff) of "what intent/instruction was added or removed, and how that changed the output" becomes ambiguous.
* Lack of Componentization: Tools like DSPy are powerful, but their internals easily become a black box, making it difficult for developers to control and debug.

## 2. Theoretical Framework
The inference process of an LLM (Autoregressive generation) can be formulated very simply, essentially as Lambda Calculus.

$$
M = \lambda c. \text{next-token}(c)
$$

The "addition of a system role" or "presentation of few-shot examples" commonly performed in prompt engineering is nothing more than currying, partial application, and $\beta$-reduction in Lambda Calculus.

Strictly following this mechanism, we will implement prompts not as "static strings" but as "higher-order functions (combinators) that receive a context and return a new context."

## 3. Core Architecture
Instead of simply being functions of strings, we define data structures that retain a "modification history (computation graph)."

* PromptTerm (Term):
Holds the final text (`text`), the origin of the function that generated it (`origin`), and a reference to the terms it was derived from (`children`). This constructs the Abstract Syntax Tree (AST) of the prompt.
* PromptCombinator:
A function that receives a `PromptTerm`, attaches new instructions (System Role, JSON Format, etc.), and returns a new `PromptTerm`.
* compose (Function Composition):
Applies multiple combinators sequentially (chaining $\beta$-reductions) to construct the final prompt tree.

## 4. Proof of Concept
Below is the reference implementation (`hello-world.py`), verified in the `uv` environment.

```python
import functools
from dataclasses import dataclass, field
from typing import Callable

# 1. Data Core: Prompt object with history
@dataclass
class PromptTerm:
    text: str
    origin: str
    children: list['PromptTerm'] = field(default_factory=list)

# Function type definition (takes a PromptTerm, returns a PromptTerm)
PromptCombinator = Callable[[PromptTerm], PromptTerm]

# 2. Prompt Function (Combinator) Definitions
def with_system_role(role: str) -> PromptCombinator:
    def _apply(arg: PromptTerm) -> PromptTerm:
        new_text = f"【System Role: {role}】\n{arg.text}"
        return PromptTerm(text=new_text, origin=f"with_system_role('{role}')", children=[arg])
    return _apply

def with_json_format(schema: str) -> PromptCombinator:
    def _apply(arg: PromptTerm) -> PromptTerm:
        new_text = f"{arg.text}\n\n【Output Rules】\nReturn valid JSON matching: {schema}"
        return PromptTerm(text=new_text, origin="with_json_format", children=[arg])
    return _apply

def with_few_shot(examples: list[str]) -> PromptCombinator:
    def _apply(arg: PromptTerm) -> PromptTerm:
        examples_str = "\n".join(f"- {e}" for e in examples)
        new_text = f"【Examples】\n{examples_str}\n\n{arg.text}"
        return PromptTerm(text=new_text, origin=f"with_few_shot({len(examples)} items)", children=[arg])
    return _apply

# 3. Pipelining (Function Composition)
def compose(*functions: PromptCombinator) -> PromptCombinator:
    def _apply(arg: PromptTerm) -> PromptTerm:
        return functools.reduce(lambda term, func: func(term), functions, arg)
    return _apply

# 4. Debugging: Function to visualize the prompt's genealogy (Tree)
def print_trace(term: PromptTerm, depth: int = 0):
    indent = "  " * depth
    prefix = "└─ " if depth > 0 else ""
    print(f"{indent}{prefix}[{term.origin}]")
    for child in term.children:
        print_trace(child, depth + 1)

if __name__ == "__main__":
    user_input = PromptTerm(
        text="Target code: `def add(a, b): return a - b`", 
        origin="User Input"
    )

    build_reviewer_prompt = compose(
        with_few_shot(["Review check: variable naming", "Review check: return type"]),
        with_json_format('{"bug_found": bool, "suggestion": str}'),
        with_system_role("Expert Python Reviewer"),
    )

    final_prompt = build_reviewer_prompt(user_input)

    print("▼ Prompt Generation History (Trace)")
    print_trace(final_prompt)
    print("\n▼ Final Text Sent to LLM\n" + "-"*40)
    print(final_prompt.text)
    print("-" * 40)
```

## 5. Next Steps
Future features to be implemented and verified in the antigravity environment:
* Integration with Pydantic (CFG / Schema Injection)
Implementation of a combinator like `with_pydantic_schema(model_cls)`, which takes a Pydantic model as an argument and automatically generates and inserts a JSON Schema or Context-Free Grammar (BNF).
* Diff Tracking
Implementation of a function `diff_terms(term_a, term_b)` that compares two `PromptTerm` objects and visualizes "which combinators were added or removed" in a Git-like manner. This facilitates A/B testing and debugging.
* Seamless Integration with Local LLMs (Ollama) and Execution Infrastructure
Implementation of a client wrapper that can execute the generated `PromptTerm` as-is. A design utilizing Lazy Evaluation to hit the API only when necessary.
