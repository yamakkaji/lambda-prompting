# Project Context: Lambda-Prompting Architecture

## 1. 解決したい課題 (The Problem)
現在のLLMにおけるプロンプトエンジニアリングは、自然言語の巨大な「文字列結合」に依存しており、モダンなソフトウェア開発（Code Writing）のパラダイムと決定的に乖離している。
* 型安全性がない: テキストエディタの補完や静的解析（Linter）が効かない。
* 変更履歴が追えない: プロンプトを書き換えた際、「どの意図（指示）を追加・削除したことで、出力がどう変わったか」の因果関係（Diff）が不明瞭になる。
* コンポーネント化の欠如: DSPyのようなツールは強力だが、内部がブラックボックス化しやすく、開発者が制御・デバッグしづらい。

## 2. 理論的背景 (Theoretical Framework)
LLMの推論プロセス（Autoregressive generation）は、本質的にラムダ計算（Lambda Calculus）として非常にシンプルに定式化できる。

$$
M = \lambda c. \text{next-token}(c)
$$

プロンプトエンジニアリングで行っている「システムプロンプトの付与」や「Few-shotの提示」は、ラムダ計算におけるカリー化（Currying）および部分適用（Partial Application）、そしてベータ簡約（$\beta$-reduction）に他ならない。

この作用機序に忠実に従い、プロンプトを「静的な文字列」ではなく「コンテキストを受け取り、新たなコンテキストを返す高階関数（コンビネータ）」として実装する。

## 3. アーキテクチャの基本概念 (Core Architecture)
単なる文字列の関数ではなく、「変更履歴（計算グラフ）」を保持するデータ構造を定義する。
* PromptTerm（項）:
最終的なテキスト（text）、それを生成した関数の由来（origin）、および元となった項への参照（children）を持つ。これによりプロンプトのAST（抽象構文木）を構築する。
* PromptCombinator（コンビネータ）:
PromptTerm を受け取り、新たな指示（System Role, JSON Formatなど）を付与した新しい PromptTerm を返す関数。
* compose（関数合成）:
複数のコンビネータを連鎖的に適用（ベータ簡約）し、最終的なプロンプトツリーを構築する。

## 4. プロトタイプコード (Proof of Concept)
以下は uv 環境で検証済みのリファレンス実装（hello-world.py）である。

```python
import functools
from dataclasses import dataclass, field
from typing import Callable

# 1. データの核：履歴を持つプロンプトオブジェクト
@dataclass
class PromptTerm:
    text: str
    origin: str
    children: list['PromptTerm'] = field(default_factory=list)

# 関数の型定義（PromptTermを受け取り、PromptTermを返す）
PromptCombinator = Callable[[PromptTerm], PromptTerm]

# 2. プロンプト関数（コンビネータ）の定義
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

# 3. パイプライン化（関数合成）
def compose(*functions: PromptCombinator) -> PromptCombinator:
    def _apply(arg: PromptTerm) -> PromptTerm:
        return functools.reduce(lambda term, func: func(term), functions, arg)
    return _apply

# 4. デバッグ用：プロンプトの系譜（Tree）を可視化する関数
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

    print("▼ プロンプトの生成履歴（Trace）")
    print_trace(final_prompt)
    print("\n▼ 最終的にLLMに送られるテキスト\n" + "-"*40)
    print(final_prompt.text)
    print("-" * 40)
```

## 5. 今後の開発アイディア・ロードマップ (Next Steps)
antigravity環境で実装・検証していきたい機能案：
* Pydanticとの統合 (CFG / Schema Injection)
`with_pydantic_schema(model_cls)` のように、Pydanticモデルを引数に取り、自動でJSON Schemaや文脈自由文法（BNF）を生成して挿入するコンビネータの実装。
* ツリー差分の可視化 (Diff Tracking)
2つの `PromptTerm` を比較し、「どのコンビネータが追加・削除されたか」をGitライクに可視化する関数 `diff_terms(term_a, term_b)` の実装。これによりA/Bテストとデバッグを容易にする。
* ローカルLLM（Ollama）および実行基盤とのシームレスな統合
生成された `PromptTerm` をそのまま実行できるクライアントラッパーの実装。遅延評価（Lazy Evaluation）を活用し、必要な時にだけAPIを叩く設計。
