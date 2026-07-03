from .core import PromptTerm

def _get_path(term: PromptTerm) -> list[PromptTerm]:
    """Retrieve the application history (path) in order from the root (e.g. User Input) to the given term."""
    path = []
    current = term
    while True:
        path.append(current)
        if not current.children:
            break
        # Assuming a single parent (argument) in the current linear list implementation
        current = current.children[0]
    return list(reversed(path))

def diff_terms(term_a: PromptTerm, term_b: PromptTerm, name_a: str = "term_a", name_b: str = "term_b") -> str:
    """
    Compare the generation history of two PromptTerms and output a Git tree-like diff in ASCII art.
    """
    path_a = _get_path(term_a)
    path_b = _get_path(term_b)
    
    # Identify the common ancestor
    common_len = 0
    for a, b in zip(path_a, path_b):
        # Determine equality by origin string
        if a.origin == b.origin:
            common_len += 1
        else:
            break
            
    lines = []
    unique_a = path_a[common_len:]
    unique_b = path_b[common_len:]
    
    # Draw branches
    if unique_a and unique_b:
        for ub in reversed(unique_b):
            label = f" ({name_b})" if ub is unique_b[-1] else ""
            lines.append(f"* [{ub.origin}]{label}")
        for ua in reversed(unique_a):
            label = f" ({name_a})" if ua is unique_a[-1] else ""
            lines.append(f"| * [{ua.origin}]{label}")
        lines.append("|/")
    elif unique_b: # Only term_b has advanced
        for ub in reversed(unique_b):
            label = f" ({name_b})" if ub is unique_b[-1] else ""
            lines.append(f"* [{ub.origin}]{label}")
    elif unique_a: # Only term_a has advanced
        for ua in reversed(unique_a):
            label = f" ({name_a})" if ua is unique_a[-1] else ""
            lines.append(f"* [{ua.origin}]{label}")
            
    # Draw common path
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
