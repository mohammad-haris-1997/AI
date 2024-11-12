from supabase import create_client
from langchain_text_splitters import RecursiveCharacterTextSplitter             
from langchain_openai import ChatOpenAI
from docx import Document
from langchain_community.document_loaders import Docx2txtLoader
from typing import List, Optional
from langchain.text_splitter import TextSplitter, RecursiveCharacterTextSplitter
from langchain.schema import Document
import os
from dotenv import load_dotenv
from langchain_community.vectorstores.supabase import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from llm_excel_similarity import standalone_question_process
import openpyxl

load_dotenv()
openaiapikey = os.getenv("OPENAI_API_KEY")
sbapikey = os.getenv("SUPABASE_API_KEY")
sburl = 'https://lzxzuazspxjtfweroqcg.supabase.co'
supabase_client = create_client(sburl, sbapikey)

llm = ChatOpenAI(model="gpt-4-turbo-2024-04-09", temperature=0.05, openai_api_key=openaiapikey)
embeddings = OpenAIEmbeddings(openai_api_key=openaiapikey, model="text-embedding-ada-002")

# Initialize vector store for storing and retrieving past project data
vectorstore = SupabaseVectorStore(embedding=embeddings, client=supabase_client, table_name='documents', query_name='match_documents')

# Initialize retriever for searching past documents
retriever = vectorstore.as_retriever()

load_dotenv()
LANGCHAIN_API_KEY= os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_ENDPOINT = "https://api.smith.langchain.com"
LANGCHAIN_PROJECT = "langsmith"


def load_and_split(file_paths: List[str], text_splitter: Optional[TextSplitter] = None) -> List[Document]:
    all_documents = []
    # Loop over each file and load its content
    for file_path in file_paths:
        loader = Docx2txtLoader(file_path)
        documents = loader.load()

        if text_splitter is None:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=250)

        split_docs = text_splitter.split_documents(documents)
        all_documents.extend(split_docs)  # Add split documents to all_documents list
    return all_documents

def process_documents(all_outputs):
    output_lines = []
    
    # Resetting index to ensure consistent numbering across different runs
    for i, doc in enumerate(all_outputs):
        if hasattr(doc, 'page_content'):
            output_lines.append(f"Document {i+1}: {doc.page_content}")  # Ensure numbering starts from 1
        else:
            output_lines.append(f"Document {i+1} does not have 'page_content' attribute or is not a Document.")
    
    output_string = "\n".join(output_lines)
    return output_string

def process_excel_requirements(file_path, sheet_name):
    # Load the workbook and sheet
    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook[sheet_name]

    # Loop through all rows, starting from row 2 (assuming row 1 is header)
    for row in range(7, sheet.max_row + 1):
        # Get the question from column B
        question = sheet[f"B{row}"].value
        
        if question:  # Only process if the question is not empty
            # Pass the question to the standalone_question_process to get citation and synopsis
            citation, synopsis, citation_2, synopsis_2, str_similarity_1, str_similarity_2 = standalone_question_process(question)
            
            sheet[f"D{row}"] = citation
            sheet[f"E{row}"] = str_similarity_1
            sheet[f"F{row}"] = synopsis
            sheet[f"G{row}"] = citation_2
            sheet[f"H{row}"] = str_similarity_2
            sheet[f"I{row}"] = synopsis_2

    # Save the workbook
    workbook.save(file_path)
    workbook.close()

def check_if_doc_exists_in_vectorstore(doc_path):
    results = supabase_client.table("documents").select("*").eq("metadata->>source", doc_path).execute()
    return len(results.data) > 0
    

def main(file_path, sheet_name, word_doc_path=None):
    try:
        if word_doc_path:
            # Process documents to load into the vectorstore (only do this once unless the document changes)
            all_outputs = load_and_split([word_doc_path])
            out = process_documents(all_outputs)
            doc_exists = check_if_doc_exists_in_vectorstore(word_doc_path)
            if not doc_exists:
                SupabaseVectorStore.from_documents(
                all_outputs,
                OpenAIEmbeddings(openai_api_key=openaiapikey),
                client=supabase_client,
                table_name='documents',
                query_name="match_documents",
                chunk_size = 500
            )
            else:
                print(f"Document {word_doc_path} is already stored in the vector store. Skipping storage.")
        process_excel_requirements(file_path, sheet_name)
        
    except Exception as err:
        print('Error in main function:', err)


