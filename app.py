from flask import Flask, request, jsonify, render_template
from src.helper import load_pdf_files, filter_to_minimal_docs, text_split, download_embeddings
from langchain_pinecone import PineconeVectorStore
from langchain_groq import ChatGroq
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from src.prompt import *
from dotenv import load_dotenv
import os


app = Flask(__name__)

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

embedding = download_embeddings()
index_name = "medical-chatbot"

doc_search = PineconeVectorStore.from_existing_index(
    embedding=embedding,
    index_name=index_name,
)

retriever = doc_search.as_retriever(search_type="similarity", search_kwargs={"k":3})
chat_model = ChatGroq(model="llama3-8b-8192")
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}")
])
question_answering_chain = create_stuff_documents_chain(chat_model, prompt)
rag_chain = create_retrieval_chain(retriever, question_answering_chain)

@app.route('/')
def index(): 
    return render_template('chat.html')

@app.route('/get', methods=['GET', 'POST'])
def chat():
    user_query = request.form.get('msg')
    response = rag_chain.invoke({"input": user_query})
    return str(response['answer'])

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)