
import pandas as pd
import os
from tqdm import tqdm

directory_path = './user_data/'

files = os.listdir(directory_path)

csv_files = [f for f in files if f.endswith('.csv')]

merged_data = pd.DataFrame()
counter = 0
for file in tqdm(csv_files, desc="Merging files"):
    df = pd.read_csv(os.path.join(directory_path, file))
    userid = file.split('_')[1].split('_')[0]
    df['userid'] = userid
    merged_data = pd.concat([merged_data, df], ignore_index=True)
    counter += 1

merged_data.head()

merged_csv_filename = f'./{counter}_user_data.csv'

# Save the merged data to CSV
merged_data.to_csv(merged_csv_filename, index=False)
