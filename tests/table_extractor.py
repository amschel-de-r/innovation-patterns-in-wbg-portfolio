import argparse
import os
from pathlib import Path
import pandas as pd
from docx import Document
import re
from src._paths import TABLES_DIR
from src._paths import ANALYSIS_ROOT

docx_path = ANALYSIS_ROOT / "manuscript" / "PRWP working draft - Innovation Patterns in WBG Portfolio.docx"
out_dir = TABLES_DIR / "auto_extracted"

def clean_table_title(text: str) -> str:
 
    matches = list(re.finditer(r'Table', text, re.IGNORECASE))
    
    if len(matches) >= 2:
        second_table_pos = matches[1].start()
        text = text[:second_table_pos]
    
    return text.strip()
    
def clean_filename(text: str) -> str:
    """
    Convert text to a valid filename by removing/replacing invalid characters.
    """
    text = clean_table_title(text)
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    text = re.sub(r'\s+', '_', text.strip())
    text = text[:100]
    text = re.sub(r'3.9._Sectoral_Patterns_of_Innovation_in_GPs_3.93.9.._Sectoral_Sectoral_PPatterns_of_atterns_of_IInno', 'Table_3.9._Sectoral_Patterns_of_Innovation_in_GPs', text.strip())
    return text

def find_table_title(doc, table_index: int) -> str:
    """
    Find the title for a table by looking at paragraphs before it.
    Assumes title is in a paragraph immediately before the table.
    """
    # Get all elements (paragraphs and tables) in order
    body_elements = []
    for element in doc.element.body:
        if element.tag.endswith('p'):  # Paragraph
            body_elements.append(('p', element))
        elif element.tag.endswith('tbl'):  # Table
            body_elements.append(('tbl', element))
    
    # Find the table at table_index
    table_count = 0
    for i, (elem_type, elem) in enumerate(body_elements):
        if elem_type == 'tbl':
            if table_count == table_index:
                # Look backwards for a title (usually in previous paragraph)
                for j in range(i - 1, max(i - 5, -1), -1):  # Check up to 5 elements back
                    if body_elements[j][0] == 'p':
                        para_text = ''.join(
                            node.text for node in body_elements[j][1].iter() 
                            if hasattr(node, 'text') and node.text
                        ).strip()
                        if para_text:  # Found non-empty paragraph
                            return para_text
                break
            table_count += 1
    
    return None

def parse_cell_value(cell_text: str):
    """
    Convert cell text to appropriate data type:
    - Percentages (e.g., "1.3%") -> float (0.013)
    - Numbers with commas -> float or int
    - Plain numbers -> int or float
    - Everything else -> string
    """
    cell_text = cell_text.strip().replace('~', '')
    
    if not cell_text:
        return ""
    
    # Check for percentage
    percent_match = re.match(r'^(-?\d+(?:[.,]\d+)?)\s*%$', cell_text)
    if percent_match:
        # Extract number and convert to decimal
        num_str = percent_match.group(1).replace(',', '.')
        try:
            return float(num_str) / 100
        except ValueError:
            return cell_text
    
    # Check for plain number (possibly with thousands separators)
    # Remove common thousands separators
    cleaned = cell_text.replace(',', '').replace(' ', '')
    
    # Try to parse as number
    try:
        # Check if it's an integer
        if '.' not in cleaned and 'e' not in cleaned.lower():
            return int(cleaned)
        else:
            return float(cleaned)
    except ValueError:
        # Not a number, return as string
        return cell_text

def extract_tables(docx_path: Path, out_dir: Path) -> int:
    """
    Extract tables from a Word document to Excel files.
    
    Args:
        docx_path: Path to the input .docx file
        out_dir: Directory to save the extracted tables
    
    Returns:
        Number of tables extracted
    """
    doc = Document(str(docx_path))
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    table_count = 0
    
    for i, table in enumerate(doc.tables):
        rows = []
        max_cols = 0
        
        # Extract and parse cell values
        for row in table.rows:
            # Parse each cell value (convert percentages and numbers)
            cells = [parse_cell_value(cell.text) for cell in row.cells]
            rows.append(cells)
            max_cols = max(max_cols, len(cells))
        
        # Normalize row lengths
        normalized = [r + [""] * (max_cols - len(r)) for r in rows]
        df = pd.DataFrame(normalized)
        
        # Find table title
        title = find_table_title(doc, i)
        
        if title:
            # Use title as filename
            clean_title = clean_filename(title)
            filename = f"{clean_title}.xlsx"
        else:
            # Fallback to numbered naming
            filename = f"table_{i+1:02d}.xlsx"
        
        # Handle duplicate filenames
        out_path = out_dir / filename
       
        # Save to Excel
        df.to_excel(out_path, index=False, header=False)
        table_count += 1
        
        print(f"Extracted: {filename}")
    
    return table_count

def main():
    num_tables = extract_tables(docx_path, out_dir)

    T32 = pd.read_excel(out_dir/"Table_3.2._Contextualizing_the_Innovation_Intensity_of_Bank_Group_Projects_Over_Time.xlsx")[['Cohort','Share of High + Moderate Innovative Projects (%)']]
    T32.to_excel(out_dir/"Table_3.2._Contextualizing_the_Innovation_Intensity_of_Bank_Group_Projects_Over_Time.xlsx", index=False)
    T41 = pd.read_excel(out_dir/"Table_4.1._Importance_of_Context-Appropriate_Innovation.xlsx").drop(columns='Definition')
    T41.to_excel(out_dir/"Table_4.1._Importance_of_Context-Appropriate_Innovation.xlsx", index=False)
    TE6 = pd.read_excel(out_dir/"Table_E.6._Citations_of_Public-Private_Partnership_Arrangements_Across_the_Bank_Group_Portfolio.xlsx")[['Approximate Share of all PPP tags','Peak Decade(s)']]
    TE6.to_excel(out_dir/"Table_E.6._Citations_of_Public-Private_Partnership_Arrangements_Across_the_Bank_Group_Portfolio.xlsx", index=False)

    return num_tables


if __name__ == '__main__':
    main()