from typing import List
from .core import PromptCombinator, PromptTerm

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

def with_few_shot(examples: List[str]) -> PromptCombinator:
    def _apply(arg: PromptTerm) -> PromptTerm:
        examples_str = "\n".join(f"- {e}" for e in examples)
        new_text = f"【Examples】\n{examples_str}\n\n{arg.text}"
        return PromptTerm(text=new_text, origin=f"with_few_shot({len(examples)} items)", children=[arg])
    return _apply
