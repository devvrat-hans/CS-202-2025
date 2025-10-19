import pandas as pd
import json
import csv
import xml.etree.ElementTree as ET
import re
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# ============================================================================
# CONFIGURATION
# ============================================================================

# Projects analyzed
PROJECTS = ['btop', 'ggml', 'OpenCC']

# Tools used
TOOLS = ['flawfinder', 'cppcheck', 'codeql']

# CWE Top 25 (2024) - https://cwe.mitre.org/top25/archive/2024/2024_cwe_top25.html
CWE_TOP_25 = [
    "CWE-79",   # Cross-site Scripting
    "CWE-787",  # Out-of-bounds Write
    "CWE-89",   # SQL Injection
    "CWE-352",  # Cross-Site Request Forgery (CSRF)
    "CWE-22",   # Path Traversal
    "CWE-125",  # Out-of-bounds Read
    "CWE-78",   # OS Command Injection
    "CWE-416",  # Use After Free
    "CWE-862",  # Missing Authorization
    "CWE-434",  # Unrestricted Upload of File with Dangerous Type
    "CWE-94",   # Code Injection
    "CWE-20",   # Improper Input Validation
    "CWE-77",   # Command Injection
    "CWE-287",  # Improper Authentication
    "CWE-269",  # Improper Privilege Management
    "CWE-502",  # Deserialization of Untrusted Data
    "CWE-200",  # Exposure of Sensitive Information
    "CWE-863",  # Incorrect Authorization
    "CWE-918",  # Server-Side Request Forgery (SSRF)
    "CWE-119",  # Memory Buffer Bounds
    "CWE-476",  # NULL Pointer Dereference
    "CWE-798",  # Hard-coded Credentials
    "CWE-190",  # Integer Overflow or Wraparound
    "CWE-400",  # Uncontrolled Resource Consumption
    "CWE-306",  # Missing Authentication for Critical Function
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_cppcheck_xml_to_csv(xml_file, csv_file):
    """
    Parse cppcheck XML output and convert to CSV format.
    
    Args:
        xml_file: Path to cppcheck XML report
        csv_file: Path to output CSV file
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['File', 'Line', 'Severity', 'ID', 'Message', 'Verbose', 'CWE', 'Column', 'Info', 'Symbol'])
        
        for error in root.findall(".//error"):
            eid = error.attrib.get('id', '')
            severity = error.attrib.get('severity', '')
            msg = error.attrib.get('msg', '')
            verbose = error.attrib.get('verbose', '')
            cwe = error.attrib.get('cwe', '')
            
            for loc in error.findall('location'):
                file = loc.attrib.get('file', '')
                line = loc.attrib.get('line', '')
                column = loc.attrib.get('column', '')
                info = loc.attrib.get('info', '')
                symbol = error.findtext('symbol', '')
                writer.writerow([file, line, severity, eid, msg, verbose, cwe, column, info, symbol])
    
    print(f"✓ Converted {xml_file} to {csv_file}")


def extract_cwe_from_sarif_tags(rule):
    """
    Extract CWE identifiers from SARIF rule tags.
    
    Args:
        rule: SARIF rule object containing properties/tags
        
    Returns:
        List of CWE IDs in format "CWE-XXX"
    """
    if not rule:
        return []
    
    tags = rule.get('properties', {}).get('tags', [])
    if not tags:
        return []
    
    cwe_ids = []
    cwe_pattern = re.compile(r'cwe-(\d+)', re.IGNORECASE)
    
    for tag in tags:
        match = cwe_pattern.search(tag)
        if match:
            cwe_id = f"CWE-{match.group(1)}"
            cwe_ids.append(cwe_id)
    
    return cwe_ids


def parse_codeql_sarif(sarif_file):
    """
    Parse CodeQL SARIF output and count CWE findings.
    
    Args:
        sarif_file: Path to CodeQL SARIF report
        
    Returns:
        Counter object with CWE counts
    """
    with open(sarif_file, 'r', encoding='utf-8') as f:
        sarif_data = json.load(f)
    
    cwe_counter = Counter()
    
    for run in sarif_data.get('runs', []):
        results = run.get('results', [])
        rules = run.get('tool', {}).get('driver', {}).get('rules', [])
        rule_map = {rule['id']: rule for rule in rules}
        
        for result in results:
            rule_id = result.get('ruleId')
            if not rule_id:
                continue
            
            rule = rule_map.get(rule_id)
            if not rule:
                continue
            
            cwe_ids = extract_cwe_from_sarif_tags(rule)
            for cwe_id in cwe_ids:
                cwe_counter[cwe_id] += 1
    
    return cwe_counter


def is_in_top_25(cwe_id):
    """
    Check if a CWE ID is in the Top 25 list.
    
    Args:
        cwe_id: CWE identifier string (e.g., "CWE-79")
        
    Returns:
        "YES" if in Top 25, "NO" otherwise
    """
    return "YES" if cwe_id in CWE_TOP_25 else "NO"


# ============================================================================
# DATA PROCESSING
# ============================================================================

def process_all_tools():
    """
    Process all tool outputs and create consolidated report.
    
    Returns:
        DataFrame with columns: Project_name, Tool_name, CWE_ID, Number_of_Findings, Is_In_CWE_Top_25?
    """
    
    # Convert cppcheck XML files to CSV
    print("\n" + "="*70)
    print("STEP 1: Converting cppcheck XML reports to CSV")
    print("="*70)
    for project in PROJECTS:
        xml_file = f"raw_reports/cppcheck_{project}.xml"
        csv_file = f"raw_reports/cppcheck_{project}.csv"
        parse_cppcheck_xml_to_csv(xml_file, csv_file)
    
    # Initialize consolidated DataFrame
    consolidated_data = []
    
    # Process flawfinder results
    print("\n" + "="*70)
    print("STEP 2: Processing flawfinder results")
    print("="*70)
    for project in PROJECTS:
        csv_file = f"raw_reports/flawfinder_{project}.csv"
        df = pd.read_csv(csv_file)
        
        # Split comma-separated CWEs and explode into separate rows
        df['CWEs'] = df['CWEs'].astype(str).str.split(',')
        df = df.explode('CWEs')
        df['CWEs'] = df['CWEs'].str.strip()
        
        # Count occurrences per CWE
        cwe_counts = df.groupby('CWEs').size().reset_index(name='Number_of_Findings')
        
        for _, row in cwe_counts.iterrows():
            cwe_id = row['CWEs']
            count = row['Number_of_Findings']
            
            consolidated_data.append({
                'Project_name': project,
                'Tool_name': 'flawfinder',
                'CWE_ID': cwe_id,
                'Number_of_Findings': count,
                'Is_In_CWE_Top_25?': is_in_top_25(cwe_id)
            })
        
        print(f"✓ Processed flawfinder results for {project}")
    
    # Process cppcheck results
    print("\n" + "="*70)
    print("STEP 3: Processing cppcheck results")
    print("="*70)
    for project in PROJECTS:
        csv_file = f"raw_reports/cppcheck_{project}.csv"
        df = pd.read_csv(csv_file)
        
        # Filter out rows with empty CWE values
        df = df[df['CWE'].notna()]
        
        # Count occurrences per CWE
        cwe_counts = df.groupby('CWE').size().reset_index(name='Number_of_Findings')
        
        for _, row in cwe_counts.iterrows():
            cwe_id = f"CWE-{int(row['CWE'])}"
            count = row['Number_of_Findings']
            
            consolidated_data.append({
                'Project_name': project,
                'Tool_name': 'cppcheck',
                'CWE_ID': cwe_id,
                'Number_of_Findings': count,
                'Is_In_CWE_Top_25?': is_in_top_25(cwe_id)
            })
        
        print(f"✓ Processed cppcheck results for {project}")
    
    # Process CodeQL SARIF results
    print("\n" + "="*70)
    print("STEP 4: Processing CodeQL SARIF results")
    print("="*70)
    for project in PROJECTS:
        sarif_file = f"raw_reports/codeql_{project}.sarif"
        cwe_counts = parse_codeql_sarif(sarif_file)
        
        # Save CodeQL results to CSV
        csv_file = f"raw_reports/codeql_{project}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['CWE_ID', 'Number_of_Findings'])
            writer.writeheader()
            for cwe_id, count in cwe_counts.items():
                writer.writerow({'CWE_ID': cwe_id, 'Number_of_Findings': count})
        
        for cwe_id, count in cwe_counts.items():
            consolidated_data.append({
                'Project_name': project,
                'Tool_name': 'codeql',
                'CWE_ID': cwe_id,
                'Number_of_Findings': count,
                'Is_In_CWE_Top_25?': is_in_top_25(cwe_id)
            })
        
        print(f"✓ Processed CodeQL results for {project}")
    
    # Create consolidated DataFrame
    df_consolidated = pd.DataFrame(consolidated_data)
    df_consolidated.to_csv('analysis_results/final_report.csv', index=False)
    print("\n" + "="*70)
    print("✓ Consolidated report saved to: analysis_results/final_report.csv")
    print("="*70)
    
    return df_consolidated


# ============================================================================
# CWE COVERAGE ANALYSIS
# ============================================================================

def analyze_cwe_coverage(df):
    """
    Analyze CWE coverage for each tool.
    
    Args:
        df: Consolidated findings DataFrame
    """
    print("\n" + "="*70)
    print("TOOL-LEVEL CWE COVERAGE ANALYSIS")
    print("="*70)
    
    coverage_data = []
    
    for tool in TOOLS:
        tool_data = df[df['Tool_name'] == tool]
        
        # Get unique CWEs detected
        unique_cwes = tool_data['CWE_ID'].unique()
        total_unique_cwes = len(unique_cwes)
        
        # Count Top 25 CWEs detected
        top25_cwes = [cwe for cwe in unique_cwes if cwe in CWE_TOP_25]
        top25_count = len(top25_cwes)
        top25_coverage = (top25_count / len(CWE_TOP_25)) * 100
        
        # Total findings
        total_findings = tool_data['Number_of_Findings'].sum()
        top25_findings = tool_data[tool_data['Is_In_CWE_Top_25?'] == 'YES']['Number_of_Findings'].sum()
        top25_findings_pct = (top25_findings / total_findings * 100) if total_findings > 0 else 0
        
        coverage_data.append({
            'Tool_name': tool,
            'Total_Unique_CWEs': total_unique_cwes,
            'Top25_CWEs_Detected': top25_count,
            'Top25_Coverage_Percent': top25_coverage,
            'Total_Findings': total_findings,
            'Top25_Findings': top25_findings,
            'Top25_Findings_Percent': top25_findings_pct
        })
        
        print(f"\n{tool.upper()}:")
        print(f"  Total Unique CWEs Detected:        {total_unique_cwes}")
        print(f"  Top 25 CWEs Detected:              {top25_count} / {len(CWE_TOP_25)}")
        print(f"  Top 25 CWE Coverage:               {top25_coverage:.2f}%")
        print(f"  Total Findings:                    {total_findings}")
        print(f"  Findings in Top 25 CWEs:           {top25_findings}")
        print(f"  % of Findings in Top 25:           {top25_findings_pct:.2f}%")
    
    coverage_df = pd.DataFrame(coverage_data)
    coverage_df.to_csv('analysis_results/tool_cwe_coverage.csv', index=False)
    print("\n✓ Coverage analysis saved to: analysis_results/tool_cwe_coverage.csv")
    
    return coverage_df


# ============================================================================
# PAIRWISE IoU ANALYSIS
# ============================================================================

def compute_iou_matrix(df):
    """
    Compute Intersection over Union (IoU) matrix for tool pairs.
    
    Args:
        df: Consolidated findings DataFrame
        
    Returns:
        DataFrame containing IoU matrix
    """
    print("\n" + "="*70)
    print("PAIRWISE AGREEMENT (IoU) ANALYSIS")
    print("="*70)
    
    # Get unique CWE sets for each tool
    tool_cwe_sets = {}
    for tool in TOOLS:
        tool_data = df[df['Tool_name'] == tool]
        tool_cwe_sets[tool] = set(tool_data['CWE_ID'].unique())
    
    # Compute IoU matrix
    iou_matrix = pd.DataFrame(index=TOOLS, columns=TOOLS, dtype=float)
    
    for tool1 in TOOLS:
        for tool2 in TOOLS:
            if tool1 == tool2:
                iou_matrix.loc[tool1, tool2] = 1.0
            else:
                set1 = tool_cwe_sets[tool1]
                set2 = tool_cwe_sets[tool2]
                
                intersection = len(set1 & set2)
                union = len(set1 | set2)
                
                iou = intersection / union if union > 0 else 0.0
                iou_matrix.loc[tool1, tool2] = iou
    
    print("\nIoU Matrix (Jaccard Index):")
    print(iou_matrix.to_string())
    
    iou_matrix.to_csv('analysis_results/iou_matrix.csv')
    print("\n✓ IoU matrix saved to: analysis_results/iou_matrix.csv")
    
    # Print interpretation
    print("\n" + "-"*70)
    print("INTERPRETATION:")
    print("-"*70)
    
    # Find tool pair with highest IoU (excluding diagonal)
    max_iou = 0
    max_pair = None
    for i, tool1 in enumerate(TOOLS):
        for j, tool2 in enumerate(TOOLS):
            if i < j:  # Only upper triangle
                iou_val = iou_matrix.loc[tool1, tool2]
                if iou_val > max_iou:
                    max_iou = iou_val
                    max_pair = (tool1, tool2)
    
    print(f"\nHighest agreement: {max_pair[0]} ↔ {max_pair[1]} (IoU = {max_iou:.4f})")
    
    # Find tool pair with lowest IoU
    min_iou = 1.0
    min_pair = None
    for i, tool1 in enumerate(TOOLS):
        for j, tool2 in enumerate(TOOLS):
            if i < j:
                iou_val = iou_matrix.loc[tool1, tool2]
                if iou_val < min_iou:
                    min_iou = iou_val
                    min_pair = (tool1, tool2)
    
    print(f"Lowest agreement:  {min_pair[0]} ↔ {min_pair[1]} (IoU = {min_iou:.4f})")
    
    # Analyze tool diversity
    print("\nTool Diversity Analysis:")
    for tool in TOOLS:
        unique_cwes = len(tool_cwe_sets[tool])
        # CWEs only found by this tool
        exclusive_cwes = tool_cwe_sets[tool]
        for other_tool in TOOLS:
            if other_tool != tool:
                exclusive_cwes = exclusive_cwes - tool_cwe_sets[other_tool]
        
        print(f"  {tool}: {unique_cwes} total CWEs, {len(exclusive_cwes)} exclusive")
    
    # Maximum coverage combination
    print("\nMaximum CWE Coverage by Tool Combination:")
    all_cwes = set()
    for tool in TOOLS:
        all_cwes |= tool_cwe_sets[tool]
    print(f"  All three tools combined: {len(all_cwes)} unique CWEs")
    
    # Check each pair
    for i, tool1 in enumerate(TOOLS):
        for j, tool2 in enumerate(TOOLS):
            if i < j:
                combined = tool_cwe_sets[tool1] | tool_cwe_sets[tool2]
                print(f"  {tool1} + {tool2}: {len(combined)} unique CWEs")
    
    return iou_matrix


# ============================================================================
# VISUALIZATION
# ============================================================================

def visualize_results(df, coverage_df, iou_matrix):
    """
    Create visualizations for the analysis.
    
    Args:
        df: Consolidated findings DataFrame
        coverage_df: Coverage analysis DataFrame
        iou_matrix: IoU matrix DataFrame
    """
    print("\n" + "="*70)
    print("GENERATING VISUALIZATIONS")
    print("="*70)
    
    # Set style
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (10, 6)
    
    # 1. Unique CWE Findings per Tool
    plt.figure(figsize=(10, 6))
    sns.barplot(data=coverage_df, x='Tool_name', y='Total_Unique_CWEs', palette='viridis')
    plt.title('Unique CWE Findings per Tool', fontsize=16, fontweight='bold')
    plt.xlabel('Tool Name', fontsize=12)
    plt.ylabel('Number of Unique CWEs', fontsize=12)
    plt.tight_layout()
    plt.savefig('visualizations/unique_cwe_findings_per_tool.png', dpi=300)
    print("✓ Saved: visualizations/unique_cwe_findings_per_tool.png")
    plt.close()
    
    # 2. Top 25 CWE Coverage per Tool
    plt.figure(figsize=(10, 6))
    sns.barplot(data=coverage_df, x='Tool_name', y='Top25_Coverage_Percent', palette='magma')
    plt.title('CWE Top 25 Coverage by Tool', fontsize=16, fontweight='bold')
    plt.xlabel('Tool Name', fontsize=12)
    plt.ylabel('Coverage of Top 25 CWEs (%)', fontsize=12)
    plt.ylim(0, 100)
    for i, row in coverage_df.iterrows():
        plt.text(i, row['Top25_Coverage_Percent'] + 2, 
                f"{row['Top25_Coverage_Percent']:.1f}%", 
                ha='center', fontsize=10, fontweight='bold')
    plt.tight_layout()
    plt.savefig('visualizations/top25_cwe_coverage_per_tool.png', dpi=300)
    print("✓ Saved: visualizations/top25_cwe_coverage_per_tool.png")
    plt.close()
    
    # 3. Percentage of Findings in Top 25 per Tool
    plt.figure(figsize=(10, 6))
    sns.barplot(data=coverage_df, x='Tool_name', y='Top25_Findings_Percent', palette='rocket')
    plt.title('Percentage of Findings in CWE Top 25 per Tool', fontsize=16, fontweight='bold')
    plt.xlabel('Tool Name', fontsize=12)
    plt.ylabel('% of Findings in Top 25', fontsize=12)
    for i, row in coverage_df.iterrows():
        plt.text(i, row['Top25_Findings_Percent'] + 1, 
                f"{row['Top25_Findings_Percent']:.1f}%", 
                ha='center', fontsize=10, fontweight='bold')
    plt.tight_layout()
    plt.savefig('visualizations/top25_findings_percentage_per_tool.png', dpi=300)
    print("✓ Saved: visualizations/top25_findings_percentage_per_tool.png")
    plt.close()
    
    # 4. IoU Heatmap
    plt.figure(figsize=(8, 6))
    sns.heatmap(iou_matrix.astype(float), annot=True, fmt='.3f', cmap='YlGnBu', 
                square=True, linewidths=1, cbar_kws={'label': 'IoU (Jaccard Index)'})
    plt.title('Pairwise Tool Agreement (IoU Matrix)', fontsize=16, fontweight='bold')
    plt.xlabel('Tool', fontsize=12)
    plt.ylabel('Tool', fontsize=12)
    plt.tight_layout()
    plt.savefig('visualizations/pairwise_iou_matrix.png', dpi=300)
    print("✓ Saved: visualizations/pairwise_iou_matrix.png")
    plt.close()
    
    # 5. Total Findings Distribution by Tool
    plt.figure(figsize=(10, 6))
    tool_findings = df.groupby('Tool_name')['Number_of_Findings'].sum().reset_index()
    sns.barplot(data=tool_findings, x='Tool_name', y='Number_of_Findings', palette='mako')
    plt.title('Total Vulnerability Findings by Tool', fontsize=16, fontweight='bold')
    plt.xlabel('Tool Name', fontsize=12)
    plt.ylabel('Total Number of Findings', fontsize=12)
    plt.tight_layout()
    plt.savefig('visualizations/total_findings_by_tool.png', dpi=300)
    print("✓ Saved: visualizations/total_findings_by_tool.png")
    plt.close()
    
    # 6. Findings Distribution by Project (per tool)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for idx, tool in enumerate(TOOLS):
        tool_data = df[df['Tool_name'] == tool]
        project_counts = tool_data.groupby('Project_name')['Number_of_Findings'].sum()
        axes[idx].pie(project_counts, labels=project_counts.index, autopct='%1.1f%%', startangle=90)
        axes[idx].set_title(f'{tool}', fontsize=12, fontweight='bold')
    plt.suptitle('Distribution of Findings Across Projects by Tool', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig('visualizations/findings_distribution_by_project.png', dpi=300)
    print("✓ Saved: visualizations/findings_distribution_by_project.png")
    plt.close()
    
    # 7. Top 10 Most Common CWEs Across All Tools
    top_cwes = df.groupby('CWE_ID')['Number_of_Findings'].sum().nlargest(10)
    plt.figure(figsize=(12, 6))
    sns.barplot(x=top_cwes.values, y=top_cwes.index, palette='coolwarm')
    plt.title('Top 10 Most Common CWEs (All Tools Combined)', fontsize=16, fontweight='bold')
    plt.xlabel('Total Number of Findings', fontsize=12)
    plt.ylabel('CWE ID', fontsize=12)
    plt.tight_layout()
    plt.savefig('visualizations/top10_cwes_overall.png', dpi=300)
    print("✓ Saved: visualizations/top10_cwes_overall.png")
    plt.close()
    
    print("\n" + "="*70)
    print("All visualizations completed!")
    print("="*70)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main execution function.
    """
    print("\n" + "="*70)
    print("LAB ASSIGNMENT 6: VULNERABILITY ANALYSIS TOOL EVALUATION")
    print("="*70)
    print(f"Projects: {', '.join(PROJECTS)}")
    print(f"Tools:    {', '.join(TOOLS)}")
    print("="*70)
    
    # Step 1: Process all tool outputs
    df = process_all_tools()
    
    # Step 2: Analyze CWE coverage
    coverage_df = analyze_cwe_coverage(df)
    
    # Step 3: Compute pairwise IoU
    iou_matrix = compute_iou_matrix(df)
    
    # Step 4: Generate visualizations
    visualize_results(df, coverage_df, iou_matrix)
    
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE!")
    print("="*70)
    print("\nGenerated Files:")
    print("  - final_report.csv")
    print("  - tool_cwe_coverage.csv")
    print("  - iou_matrix.csv")
    print("  - *.png (visualization files)")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
