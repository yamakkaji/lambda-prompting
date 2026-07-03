import sys
from pathlib import Path
from pydantic import BaseModel, Field

# srcディレクトリをパスに追加してインポートできるようにする
sys.path.insert(0, str(Path(__file__).parent / "src"))

from lambda_prompting import (
    PromptTerm,
    compose,
    print_trace,
    with_few_shot,
    with_json_format,
    with_system_role,
    with_pydantic_schema,
    diff_terms,
)

# Pydanticモデルの定義
class ReviewResult(BaseModel):
    bug_found: bool = Field(..., description="Whether a bug was found in the code")
    suggestion: str = Field(..., description="Suggestion for fixing the bug or improving the code")


def main():
    # 1. 初期状態（ユーザーからの入力など）
    user_input = PromptTerm(
        text="Target code: `def add(a, b): return a - b`", 
        origin="User Input"
    )

    # 2. 共通のベースプロンプト（部分適用・再利用）
    base_prompt_builder = compose(
        with_few_shot(["Review check: variable naming", "Review check: return type"])
    )
    base_term = base_prompt_builder(user_input)

    # 3. ブランチ A: 従来の文字列ベースのJSON Format指定
    builder_a = compose(
        with_json_format('{"bug_found": bool, "suggestion": str}'),
        with_system_role("Expert Python Reviewer"),
    )
    term_a = builder_a(base_term)

    # 4. ブランチ B: 新しいPydantic統合スキーマ挿入
    builder_b = compose(
        with_pydantic_schema(ReviewResult),
        with_system_role("Friendly Python Assistant"), # ロールも少し変えて差分を明確に
    )
    term_b = builder_b(base_term)

    # 5. 結果の確認（ツリー差分）
    print("▼ プロンプト生成履歴の差分（Tree Diff）")
    print(diff_terms(term_a, term_b, name_a="Branch A (Manual)", name_b="Branch B (Pydantic)"))
    
    print("\n▼ 最終的にLLMに送られるテキスト (Branch B)")
    print("-" * 40)
    print(term_b.text)
    print("-" * 40)

if __name__ == "__main__":
    main()
