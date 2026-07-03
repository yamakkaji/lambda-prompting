from .core import PromptTerm

def _get_path(term: PromptTerm) -> list[PromptTerm]:
    """ルート（User Input等）から引数の項までの適用履歴（パス）を順に取得する"""
    path = []
    current = term
    while True:
        path.append(current)
        if not current.children:
            break
        # 現在の実装では単一の親(引数)を持つ前提（線形リスト）
        current = current.children[0]
    return list(reversed(path))

def diff_terms(term_a: PromptTerm, term_b: PromptTerm, name_a: str = "term_a", name_b: str = "term_b") -> str:
    """
    2つのPromptTermの生成履歴を比較し、Gitツリー風の差分をアスキーアートで出力する。
    """
    path_a = _get_path(term_a)
    path_b = _get_path(term_b)
    
    # 共通祖先を特定
    common_len = 0
    for a, b in zip(path_a, path_b):
        # originの文字列で同値性を判定
        if a.origin == b.origin:
            common_len += 1
        else:
            break
            
    lines = []
    unique_a = path_a[common_len:]
    unique_b = path_b[common_len:]
    
    # 分岐の描画
    if unique_a and unique_b:
        for ub in reversed(unique_b):
            label = f" ({name_b})" if ub is unique_b[-1] else ""
            lines.append(f"* [{ub.origin}]{label}")
        for ua in reversed(unique_a):
            label = f" ({name_a})" if ua is unique_a[-1] else ""
            lines.append(f"| * [{ua.origin}]{label}")
        lines.append("|/")
    elif unique_b: # term_b のみが進んでいる
        for ub in reversed(unique_b):
            label = f" ({name_b})" if ub is unique_b[-1] else ""
            lines.append(f"* [{ub.origin}]{label}")
    elif unique_a: # term_a のみが進んでいる
        for ua in reversed(unique_a):
            label = f" ({name_a})" if ua is unique_a[-1] else ""
            lines.append(f"* [{ua.origin}]{label}")
            
    # 共通部分の描画
    common = path_a[:common_len]
    for i, c in enumerate(reversed(common)):
        label = ""
        if i == 0:
            if not unique_a and not unique_b:
                label = f" ({name_a}, {name_b})"
            elif not unique_a and unique_b:
                label = f" ({name_a})"
            elif not unique_b and unique_a:
                label = f" ({name_b})"
                
        lines.append(f"* [{c.origin}]{label}")
        
    return "\n".join(lines)
