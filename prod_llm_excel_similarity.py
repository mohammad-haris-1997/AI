from langchain_community.vectorstores.supabase import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from supabase import create_client
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
from dotenv import load_dotenv
import logging

load_dotenv()
openaiapikey = os.getenv("OPENAI_API_KEY")
sbapikey = os.getenv("SUPABASE_API_KEY")
sburl = 'https://lzxzuazspxjtfweroqcg.supabase.co'
supabase_client = create_client(sburl, sbapikey)

if not openaiapikey: 
    logging.error("OpenAI API key is missing in the environment variable. Please set.")
    raise ValueError("Missing OpenAI API Key.")

if not sbapikey:
    logging.error("Missing supabase API Key in the environment variable. Please set")
    raise ValueError("Missing Supabase API Key.")

try: 
    supabase_client = create_client(sburl, sbapikey)
    llm = ChatOpenAI(model="gpt-4-turbo-2024-04-09", temperature=0.05, openai_api_key=openaiapikey)
    embeddings = OpenAIEmbeddings(openai_api_key=openaiapikey)
    vectorstore = SupabaseVectorStore(embedding=embeddings, client=supabase_client, table_name='documents', query_name='match_documents')
    logging.info("Clients and models initialized successfully.")
except Exception as e:
    logging.error("Error initializing models or clients: %s", e)
    raise


def cosine_similarity_1(question, matched_docs, embeddings):
        try:
            logging.info("Starting cosine similarity calculation.")    
            embed_query = embeddings.embed_query(question)
            doc_embeddings = []
            similarity_scores = []
            doc_texts = []
            for doc in matched_docs:
                document_text = doc.page_content
                embedding = embeddings.embed_documents([document_text]) 
                doc_embeddings.append(embedding[0]) 
                doc_texts.append(document_text) 
            doc_embeddings = np.array(doc_embeddings)
            embed_query = np.array(embed_query).reshape(1, -1)
            for i, doc_embedding in enumerate(doc_embeddings):
                similarity_score = cosine_similarity(embed_query, np.array(doc_embedding).reshape(1, -1))
                similarity_scores.append(similarity_score[0][0])
                logging.info(f"Document: {matched_docs[i].page_content[:100]}...")  # Short preview of the doc
                logging.info(f"Cosine Similarity: {similarity_scores[-1]}\n")

            results = []
            for i in range(len(doc_texts)):
                doc_results = {
                'document_text': doc_texts[i],
                'similarity_score': similarity_scores[i]
                            }
                results.append(doc_results)
            return results
        except Exception as err:
            logging.error("Error during cosine similarity calculation: %s", err)
        raise

def get_llm_response(prompt_template, all_elements = None, all_elements_2 = None):
    try:
            response_type_prompt = ChatPromptTemplate.from_template(prompt_template)
            chain = (response_type_prompt | llm | StrOutputParser())
            logging.info("Fetching LLM response.")
            return chain.stream({"all_elements": all_elements,"all_elements_2":all_elements_2})
        
    except Exception as err:
        logging.error("Error generating LLM response: %s", err)
        raise

def standalone_question_process(question):
    try:
        logging.info(f"Processing question: {question}")
        matched_docs = vectorstore.similarity_search(question)
        if not matched_docs or len(matched_docs)<2:
            logging.warning("Documents retrieved via similarity search is less than two.")
            return None
        document = matched_docs[0]
        all_elements = document.page_content
        similarity = cosine_similarity_1(question,matched_docs,embeddings) 
        similarity_1 = round(similarity[0]['similarity_score'] * 100, 2) 
        similarity_2 = round(similarity[1]['similarity_score'] * 100, 2)     
        document_2 = matched_docs[1]
        all_elements_2 = document_2.page_content   
        str_similarity_1 = str(similarity_1)
        str_similarity_2 = str(similarity_2)
        citation_generator = get_llm_response("""I did a similarity search and obtained the results in {all_elements}. Provide only the section number and citation related to the project requirement. """,all_elements,None)
        synopsis_generator = get_llm_response("""I did a similarity search and obtained the results in {all_elements}. Provide a 50-word synopsis of the company's work related to the project requirement. """,all_elements,None)
        citation_generator_2 = get_llm_response("""I did a similarity search and obtained the results in {all_elements_2}. Provide only the section number and citation related to the project requirement.""",None,all_elements_2)
        synopsis_generator_2 = get_llm_response("""I did a similarity search and obtained the results in {all_elements_2}. Provide a 50-word synopsis of the company's work related to the project requirement. """,None,all_elements_2)
        citation = "".join([chunk for chunk in citation_generator])  # Join chunks into a full string
        synopsis = "".join([chunk for chunk in synopsis_generator])
        citation_2 = "".join([chunk for chunk in citation_generator_2])  
        synopsis_2 = "".join([chunk for chunk in synopsis_generator_2])
        logging.info(f"Processed question successfully: {question}")
        return citation, synopsis, citation_2, synopsis_2, str_similarity_1, str_similarity_2

    except Exception as err:
        logging.error('Error processing standalone question: %s', err)
        raise 
