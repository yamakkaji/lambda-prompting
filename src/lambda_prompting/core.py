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
    """複数のプロンプト関数を順番に適用（合成）する"""
    def _apply(arg: PromptTerm) -> PromptTerm:
        # functools.reduceを使って、関数を順番に連鎖適用（ベータ簡約の連鎖）させる
        return functools.reduce(lambda term, func: func(term), functions, arg)
    return _apply


def print_trace(term: PromptTerm, depth: int = 0):
    """プロンプトの系譜（Tree）を可視化するデバッグ用関数"""
    indent = "  " * depth
    prefix = "└─ " if depth > 0 else ""
    print(f"{indent}{prefix}[{term.origin}]")
    for child in term.children:
        print_trace(child, depth + 1)
