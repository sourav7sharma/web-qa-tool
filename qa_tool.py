import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize OpenAI client
client = OpenAI(api_key="sk-your-openai-key")  # Replace with your key

def scrape_url(url):
    """Scrape text content from a URL"""
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unnecessary elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()
            
        text = ' '.join(soup.stripped_strings)
        return text[:10000]  # Limit to first 10k characters
    except Exception as e:
        st.error(f"Error scraping {url}: {str(e)}")
        return None

def find_relevant_chunks(question, chunks):
    """Find most relevant text chunks using TF-IDF"""
    vectorizer = TfidfVectorizer().fit_transform([question] + chunks)
    vectors = vectorizer.toarray()
    similarities = cosine_similarity(vectors[0:1], vectors[1:])[0]
    most_relevant = chunks[similarities.argmax()]
    return most_relevant

def generate_answer(question, context):
    """Generate answer using OpenAI with context constraint"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # Updated model
        messages=[
            {"role": "system", "content": "You answer questions strictly based on the provided context."},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
        ],
        max_tokens=150,
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

# Streamlit UI remains the same
st.title("Web Content Q&A Tool")

# URL Input
urls = st.text_area("Enter URLs (one per line)", height=100).split('\n')
if st.button("Ingest URLs"):
    with st.spinner("Scraping content..."):
        scraped_data = []
        for url in urls:
            if url.strip():
                content = scrape_url(url.strip())
                if content:
                    scraped_data.append((url, content))
        
        st.session_state['content'] = scraped_data
        st.success(f"Ingested {len(scraped_data)} URLs")

# Question Input
question = st.text_input("Ask a question about the content")
if question and 'content' in st.session_state:
    with st.spinner("Analyzing..."):
        # Prepare text chunks
        chunks = [f"URL: {url}\nContent: {content[:2000]}" 
                 for url, content in st.session_state['content']]
        
        # Find relevant content
        context = find_relevant_chunks(question, chunks)
        
        # Generate answer
        answer = generate_answer(question, context)
        
        # Display results
        st.subheader("Answer")
        st.write(answer)
        
        st.subheader("Source")
        st.write(context.split("\nContent:")[0].replace("URL: ", ""))