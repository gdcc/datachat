import re

def llmprompts(description):
    llmprompt_cr = (
f"Below is a JSON-LD object describing a dataset: {description}\n\n"
"What is the title of the dataset and who is author and creator? Mention a few authors if there are present."
"To which country data belong?"
"What is about? Give possible categories"
"When dataset was created?"
"What is the source of the data?"
"What is the purpose of the dataset?"
"What are the key features (columns/variables) in the dataset?"
"What is the size of the dataset (number of rows and columns)?"
"Are there any missing or null values?"
"What is the data type of each feature (categorical, numerical, etc.)?"
"Are there any outliers or anomalies?"
"Is the data balanced or imbalanced (especially for classification problems)?"
"How was the data collected, and over what time period?"
"What are the potential biases in the dataset?"
"What preprocessing steps (e.g., normalization, encoding) are required?"
"How frequently is the dataset updated?"
"Are there any privacy or ethical concerns regarding this data?"
"What are the target variables (if any)?"
"Are there any relationships or correlations between the features?"
"Give me up to 10 questions on which the content of the dataset can respond base on its description and title"
    ) 
    return llmprompt_cr
