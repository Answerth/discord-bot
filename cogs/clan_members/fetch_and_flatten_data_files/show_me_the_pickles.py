import pandas as pd
from tabulate import tabulate
import textwrap
import pydoc

# Load the DataFrame from the pickle file
df = pd.read_pickle("activities_data.pkl")

# Wrap text in each cell to a max width of 50 characters
wrapped_df = df.applymap(lambda x: '\n'.join(textwrap.wrap(str(x), width=50)))

# Convert the DataFrame to a Markdown-style table
markdown_table = tabulate(wrapped_df, headers='keys', tablefmt='pipe', showindex=False)

# Paginate the output
pydoc.pager(markdown_table)
