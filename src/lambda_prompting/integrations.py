import json
from typing import Type
from pydantic import BaseModel
from .core import PromptCombinator, PromptTerm

def with_pydantic_schema(model_cls: Type[BaseModel]) -> PromptCombinator:
    """
    PydanticのモデルからJSON Schemaを生成し、出力ルールとして付与するコンビネータ
    """
    def _apply(arg: PromptTerm) -> PromptTerm:
        schema = model_cls.model_json_schema()
        schema_str = json.dumps(schema, indent=2)
        new_text = f"{arg.text}\n\n【Output Rules】\nReturn valid JSON matching the following schema:\n{schema_str}"
        return PromptTerm(text=new_text, origin=f"with_pydantic_schema('{model_cls.__name__}')", children=[arg])
    return _apply
