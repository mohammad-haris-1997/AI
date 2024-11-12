import logging
import io
import openpyxl
import os
import streamlit as st
import tempfile
from dotenv import load_dotenv
from supabase import create_client
from langchain_community.document_loaders import Docx2txtLoader
from langchain.text_splitter import TextSplitter, RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores.supabase import SupabaseVectorStore
from prod_llm_excel_similarity import standalone_question_process
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import List, Optional

load_dotenv()
openaiapikey = os.getenv("OPENAI_API_KEY")
sbapikey = os.getenv("SUPABASE_API_KEY")                                                                                                    
sburl = 'https://lzxzuazspxjtfweroqcg.supabase.co'
supabase_client = create_client(sburl, sbapikey)

llm = ChatOpenAI(model="gpt-4-turbo-2024-04-09", temperature=0.05, openai_api_key=openaiapikey)
embeddings = OpenAIEmbeddings(openai_api_key=openaiapikey, model="text-embedding-ada-002")

vectorstore = SupabaseVectorStore(embedding=embeddings, client=supabase_client, table_name='documents', query_name='match_documents')
retriever = vectorstore.as_retriever()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def call_openai_api():
    pass

def load_and_split(file_bytes: io.BytesIO, text_splitter: Optional[TextSplitter] = None) -> List[Document]:
    # Create a temporary file to store the Word document
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
        temp_file.write(file_bytes.read())
        temp_path = temp_file.name 

    loader = Docx2txtLoader(temp_path)
    documents = loader.load()

    if text_splitter is None:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=250)

    split_docs = text_splitter.split_documents(documents)

    os.remove(temp_path)
    
    return split_docs

def process_documents(all_outputs):
    output_lines = [f"Document {i+1}: {doc.page_content}" for i, doc in enumerate(all_outputs) if hasattr(doc, 'page_content')]
    return "\n".join(output_lines)

def process_excel_requirements(file_bytes: io.BytesIO, sheet_name):
    try:
        workbook = openpyxl.load_workbook(file_bytes)
        sheet = workbook[sheet_name]

        for row in range(7, sheet.max_row + 1):
            question = sheet[f"B{row}"].value
            if question:
                citation, synopsis, citation_2, synopsis_2, str_similarity_1, str_similarity_2 = standalone_question_process(question)
                sheet[f"D{row}"] = citation
                sheet[f"E{row}"] = str_similarity_1
                sheet[f"F{row}"] = synopsis
                sheet[f"G{row}"] = citation_2
                sheet[f"H{row}"] = str_similarity_2
                sheet[f"I{row}"] = synopsis_2

        output_bytes = io.BytesIO()
        workbook.save(output_bytes)
        output_bytes.seek(0)
        return output_bytes
    except Exception as e:
        logging.error(f"Error processing Excel file: {e}")

def check_if_doc_exists_in_vectorstore(doc_name):
    try:
        results = supabase_client.table("documents").select("*").eq("metadata->>source", doc_name).execute()
        return len(results.data) > 0
    except Exception as e:
        logging.error(f"Error checking document in vector store: {e}")
        return False

def clear_vectorstore_documents():
    try:
        supabase_client.table("documents").delete().lt('id', 'ffffffff-ffff-ffff-ffff-ffffffffffff').execute()
    except Exception as e:
        logging.error(f"Error clearing documents from vector store: {e}")

def main(file_bytes, sheet_name, word_doc_bytes=None):
    try:
        if word_doc_bytes:
            all_outputs = load_and_split(word_doc_bytes)
            doc_exists = check_if_doc_exists_in_vectorstore(word_doc_bytes)
            if not doc_exists:
                clear_vectorstore_documents()
                SupabaseVectorStore.from_documents(
                    all_outputs,
                    OpenAIEmbeddings(openai_api_key=openaiapikey),
                    client=supabase_client,
                    table_name='documents',
                    query_name="match_documents",
                    chunk_size=500
                )
            else:
                logging.info(f"Document {word_doc_bytes} is already stored in the vector store. Skipping storage.")
        data = process_excel_requirements(file_bytes, sheet_name)
        logging.info(f"Excel requirements processed successfully for file: {file_bytes}, sheet: {sheet_name}")
        return data
    except Exception as err:
        logging.error(f"Error in main function: {err}")


