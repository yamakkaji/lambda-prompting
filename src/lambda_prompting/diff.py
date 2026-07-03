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

def diff_terms(term_a: PromptTerm, term_b: PromptTerm, name_a: str = "term_a", name_b: str = "term_b", use_color: bool = True) -> str:
    """
    Compare the generation history of two PromptTerms and output a Git tree-like diff in ASCII art.
    """
    path_a = _get_path(term_a)
    path_b = _get_path(term_b)
    
    # ANSI Color Codes
    c_reset = "\033[0m" if use_color else ""
    c_a = "\033[32m" if use_color else ""      # Green for Branch A
    c_b = "\033[36m" if use_color else ""      # Cyan for Branch B
    c_common = "\033[90m" if use_color else "" # Gray for common path
    c_node = "\033[33m" if use_color else ""   # Yellow for the node origin
    
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
            label = f" {c_b}({name_b}){c_reset}" if ub is unique_b[-1] else ""
            lines.append(f"{c_b}*{c_reset} [{c_node}{ub.origin}{c_reset}]{label}")
        for ua in reversed(unique_a):
            label = f" {c_a}({name_a}){c_reset}" if ua is unique_a[-1] else ""
            lines.append(f"{c_b}|{c_reset} {c_a}*{c_reset} [{c_node}{ua.origin}{c_reset}]{label}")
        lines.append(f"{c_b}|/{c_reset}")
    elif unique_b: # Only term_b has advanced
        for ub in reversed(unique_b):
            label = f" {c_b}({name_b}){c_reset}" if ub is unique_b[-1] else ""
            lines.append(f"{c_b}*{c_reset} [{c_node}{ub.origin}{c_reset}]{label}")
    elif unique_a: # Only term_a has advanced
        for ua in reversed(unique_a):
            label = f" {c_a}({name_a}){c_reset}" if ua is unique_a[-1] else ""
            lines.append(f"{c_a}*{c_reset} [{c_node}{ua.origin}{c_reset}]{label}")
            
    # Draw common path
    common = path_a[:common_len]
    for i, c in enumerate(reversed(common)):
        label = ""
        if i == 0:
            if not unique_a and not unique_b:
                label = f" {c_common}({name_a}, {name_b}){c_reset}"
            elif not unique_a and unique_b:
                label = f" {c_a}({name_a}){c_reset}"
            elif not unique_b and unique_a:
                label = f" {c_b}({name_b}){c_reset}"
                
        lines.append(f"{c_common}*{c_reset} [{c_node}{c.origin}{c_reset}]{label}")
        
    return "\n".join(lines)


def render_tree(named_terms: dict[str, PromptTerm], use_color: bool = True) -> str:
    """
    Given a dictionary of branch names and their corresponding PromptTerms,
    render a forward-facing ASCII tree (like the `tree` command) supporting N branches.
    """
    c_reset = "\033[0m" if use_color else ""
    c_branch = "\033[36m" if use_color else ""  # Cyan for tree lines
    c_node = "\033[33m" if use_color else ""    # Yellow for nodes
    c_label = "\033[32m" if use_color else ""   # Green for labels
    
    term_map = {}
    children_map = {}
    
    # 1. Build the forward graph from backward pointers
    for term in named_terms.values():
        current = term
        while True:
            tid = id(current)
            if tid not in term_map:
                term_map[tid] = current
                children_map[tid] = []
            
            if not current.children:
                break
                
            parent = current.children[0]
            pid = id(parent)
            
            if pid not in term_map:
                term_map[pid] = parent
                children_map[pid] = []
                
            if tid not in [id(c) for c in children_map[pid]]:
                children_map[pid].append(current)
                
            current = parent
            
    # 2. Traverse and print from roots
    roots = [tid for tid, t in term_map.items() if not t.children]
    lines = []
    
    def _traverse(node_id, prefix=""):
        term = term_map[node_id]
        
        # Check if this node is one of the named terms (leaves)
        labels = [name for name, t in named_terms.items() if id(t) == node_id]
        label_str = f" {c_label}({', '.join(labels)}){c_reset}" if labels else ""
        
        node_str = f"{c_node}[{term.origin}]{c_reset}"
        
        child_nodes = children_map[node_id]
        
        if not prefix: # Root
            lines.append(f"{node_str}{label_str}")
        else:
            lines.append(f"{c_branch}{prefix}{c_reset}{node_str}{label_str}")
            
        for i, child in enumerate(child_nodes):
            is_last = (i == len(child_nodes) - 1)
            if not prefix:
                next_prefix = "└── " if is_last else "├── "
            else:
                base = prefix.replace("├── ", "│   ").replace("└── ", "    ")
                next_prefix = base + ("└── " if is_last else "├── ")
            
            _traverse(id(child), next_prefix)
            
    for root_id in roots:
        _traverse(root_id)
        
    return "\n".join(lines)

