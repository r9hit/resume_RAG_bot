import os 
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader

from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings,
)
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

load_dotenv()

print("Loading Resume PDF file...")

loader = PyPDFLoader("rohit_resume.pdf")

doc =  loader.load()

# print(doc[0].page_content)

print("Chuncking PDF(resume) file...")

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, 
    chunk_overlap=50
)

chunks = text_splitter.split_documents(doc)

# print(chunks[0].page_content)
                     

# for i, chunk in enumerate(chunks):
#     print(f"\n{'='*50}")
#     print(f"Chunk {i+1}")
#     print(chunk.page_content)

print("Creating Vector Database...")

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001"
)

vector_db = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db",
)

# creating a retriever to fetch relevant chunks from the vector database based on the user's question

retriever = vector_db.as_retriever(search_kwargs={"k": 2})


# prompt template to format the retrieved context and the user's question for the LLM

template = """Use the following pieces of retrieved context to answer the question. 
If you don't know the answer, just say that you don't know. 
Use three sentences maximum and keep the answer concise.

Context: {context}

Question: {question}

Answer:

"""

prompt = PromptTemplate.from_template(template)

# Initializing the LLM and Constructing the RAG Chain

llm = ChatGoogleGenerativeAI(
    model="models/gemini-3.5-flash",
    temperature=0
)


# Helper function to stitch retrieved chunks into a single text block

def format_docs(docs):
    return "\n\n".join([doc.page_content for doc in docs])



# Here Connecting everything together using LangChain Expression Language (LCEL)

rag_chain = (
    {
        "context": retriever | format_docs, 
        "question" : RunnablePassthrough(),
    }
    | prompt
    | llm
)

# Invoking the Chain with a Question

user_question = "What is the name of the person in the resume?"
print(f"\n Question: {user_question}")

response = rag_chain.invoke(user_question)



# CleanING up the output if Gemini returns a list of content blocks
if isinstance(response.content, list):
    clean_answer = response.content[0]['text']
else:
    clean_answer = response.content
    


print(f"Answer: {clean_answer}")


while True:
    question = input("\nAsk a question (type 'exit' to quit): ")

    if question.lower() == "exit":
        break

    response = rag_chain.invoke(question)

    if isinstance(response.content, list):
        answer = response.content[0]["text"]
    else:
        answer = response.content

    print("\nAnswer:", answer)