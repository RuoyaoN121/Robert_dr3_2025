import pandas as pd
import os

def compare_csv(file1, file2, base_dir):
    # Read the CSV files
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)

    # Get the columns
    columns1 = set(df1.columns)
    columns2 = set(df2.columns)

    # Find common columns
    common_columns = columns1.intersection(columns2)

    common_values_dict = {}
    diff_values1_dict = {}
    diff_values2_dict = {}

    for column in common_columns:
        print(f"Comparing column: {column}")
        values1 = set(df1[column])
        values2 = set(df2[column])

        common_values = values1.intersection(values2)
        diff_values1 = values1.difference(values2)
        diff_values2 = values2.difference(values1)

        # Store the values in dictionaries
        common_values_dict[column] = list(common_values)
        diff_values1_dict[column] = list(diff_values1)
        diff_values2_dict[column] = list(diff_values2)

    # Save the common values to a CSV file
    common_values_df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in common_values_dict.items()]))
    common_values_df.to_csv(os.path.join(base_dir, 'common_values_all_columns.csv'), index=False)

    # Save the different values to CSV files
    diff_values1_df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in diff_values1_dict.items()]))
    diff_values1_df.to_csv(os.path.join(base_dir, f'diff_values_{os.path.basename(file1)}_all_columns.csv'), index=False)

    diff_values2_df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in diff_values2_dict.items()]))
    diff_values2_df.to_csv(os.path.join(base_dir, f'diff_values_{os.path.basename(file2)}_all_columns.csv'), index=False)

if __name__ == "__main__":
    base_dir = r'/fred/oz002/users/mbailes/astral/timing2025/compare_epochs/'
    file1 = os.path.join(base_dir, 'partim_matt_vs_partim_robert_unique.csv')
    file2 = os.path.join(base_dir, 'partim_deleted_vs_partim_robert_unique.csv')
    compare_csv(file1, file2, base_dir)