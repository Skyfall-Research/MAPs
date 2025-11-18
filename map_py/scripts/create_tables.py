import pandas as pd
import numpy as np

def create_main_latex_table_from_csv(csv_file_path, output_file_path=None):
    """
    Reads a CSV file and creates a LaTeX table with specified headers and structure.
    
    Args:
        csv_file_path (str): Path to the input CSV file
        output_file_path (str): Path to output LaTeX file (optional)
    """
    
    # Read the CSV file
    df = pd.read_csv(csv_file_path)
    
    # Create LaTeX table header
    latex_table = []
    latex_table.append("\\begin{table}[h!]")
    latex_table.append("\\centering")
    latex_table.append("\\begin{tabular}{|l|c|c|c|c|}")
    latex_table.append("\\hline")
    
    # Add data rows for each difficulty level
    difficulty_levels = ['easy', 'medium', 'hard']
    
    for difficulty in difficulty_levels:
        # Add difficulty header
        latex_table.append(f"\\multicolumn{{5}}{{c}}{{\\textbf{{{difficulty.capitalize()}}}}} \\\\")
        latex_table.append("\\hline")
        latex_table.append("Model & True Zero & Zero-shot & Few-shot & Unlimited \\\\")
        latex_table.append("\\midrule")
        
        # Add model results for this difficulty level
        for _, row in df.iterrows():
            model = row['model']
            
            true_zero = f"${row[f'{difficulty}_true_zero_mean']:.2f}_{{\\pm{row[f'{difficulty}_true_zero_se']:.2f}}}$"
            zero_shot = f"${row[f'{difficulty}_zero_shot_mean']:.2f}_{{\\pm{row[f'{difficulty}_zero_shot_se']:.2f}}}$"
            few_shot = f"${row[f'{difficulty}_few_shot_mean']:.2f}_{{\\pm{row[f'{difficulty}_few_shot_se']:.2f}}}$"
            unlimited = f"${row[f'{difficulty}_unlimited_mean']:.2f}_{{\\pm{row[f'{difficulty}_unlimited_se']:.2f}}}$"
            
            latex_table.append(f"{model} & {true_zero} & {zero_shot} & {few_shot} & {unlimited} \\\\")
        
        # Add separator line between difficulty levels (except for the last one)
        if difficulty != difficulty_levels[-1]:
            latex_table.append("\\hline")
    
    # Close the table
    latex_table.append("\\hline")
    latex_table.append("\\end{tabular}")
    latex_table.append("\\caption{Performance comparison across different models and difficulty levels}")
    latex_table.append("\\label{tab:model_comparison}")
    latex_table.append("\\end{table}")
    
    # Join all lines
    latex_content = "\n".join(latex_table)
    
    # Output to file if specified, otherwise print
    if output_file_path:
        with open(output_file_path, 'w') as f:
            f.write(latex_content)
        print(f"LaTeX table saved to {output_file_path}")
    else:
        print(latex_content)
    
    return latex_content

def create_challenge_latex_table_from_csv(csv_file_path, output_file_path=None):
    """
    Reads a CSV file and creates a LaTeX table with specified headers and structure.
    """
    df = pd.read_csv(csv_file_path)
    latex_table = []
    latex_table.append("\\begin{table}[h!]")
    latex_table.append("\\centering")
    latex_table.append("\\begin{tabular}{|l|c|l|}")
    latex_table.append("\\hline")
    latex_table.append("Base Model & Alteration & Performance \\\\")
    latex_table.append("\\hline")
    # for _, row in df.iterrows():
    #     model = row['model']
    #     performance = row['performance']
    #     latex_table.append(f"{model} & {performance} \\\\")

    latex_table.append("Human & None & TBD_{\pmTBD} \\\\")
    latex_table.append("SPRING & None & TBD_{\pmTBD} \\\\")
    latex_table.append("SPRING & w/ Spatial Heuristic & TBD_{\pmTBD} \\\\")
    latex_table.append("SPRING & Aggregate Statistics Only & TBD_{\pmTBD} \\\\")
    latex_table.append("SPRING & w/ Human Defined Subgoals & TBD_{\pmTBD} \\\\")

    latex_table.append("\\hline")
    latex_table.append("\\end{tabular}")
    latex_table.append("\\caption{Performance in easy mode using few-shot learning of various alternate models to highlight challenges of \envacro }")
    latex_table.append("\\label{tab:model_comparison}")
    latex_table.append("\\end{table}")
    latex_content = "\n".join(latex_table)
    return latex_content


def create_sample_csv():
    """
    Creates a sample CSV file with placeholder data for the specified models.
    """
    # Create sample data with three difficulty levels
    data = {
        'model': ['human', 'ReAct', 'SPRING', 'WALLE', 'PPO'],
        
        # Easy level data
        'easy_true_zero_mean': ["TBD", "TBD", "TBD", "TBD", "TBD"],
        'easy_true_zero_se': ["TBD", "TBD", "TBD", "TBD", "TBD"],
        'easy_zero_shot_mean': ["TBD", "TBD", "TBD", "TBD", "TBD"],
        'easy_zero_shot_se': ["TBD", "TBD", "TBD", "TBD", "TBD"],
        'easy_few_shot_mean': ["TBD", "TBD", "TBD", "TBD", "TBD"],
        'easy_few_shot_se': ["TBD", "TBD", "TBD", "TBD", "TBD"],
        'easy_unlimited_mean': ["TBD", "TBD", "TBD", "TBD", "TBD"],
        'easy_unlimited_se': ["TBD", "TBD", "TBD", "TBD", "TBD"],
        
        # Medium level data
        'medium_true_zero_mean': ["TBD", "TBD", "TBD", "TBD", "TBD"],
        'medium_true_zero_se': ["TBD", "TBD", "TBD", "TBD", "TBD"],
        'medium_zero_shot_mean': ["TBD", "TBD", "TBD", "TBD", "TBD"],
        'medium_zero_shot_se': ["TBD", "TBD", "TBD", "TBD", "TBD"],
        'medium_few_shot_mean': ["TBD", "TBD", "TBD", "TBD", "TBD"],
        'medium_few_shot_se': ["TBD", "TBD", "TBD", "TBD", "TBD"],
        'medium_unlimited_mean': ["TBD", "TBD", "TBD", "TBD", "TBD"],
        'medium_unlimited_se': ["TBD", "TBD", "TBD", "TBD", "TBD"],
        
        # Hard level data
        'hard_true_zero_mean': ["TBD", "TBD", "TBD", "TBD", "TBD"],
        'hard_true_zero_se': ["TBD", "TBD", "TBD", "TBD", "TBD"],
        'hard_zero_shot_mean': ["TBD", "TBD", "TBD", "TBD", "TBD"],
        'hard_zero_shot_se': ["TBD", "TBD", "TBD", "TBD", "TBD"],
        'hard_few_shot_mean': ["TBD", "TBD", "TBD", "TBD", "TBD"],
        'hard_few_shot_se': ["TBD", "TBD", "TBD", "TBD", "TBD"],
        'hard_unlimited_mean': ["TBD", "TBD", "TBD", "TBD", "TBD"],
        'hard_unlimited_se': ["TBD", "TBD", "TBD", "TBD", "TBD"]
    }
    
    df = pd.DataFrame(data)
    csv_path = 'sample_data.csv'
    df.to_csv(csv_path, index=False)
    print(f"Sample CSV created: {csv_path}")
    return csv_path

if __name__ == "__main__":
    # Create sample data
    sample_csv = create_sample_csv()
    
    # Generate LaTeX table
    latex_output = create_main_latex_table_from_csv(sample_csv, 'model_comparison_table.tex')
    
    print("\n" + "="*50)
    print("LaTeX Table Preview:")
    print("="*50)
    print(latex_output)