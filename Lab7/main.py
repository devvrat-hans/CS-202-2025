import os
import re
import subprocess
import pandas as pd
from collections import defaultdict, deque

# Configuration
C_FILES_DIR = "c_files"
CFGS_DIR = "cfgs"
DOTS_DIR = "dots"
PNGS_DIR = "pngs"
OUTPUT_FILE = "analysis_results.txt"

# Ensure directories exist
for dir_path in [CFGS_DIR, DOTS_DIR, PNGS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# ============================================================================
# STEP 1: PARSE C FILES AND BUILD DETAILED CFG
# ============================================================================

def parse_c_file(file_path):
    """
    Parse a C file and extract the complete content for detailed CFG construction.
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Remove comments but preserve structure
    content = re.sub(r'//.*?\n', '\n', content)
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    
    return content


def identify_leaders(statements):
    """
    Identify leader statements (first statement of each basic block).
    Leaders are:
    1. First statement
    2. Target of any conditional/unconditional jump
    3. Statement following a conditional/unconditional jump
    """
    leaders = set()
    leaders.add(0)  # First statement is always a leader
    
    for i, stmt in enumerate(statements):
        stmt_lower = stmt.lower().strip()
        
        # Statement after control flow is a leader
        if i > 0:
            prev_stmt = statements[i-1].lower().strip()
            if (prev_stmt.startswith('if') or prev_stmt.startswith('else') or 
                prev_stmt.startswith('while') or prev_stmt.startswith('for') or
                prev_stmt.startswith('return') or prev_stmt.startswith('break') or
                prev_stmt.startswith('continue') or prev_stmt.endswith('}')):
                leaders.add(i)
        
        # Targets of branches are leaders
        if stmt_lower.startswith('if'):
            # Next statement after if condition
            if i + 1 < len(statements):
                leaders.add(i + 1)
        
        # Statement with opening brace often starts a new block
        if '{' in stmt and i + 1 < len(statements):
            leaders.add(i + 1)
        
        # Statement with closing brace - next is a leader
        if '}' in stmt and i + 1 < len(statements):
            leaders.add(i + 1)
    
    return sorted(leaders)


def build_detailed_cfg(content):
    """
    Build a very detailed CFG with many basic blocks.
    Creates fine-grained basic blocks for each statement or group of related statements.
    """
    # Split content into logical statements
    # Handle braces, semicolons, and control structures
    lines = content.split('\n')
    statements = []
    current_stmt = ""
    brace_depth = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        current_stmt += line + " "
        
        # Count braces
        brace_depth += line.count('{') - line.count('}')
        
        # End of statement conditions
        if (line.endswith(';') or line.endswith('{') or line.endswith('}') or
            line.startswith('if') or line.startswith('else') or 
            line.startswith('while') or line.startswith('for') or
            line.startswith('do') or line.startswith('case') or
            line.startswith('default') or line.startswith('break') or
            line.startswith('continue') or line.startswith('return')):
            
            if current_stmt.strip():
                statements.append(current_stmt.strip())
                current_stmt = ""
    
    if current_stmt.strip():
        statements.append(current_stmt.strip())
    
    # Identify leaders
    leaders = identify_leaders(statements)
    
    # Build basic blocks
    blocks = []
    block_id = 0
    
    for i in range(len(leaders)):
        start = leaders[i]
        end = leaders[i + 1] if i + 1 < len(leaders) else len(statements)
        
        block_stmts = statements[start:end]
        if block_stmts:
            blocks.append((block_id, block_stmts))
            block_id += 1
    
    # Build edges based on control flow
    edges = []
    for i, (bid, stmts) in enumerate(blocks):
        if not stmts:
            continue
        
        last_stmt = stmts[-1].lower().strip()
        
        # Sequential flow (no control flow statement)
        if not any(kw in last_stmt for kw in ['if', 'else', 'while', 'for', 'return', 'break', 'continue', 'goto']):
            if i + 1 < len(blocks):
                edges.append((bid, blocks[i + 1][0], ''))
        
        # If statement - branches to true and false paths
        elif last_stmt.startswith('if'):
            if i + 1 < len(blocks):
                edges.append((bid, blocks[i + 1][0], 'true'))
            # Find else block or fall-through
            for j in range(i + 2, len(blocks)):
                if any('else' in s.lower() for s in blocks[j][1]):
                    edges.append((bid, blocks[j][0], 'false'))
                    break
            else:
                # No else, fall through to next-next block
                if i + 2 < len(blocks):
                    edges.append((bid, blocks[i + 2][0], 'false'))
        
        # Else - sequential after else block
        elif 'else' in last_stmt:
            if i + 1 < len(blocks):
                edges.append((bid, blocks[i + 1][0], ''))
        
        # While/For loops - to body and to exit
        elif last_stmt.startswith('while') or last_stmt.startswith('for'):
            if i + 1 < len(blocks):
                edges.append((bid, blocks[i + 1][0], 'true'))  # Loop body
            # Find loop exit
            loop_depth = 1
            for j in range(i + 1, len(blocks)):
                for stmt in blocks[j][1]:
                    if '{' in stmt:
                        loop_depth += 1
                    if '}' in stmt:
                        loop_depth -= 1
                        if loop_depth == 0:
                            if j + 1 < len(blocks):
                                edges.append((bid, blocks[j + 1][0], 'false'))  # Loop exit
                            break
        
        # Return/Break - no outgoing edges (or to exit)
        elif 'return' in last_stmt or 'break' in last_stmt:
            pass  # Terminal or exit block
        
        # Continue - back to loop header (simplified: next block)
        elif 'continue' in last_stmt:
            # Try to find loop header
            for j in range(i - 1, -1, -1):
                block_stmts = blocks[j][1]
                if any('while' in s.lower() or 'for' in s.lower() for s in block_stmts):
                    edges.append((bid, blocks[j][0], ''))
                    break
        
        # Default sequential flow
        else:
            if i + 1 < len(blocks):
                edges.append((bid, blocks[i + 1][0], ''))
    
    return blocks, edges


def generate_cfg_files():
    """
    Parse C files and build detailed CFG structure with many basic blocks.
    """
    print("="*70)
    print("STEP 1: Parsing C files and building DETAILED CFG")
    print("="*70)
    
    c_files = [f for f in os.listdir(C_FILES_DIR) if f.endswith('.c')]
    
    for c_file in c_files:
        c_path = os.path.join(C_FILES_DIR, c_file)
        base_name = os.path.splitext(c_file)[0]
        
        print(f"\nProcessing: {c_file}")
        
        # Parse entire C file
        content = parse_c_file(c_path)
        
        # Build detailed CFG
        blocks, edges = build_detailed_cfg(content)
        
        print(f"  Generated {len(blocks)} basic blocks and {len(edges)} edges")
        
        # Store CFG data
        cfg_data = {
            'file': c_file,
            'blocks': blocks,
            'edges': edges,
            'total_blocks': len(blocks),
            'total_edges': len(edges)
        }
        
        # Save to file
        cfg_path = os.path.join(CFGS_DIR, f"{base_name}.cfg")
        import json
        with open(cfg_path, 'w') as f:
            json.dump(cfg_data, f, indent=2)
        
        print(f"  ✓ Generated: {base_name}.cfg")
    
    print("\n" + "="*70)


def generate_cfg_files():
    """
    Parse C files and build detailed CFG structure with many basic blocks.
    """
    print("="*70)
    print("STEP 1: Parsing C files and building DETAILED CFG")
    print("="*70)
    
    c_files = [f for f in os.listdir(C_FILES_DIR) if f.endswith('.c')]
    
    for c_file in c_files:
        c_path = os.path.join(C_FILES_DIR, c_file)
        base_name = os.path.splitext(c_file)[0]
        
        print(f"\nProcessing: {c_file}")
        
        # Parse entire C file
        content = parse_c_file(c_path)
        
        # Build detailed CFG
        blocks, edges = build_detailed_cfg(content)
        
        print(f"  Generated {len(blocks)} basic blocks and {len(edges)} edges")
        
        # Store CFG data
        cfg_data = {
            'file': c_file,
            'blocks': blocks,
            'edges': edges,
            'total_blocks': len(blocks),
            'total_edges': len(edges)
        }
        
        # Save to file
        cfg_path = os.path.join(CFGS_DIR, f"{base_name}.cfg")
        import json
        with open(cfg_path, 'w') as f:
            json.dump(cfg_data, f, indent=2)
        
        print(f"  ✓ Generated: {base_name}.cfg")
    
    print("\n" + "="*70)


# ============================================================================
# STEP 2: GENERATE DOT FILES FROM CFG
# ============================================================================

def generate_dot_files():
    """
    Convert CFG format to GraphViz DOT format for visualization.
    """
    print("\nSTEP 2: Generating DOT files from CFG")
    print("="*70)
    
    import json
    cfg_files = [f for f in os.listdir(CFGS_DIR) if f.endswith('.cfg')]
    
    for cfg_file in cfg_files:
        cfg_path = os.path.join(CFGS_DIR, cfg_file)
        base_name = os.path.splitext(cfg_file)[0]
        
        print(f"\nProcessing: {cfg_file}")
        
        with open(cfg_path, 'r') as f:
            cfg_data = json.load(f)
        
        blocks = cfg_data['blocks']
        edges = cfg_data['edges']
        
        # Generate DOT content
        dot_path = os.path.join(DOTS_DIR, f"{base_name}.dot")
        generate_dot_file(base_name, blocks, edges, dot_path)
        
        print(f"  ✓ Generated: {base_name}.dot ({len(blocks)} blocks, {len(edges)} edges)")
    
    print("\n" + "="*70)


def generate_dot_file(name, blocks, edges, output_path):
    """
    Generate GraphViz DOT file with detailed basic blocks.
    """
    dot_lines = [f'digraph {name}_CFG {{']
    dot_lines.append('    rankdir=TB;')
    dot_lines.append('    node [shape=box, style=filled, fillcolor=lightblue];')
    dot_lines.append('')
    
    # Add nodes with detailed labels
    for block_id, stmts in blocks:
        # Format label
        label_lines = [f"B{block_id}:"]
        
        # Add statements (truncate if too long)
        for stmt in stmts[:10]:  # First 10 statements
            stmt_clean = stmt.replace('"', '\\"').replace('{', '\\{').replace('}', '\\}').replace('\n', '\\n')
            # Truncate long statements
            if len(stmt_clean) > 50:
                stmt_clean = stmt_clean[:47] + "..."
            label_lines.append(stmt_clean)
        
        if len(stmts) > 10:
            label_lines.append("...")
        
        label = "\\n".join(label_lines)
        dot_lines.append(f'    B{block_id} [label="{label}"];')
    
    dot_lines.append('')
    
    # Add edges
    for edge in edges:
        if len(edge) == 3:
            src, dst, label = edge
        else:
            src, dst = edge
            label = ''
        
        if label:
            dot_lines.append(f'    B{src} -> B{dst} [label="{label}"];')
        else:
            dot_lines.append(f'    B{src} -> B{dst};')
    
    dot_lines.append('}')
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(dot_lines))


# ============================================================================
# STEP 3: GENERATE PNG IMAGES FROM DOT FILES
# ============================================================================

def generate_png_files():
    """
    Use GraphViz dot command to generate PNG images from DOT files.
    """
    print("\nSTEP 3: Generating PNG images from DOT files")
    print("="*70)
    
    dot_files = [f for f in os.listdir(DOTS_DIR) if f.endswith('.dot')]
    
    for dot_file in dot_files:
        dot_path = os.path.join(DOTS_DIR, dot_file)
        base_name = os.path.splitext(dot_file)[0]
        png_path = os.path.join(PNGS_DIR, f"{base_name}_cfg.png")
        
        print(f"\nProcessing: {dot_file}")
        
        cmd = f"dot -Tpng {dot_path} -o {png_path}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"  ✓ Generated: {base_name}_cfg.png")
        else:
            print(f"  ✗ Failed to generate PNG for {dot_file}")
            print(f"  Error: {result.stderr}")
    
    print("\n" + "="*70)


# ============================================================================
# STEP 4: CALCULATE CYCLOMATIC COMPLEXITY
# ============================================================================

def calculate_cyclomatic_complexity():
    """
    Calculate cyclomatic complexity from CFG data.
    CC = E - N + 2
    where E = number of edges, N = number of nodes
    """
    print("\nSTEP 4: Calculating Cyclomatic Complexity")
    print("="*70)
    
    import json
    results = []
    cfg_files = [f for f in os.listdir(CFGS_DIR) if f.endswith('.cfg')]
    
    if not cfg_files:
        print("\n  No CFG files found. Skipping cyclomatic complexity calculation.")
        return pd.DataFrame()
    
    for cfg_file in sorted(cfg_files):
        cfg_path = os.path.join(CFGS_DIR, cfg_file)
        base_name = os.path.splitext(cfg_file)[0]
        
        with open(cfg_path, 'r') as f:
            cfg_data = json.load(f)
        
        # Get node and edge counts from CFG data
        N = cfg_data['total_blocks']
        E = cfg_data['total_edges']
        
        # Calculate cyclomatic complexity
        CC = E - N + 2
        
        results.append({
            'Program Name': base_name,
            'No. of Nodes (N)': N,
            'No. of Edges (E)': E,
            'Cyclomatic Complexity (CC)': CC
        })
        
        print(f"\n{base_name}:")
        print(f"  Nodes (N): {N}")
        print(f"  Edges (E): {E}")
        print(f"  Cyclomatic Complexity (CC): {CC}")
    
    # Create DataFrame
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values('Cyclomatic Complexity (CC)', ascending=False).reset_index(drop=True)
        df.insert(0, 'Program No.', range(1, len(df) + 1))
        
        print("\n" + "="*70)
        print("\nCyclomatic Complexity Summary:")
        print(df.to_string(index=False))
    
    return df


# ============================================================================
# STEP 5: REACHING DEFINITIONS ANALYSIS
# ============================================================================

def perform_reaching_definitions():
    """
    Perform reaching definitions analysis on CFG files.
    """
    print("\n" + "="*70)
    print("STEP 5: Reaching Definitions Analysis")
    print("="*70)
    
    import json
    cfg_files = [f for f in os.listdir(CFGS_DIR) if f.endswith('.cfg')]
    
    all_results = []
    
    for cfg_file in sorted(cfg_files):
        cfg_path = os.path.join(CFGS_DIR, cfg_file)
        base_name = os.path.splitext(cfg_file)[0]
        
        print(f"\n{'='*70}")
        print(f"Analyzing: {base_name}")
        print('='*70)
        
        with open(cfg_path, 'r') as f:
            cfg_data = json.load(f)
        
        blocks = cfg_data['blocks']
        edges = cfg_data['edges']
        
        print(f"\nTotal blocks: {len(blocks)}, Total edges: {len(edges)}")
        
        # Extract definitions from blocks
        definitions = {}
        def_counter = 1
        
        for block_id, stmts in blocks:
            for stmt in stmts:
                # Look for assignment statements
                if '=' in stmt and not any(op in stmt for op in ['==', '!=', '<=', '>=', '++', '--']):
                    # Simple pattern for variable assignment
                    match = re.match(r'\s*(\w+)\s*=', stmt)
                    if match:
                        var_name = match.group(1)
                        # Skip type declarations
                        if var_name not in ['int', 'char', 'float', 'double', 'void', 'long', 'short', 'unsigned', 'signed', 'struct', 'typedef']:
                            def_id = f"D{def_counter}"
                            definitions[def_id] = (var_name, str(block_id), stmt[:80])  # Truncate long statements
                            def_counter += 1
        
        if not definitions:
            print(f"\n  No variable definitions found")
            continue
        
        print(f"\nTotal definitions found: {len(definitions)}")
        print(f"\n=== Definition Mapping (First 20) ===")
        print(f"{'DefID':<10} {'Variable':<20} {'Block':<10} {'Statement':<60}")
        print("-" * 100)
        for def_id, (var, block, stmt) in list(sorted(definitions.items()))[:20]:
            print(f"{def_id:<10} {var:<20} {block:<10} {stmt:<60}")
        
        if len(definitions) > 20:
            print(f"... and {len(definitions) - 20} more definitions")
        
        # Compute gen and kill sets
        gen_sets, kill_sets = compute_gen_kill_detailed(blocks, definitions)
        
        # Build predecessor map
        pred_map = build_predecessor_map_detailed([str(b[0]) for b in blocks], edges)
        
        # Compute reaching definitions
        in_sets, out_sets = compute_reaching_definitions_detailed([str(b[0]) for b in blocks], gen_sets, kill_sets, pred_map)
        
        # Print summary results (first 20 blocks)
        print(f"\n=== Reaching Definitions Results (First 20 Blocks) ===")
        print(f"{'Block':<10} {'|gen|':<10} {'|kill|':<10} {'|in|':<10} {'|out|':<10}")
        print("-" * 50)
        
        blocks_to_show = sorted([str(b[0]) for b in blocks], key=lambda x: int(x))[:20]
        for block in blocks_to_show:
            gen_size = len(gen_sets[block])
            kill_size = len(kill_sets[block])
            in_size = len(in_sets[block])
            out_size = len(out_sets[block])
            
            print(f"B{block:<9} {gen_size:<10} {kill_size:<10} {in_size:<10} {out_size:<10}")
        
        total_blocks = len([b[0] for b in blocks])
        if total_blocks > 20:
            print(f"... and {total_blocks - 20} more blocks")
        
        all_results.append({
            'program': base_name,
            'total_blocks': len(blocks),
            'total_edges': len(edges),
            'total_definitions': len(definitions),
            'definitions': definitions,
            'gen_sets': gen_sets,
            'kill_sets': kill_sets,
            'in_sets': in_sets,
            'out_sets': out_sets
        })
    
    return all_results


def compute_gen_kill_detailed(blocks, definitions):
    """
    Compute gen and kill sets for each basic block.
    """
    gen_sets = defaultdict(set)
    kill_sets = defaultdict(set)
    
    # Build variable to definition mapping
    var_to_defs = defaultdict(list)
    for def_id, (var, block, stmt) in definitions.items():
        var_to_defs[var].append(def_id)
    
    # Compute gen and kill for each block
    for block_id, stmts in blocks:
        block_str = str(block_id)
        
        # gen[B]: definitions generated in this block
        for def_id, (var, def_block, stmt) in definitions.items():
            if def_block == block_str:
                gen_sets[block_str].add(def_id)
                # Kill all other definitions of the same variable
                for other_def in var_to_defs[var]:
                    if other_def != def_id:
                        kill_sets[block_str].add(other_def)
    
    return gen_sets, kill_sets


def build_predecessor_map_detailed(blocks, edges):
    """
    Build a map from each block to its predecessors.
    """
    pred_map = defaultdict(list)
    for edge in edges:
        if len(edge) == 3:
            src, dst, label = edge
        else:
            src, dst = edge
        pred_map[str(dst)].append(str(src))
    return pred_map


def compute_reaching_definitions_detailed(blocks, gen_sets, kill_sets, pred_map):
    """
    Compute reaching definitions using iterative dataflow analysis.
    in[B] = ∪ out[P] for all predecessors P of B
    out[B] = gen[B] ∪ (in[B] - kill[B])
    """
    in_sets = defaultdict(set)
    out_sets = defaultdict(set)
    
    # Initialize
    for block in blocks:
        in_sets[block] = set()
        out_sets[block] = gen_sets[block].copy()
    
    # Iterate until convergence
    changed = True
    iteration = 0
    max_iterations = 100  # Prevent infinite loops
    
    while changed and iteration < max_iterations:
        changed = False
        iteration += 1
        
        for block in sorted(blocks, key=lambda x: int(x) if x.isdigit() else 0):
            # Compute in[B] = ∪ out[P]
            new_in = set()
            for pred in pred_map[block]:
                new_in |= out_sets[pred]
            
            # Compute out[B] = gen[B] ∪ (in[B] - kill[B])
            new_out = gen_sets[block] | (new_in - kill_sets[block])
            
            # Check for changes
            if new_in != in_sets[block] or new_out != out_sets[block]:
                changed = True
                in_sets[block] = new_in
                out_sets[block] = new_out
    
    print(f"\n  Converged after {iteration} iterations")
    
    return in_sets, out_sets


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main execution function.
    """
    print("\n" + "="*70)
    print("LAB ASSIGNMENT 7: REACHING DEFINITIONS ANALYZER FOR C PROGRAMS")
    print("="*70)
    print(f"\nAnalyzing C programs in: {C_FILES_DIR}/")
    
    # List C programs
    c_files = [f for f in os.listdir(C_FILES_DIR) if f.endswith('.c')]
    print(f"\nFound {len(c_files)} C programs:")
    for i, c_file in enumerate(c_files, 1):
        c_path = os.path.join(C_FILES_DIR, c_file)
        with open(c_path, 'r') as f:
            lines = len(f.readlines())
        print(f"  {i}. {c_file} ({lines} lines)")
    
    # Step 1: Generate CFG files
    generate_cfg_files()
    
    # Step 2: Generate DOT files
    generate_dot_files()
    
    # Step 3: Generate PNG images
    generate_png_files()
    
    # Step 4: Calculate cyclomatic complexity
    cc_df = calculate_cyclomatic_complexity()
    
    # Step 5: Perform reaching definitions analysis
    rd_results = perform_reaching_definitions()
    
    # Save results
    print("\n" + "="*70)
    print("SAVING RESULTS")
    print("="*70)
    
    # Save cyclomatic complexity table
    cc_df.to_csv('cyclomatic_complexity.csv', index=False)
    print(f"\n✓ Saved: cyclomatic_complexity.csv")
    
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE!")
    print("="*70)
    print(f"\nGenerated files:")
    print(f"  - CFG files: {CFGS_DIR}/")
    print(f"  - DOT files: {DOTS_DIR}/")
    print(f"  - PNG images: {PNGS_DIR}/")
    print(f"  - Cyclomatic complexity: cyclomatic_complexity.csv")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
