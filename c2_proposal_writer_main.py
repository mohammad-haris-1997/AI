from supabase import create_client
from langchain_text_splitters import RecursiveCharacterTextSplitter             
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from proposal_writer_standalone import standalone_question_process
from docx import Document
from langchain_community.document_loaders import Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from typing import List, Optional
from langchain.text_splitter import TextSplitter, RecursiveCharacterTextSplitter
from langchain.schema import Document
import os
from dotenv import load_dotenv
from langchain_community.vectorstores.supabase import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings,ChatOpenAI
import logging

load_dotenv()
openaiapikey = os.getenv("OPENAI_API_KEY")
sbapikey = os.getenv("SUPABASE_API_KEY")  
sburl = 'https://lzxzuazspxjtfweroqcg.supabase.co'
supabase_client = create_client(sburl, sbapikey)

load_dotenv()
LANGCHAIN_API_KEY= os.getenv("LANGCHAIN_API_KEY")  
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_ENDPOINT ="https://api.smith.langchain.com"
LANGCHAIN_PROJECT = "langsmith"


llm = ChatOpenAI(model="chatgpt-4o-latest", temperature=0, openai_api_key =openaiapikey)

def load_and_split(file_paths: List[str], text_splitter: Optional[TextSplitter] = None) -> List[Document]:
    all_documents = []

    for file_path in file_paths:
        loader = Docx2txtLoader(file_path)
        documents = loader.load()

        if text_splitter is None:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=100)

        split_docs = text_splitter.split_documents(documents)
        all_documents.extend(split_docs)
    return all_documents

def process_documents(all_outputs):
            output_lines = []  
    
            for i, doc in enumerate(all_outputs):
                if hasattr(doc, 'page_content'):
                    output_lines.append(f"Document {i+1}: {doc.page_content}")
                else:
                    output_lines.append(f"Document {i+1} does not have 'page_content' attribute or is not a Document.")
    
            output_string = "\n".join(output_lines)
            return output_string
def clear_vectorstore_documents():
    try:
        supabase_client.table("proposal_doc").delete().lt('id', 'ffffffff-ffff-ffff-ffff-ffffffffffff').execute()
    except Exception as e:
        logging.error(f"Error clearing documents from vector store: {e}")

def main(question):

    file_paths = ['/Users/mohammadharis/Downloads/AFJROTC_11 copy.docx',
                  '/Users/mohammadharis/Downloads/AETC Change Management_2 copy.docx',
                  '/Users/mohammadharis/Downloads/AETC Maintenance Next copy.docx',
                  '/Users/mohammadharis/Downloads/Air Force COOL Purchase Agents_EA18-M0002 copy 3 (1).docx',
                  '/Users/mohammadharis/Downloads/PPCitation-A10-EC130  CAT-CWD (August 2019) copy.docx',
                  '/Users/mohammadharis/Downloads/EC-130H A-10C copy.docx',
                  '/Users/mohammadharis/Downloads/AFCEC Past Performance copy.docx',
                  '/Users/mohammadharis/Downloads/Air Univeristy_Professional Military Education PME courses copy.docx',
                  '/Users/mohammadharis/Downloads/Air Force Air University Online copy.docx',
                  '/Users/mohammadharis/Downloads/USAF LIVE Project Summary copy.docx',
                  '/Users/mohammadharis/Downloads/C2_SCDC Support Services_Dev Ed Exp for USAF Squadron Commanders_FA330018RFQ0004 copy.docx',
                  '/Users/mohammadharis/Downloads/AETC_5 copy.docx']

    try:
                           
        all_outputs = load_and_split(file_paths)
        out = process_documents(all_outputs)

        clear_vectorstore_documents()
        SupabaseVectorStore.from_documents(
            all_outputs,
            OpenAIEmbeddings(openai_api_key=openaiapikey),
            client=supabase_client,
            table_name='proposal_doc'
        )

        # question = "Write a description about how C2 technologies have implemented change management process for the US Air Force in a detailed manner. Answer in 1000 words."
        resp = None
        chain1_result = None

        keywords = ["description", "proposal", "write", "summary","summarise","summarize","describe","propose","detail","detailed","details","outline","trace","sketch","illustrate","depict","elaborate","explain","emphasize","explaining","often","think"]

        if any(keyword in question.lower() for keyword in keywords):
             resp = standalone_question_process(question)
             if resp is not None: 
                return resp

        else: 
            prompt_1 = """For the following user query, you need to find out if the answer exists in the output {out} or not. Traverse through all the Documents, document 1, document 2 so on and so forth, 
                      If the answer exists respond precisely and to the point along with the contract title always for the user's reference along with it's contract description in one paragraph. Your answer should contain no verbose.
                      Here's the original user query: {question} and output {out} for you to refer 
                    """    
          
            response_type_prompt = ChatPromptTemplate.from_template(prompt_1)        
            chain1 = ( response_type_prompt| llm | StrOutputParser())
            chain1_result = chain1.stream(input = {"question": question,"out": out})
            return chain1_result
    
        prompt_3 = """I have received a response in {chain1_result}. Please pretty print all the contents such that it is easily understood by the user. Remove all the #,**, -. Only provide the text and whatever os necessary like numbers."""   
        
        response_type_prompt2 = ChatPromptTemplate.from_template(prompt_3)
        chain3 = (response_type_prompt2 | llm | StrOutputParser())
        chain3_result = chain3.stream({"chain1_result":chain1_result})
        return chain3_result

    except Exception as err:
        print('Error in main function:', err)

 

