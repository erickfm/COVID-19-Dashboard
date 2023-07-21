import streamlit as st
import os
import time
import pinecone
from langchain import OpenAI
from langchain.chains.question_answering import load_qa_chain
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Pinecone


def save_texts(texts):
    with open(texts.name, "wb") as f:
        f.write(texts.getbuffer())
    return texts.name


@st.cache_resource(show_spinner=False)
def split_files(files):
    documents = []
    for file in files:
        with st.spinner(f'✂️ Splitting {file.name}...'):
            save_location = save_texts(file)
            loader = PyPDFLoader(save_location)
            data = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=0)
            for text_split in text_splitter.split_documents(data):
                if not file.name:
                    st.write(file)
                    st.stop()
                document = [{'text': text_split, 'filename': file.name}]
                documents += document
    return documents


@st.cache_resource(show_spinner=False)
def vectorize_documents(_documents, number_of_documents):
    temp = st.empty()
    texts = [doc['text'].page_content for doc in _documents]
    metadatas = [{'source file': doc['filename']} for doc in _documents]
    with st.spinner('✨ Vectorizing documents...'):
        embeddings = OpenAIEmbeddings(openai_api_key=os.environ["OPENAI_API_KEY"])
        pinecone.init(
            api_key=os.environ["PINECONE_API_KEY"],  # find at app.pinecone.io
            environment=os.environ["PINECONE_API_ENV"]  # next to api key in console
        )
        pinecone.Index("dewey").delete(deleteAll='true')
        docsearch = Pinecone.from_texts(
            texts=texts,
            embedding=embeddings,
            metadatas=metadatas,
            index_name="dewey"
        )
        llm = OpenAI(temperature=0.5, openai_api_key=os.environ["OPENAI_API_KEY"])
        chain = load_qa_chain(llm, chain_type="stuff")
    temp.success('Texts successfully assimilated 😈')
    time.sleep(1)
    temp.empty()
    return docsearch, chain


# @st.cache_resource(show_spinner=False)
def answer(query, _docsearch, _chain):
    with st.spinner('📚 Researching...'):
        docs = _docsearch.similarity_search(query)
    with st.spinner('🧠 Synthesizing...'):
        response = _chain.run(input_documents=docs, question=query).strip()
    return docs, response
