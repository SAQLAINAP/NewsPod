import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from lambeq import AtomicType, IQPAnsatz, BobcatParser, TketModel
from sympy import symbols
from pytket.extensions.qiskit import AerBackend
import numpy as np

# Download NLTK data
nltk.download('punkt')
nltk.download('stopwords')

# Topics mapping
TOPICS = [
    'Quantum Computing', 'Blockchain', 'General Knowledge', 'Political News', 
    'Science', 'Artificial Intelligence', 'Machine Learning', 'Deep Learning', 
    'Data Science', 'Neural Networks', 'Geography', 'History', 'Sports'
]

# Web scraping function
def scrape_sciencedaily():
    url = "https://www.sciencedaily.com/news/top/science/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    titles = [title.text for title in soup.find_all('h3')]
    return titles

# Preprocessing function
def preprocess_text(text):
    stop_words = set(stopwords.words('english'))
    words = word_tokenize(text.lower())
    return [word for word in words if word.isalnum() and word not in stop_words]

# Quantum NLP categorization
def categorize_titles_with_qnlp(titles):
    parser = BobcatParser(root_types=[AtomicType.SENTENCE])
    ansatz = IQPAnsatz({AtomicType.NOUN: 1, AtomicType.SENTENCE: 1})

    backend = AerBackend()
    params = symbols('params:10')
    model = TketModel.from_diagrams(
        ansatz([AtomicType.SENTENCE], parser.sentences_to_diagrams(titles)), 
        backend
    )

    categories = []
    for title in titles:
        processed_title = preprocess_text(title)
        if not processed_title:
            categories.append("Uncategorized")
            continue
        
        diagram = parser.sentences_to_diagrams([" ".join(processed_title)])[0]
        q_circuit = ansatz([AtomicType.SENTENCE], [diagram])

        probabilities = model.predict_probabilities(q_circuit)
        predicted_category = TOPICS[np.argmax(probabilities)]
        categories.append(predicted_category)

    return categories

# Streamlit app
def main():
    st.title("Web Scraping and Quantum NLP with Lambeq")
    st.write("This app scrapes titles from ScienceDaily and categorizes them using Quantum NLP!")

    # Step 1: Web Scraping
    if st.button("Scrape Titles"):
        titles = scrape_sciencedaily()
        st.success(f"Scraped {len(titles)} titles!")
        st.write(titles)
        st.session_state['titles'] = titles

    # Step 2: Categorization
    if 'titles' in st.session_state:
        if st.button("Categorize Titles"):
            titles = st.session_state['titles']
            categories = categorize_titles_with_qnlp(titles)
            st.session_state['categories'] = categories

            df = pd.DataFrame({'Title': titles, 'Category': categories})
            st.dataframe(df)
            st.session_state['df'] = df

    # Step 3: Download Results
    if 'df' in st.session_state:
        df = st.session_state['df']
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Categorized Titles as CSV",
            data=csv,
            file_name='categorized_titles.csv',
            mime='text/csv'
        )

if __name__ == "__main__":
    main()