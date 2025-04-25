import os
import json
import re
import random
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# Load API key
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=API_KEY)

# Load synthetic data from JSON file
try:
    with open(r'C:\HACKTHON\corrected_dataset.json', 'r') as file:  # Use raw string or double backslashes
        synthetic_data = json.load(file)
        if not isinstance(synthetic_data, list):
            raise ValueError("Synthetic data should be a list of dictionaries.")
except Exception as e:
    st.error(f"Error loading synthetic data: {e}")
    synthetic_data = []

# Function to extract valid JSON from LLM response
def extract_json(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)  # Extract content between first '{' and last '}'
    if match:
        try:
            return json.loads(match.group())  # Convert extracted string to JSON
        except json.JSONDecodeError:
            return None
    return None

# Function to generate rule
def generate_rule(prompt):
    # Function to find relevant examples based on keyword matching
    def find_relevant_examples(prompt, examples, num_samples=5):
        keywords = set(prompt.lower().split())
        scored_examples = []

        for example in examples:
            example_keywords = set(example['input'].lower().split())
            score = len(keywords & example_keywords)  # Intersection of keywords
            scored_examples.append((score, example))

        # Sort examples by score in descending order and select top ones
        scored_examples.sort(reverse=True, key=lambda x: x[0])
        return [example for _, example in scored_examples[:num_samples]]

    # Find relevant examples from synthetic data
    relevant_examples = find_relevant_examples(prompt, synthetic_data)

    example_texts = "\n\n".join(
        f"Input: \"{example['input']}\"\nOutput: {json.dumps(example['output'], indent=2)}"
        for example in relevant_examples
    )

    query = f"""
    You are an expert with extensive experience in Business Rule Engines (BRE). Your task is to convert natural language statements into structured JSON rules. Below are some examples of how to perform this task:

    Examples:
    {example_texts}

    Now, please convert the following natural language statement into a structured JSON rule format. Identify and mark any variables that need to be calculated or derived from other data:

    "{prompt}"
    """

    response = client.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=[{'role': 'user', 'content': query}],
        temperature=0.7  # Adjust the temperature parameter
    )
    rule_text = response.choices[0].message.content.strip()

    # Log response for debugging
    print("LLM Response:", rule_text)

    # Extract and validate JSON
    rule_json = extract_json(rule_text)
    if rule_json:
        return rule_json
    else:
        return {
            "error": "Invalid JSON response",
            "raw_output": rule_text
        }



# Streamlit UI
st.set_page_config(page_title="AI-Powered Business Rules Engine", layout="wide")
st.title("AI-Powered Business Rules Engine")

st.markdown("""
<style>
    .main {
        background-color: #f0f2f6;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 24px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

st.subheader("Enter your rule in natural language:")
user_prompt = st.text_area("Rule Input", label_visibility="collapsed")

if st.button("Generate Rule"):
    if user_prompt:
        with st.spinner("Generating rule..."):
            rule_json = generate_rule(user_prompt)
            st.success("Rule generated successfully!")
            st.json(rule_json)
    else:
        st.warning("Please enter a rule.")

st.markdown("""
### How It Works
1. **Enter your rule**: Type a rule in plain English in the text area above.
2. **Generate Rule**: Click the "Generate Rule" button to convert your input into a structured JSON rule.
3. **Review and Refine**: Review the generated rule and make any necessary adjustments.

### Benefits
- **Increased Efficiency**: Reduces rule creation time significantly.
- **Lower Training Effort**: Minimizes the learning curve for new users.
- **Higher Accuracy**: Eliminates manual errors and improves consistency.
- **Greater Accessibility**: Enables a broader range of users to contribute to rule creation.
""")
