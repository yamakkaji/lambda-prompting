import functools
from dataclasses import dataclass, field
from typing import Callable

@dataclass
class PromptTerm:
    text: str
    origin: str
    children: list['PromptTerm'] = field(default_factory=list)

PromptCombinator = Callable[[PromptTerm], PromptTerm]

def compose(*functions: PromptCombinator) -> PromptCombinator:
    """Compose multiple prompt combinator functions sequentially."""
    def _apply(arg: PromptTerm) -> PromptTerm:
        # Chain function applications sequentially using functools.reduce (beta-reduction chain)
        return functools.reduce(lambda term, func: func(term), functions, arg)
    return _apply

def print_trace(term: PromptTerm, depth: int = 0):
    """Debug function to visualize the genealogy (Tree) of the prompt."""
    indent = "  " * depth
    prefix = "└─ " if depth > 0 else ""
    print(f"{indent}{prefix}[{term.origin}]")
    for child in term.children:
        print_trace(child, depth + 1)
