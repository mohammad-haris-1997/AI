from langchain_community.vectorstores.supabase import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from supabase import create_client
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()
openaiapikey = os.getenv("OPENAI_API_KEY")
sbapikey = os.getenv("SUPABASE_API_KEY")
sburl = 'https://lzxzuazspxjtfweroqcg.supabase.co'
supabase_client = create_client(sburl, sbapikey)

llm = ChatOpenAI(model="gpt-4-turbo-2024-04-09", temperature=0.05, openai_api_key=openaiapikey)
embeddings = OpenAIEmbeddings(openai_api_key=openaiapikey)

# Initialize vector store for storing and retrieving past project data
vectorstore = SupabaseVectorStore(embedding=embeddings, client=supabase_client, table_name='documents', query_name='match_documents')

def cosine_similarity_1(question, matched_docs, embeddings):
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
                print(f"Document: {matched_docs[i].page_content[:100]}...")  # Short preview of the doc
                print(f"Cosine Similarity: {similarity_scores[-1]}\n")

            results = []
            for i in range(len(doc_texts)):
                doc_results = {
                'document_text': doc_texts[i],
                'similarity_score': similarity_scores[i]
                            }
                results.append(doc_results)
            return results

def get_llm_citation(all_elements):
    try:
        prompt_citation = """I did a similarity search and obtained the results in {all_elements}. Provide only the section number and citation related to the project requirement. """   
        response_type_prompt = ChatPromptTemplate.from_template(prompt_citation)
        chain_citation = (response_type_prompt | llm | StrOutputParser())    
        chain_citation_result = chain_citation.stream({"all_elements": all_elements})
        return chain_citation_result
    
    except Exception as err:
        print('Error processing citation:', err)
        raise err
    
def get_llm_synopsis(all_elements):
    try:
        prompt_synopsis = """I did a similarity search and obtained the results in {all_elements}. Provide a 50-word synopsis of the company's work related to the project requirement. """   
        response_type_prompt = ChatPromptTemplate.from_template(prompt_synopsis)
        chain_synopsis = (response_type_prompt | llm | StrOutputParser())    
        chain_synopsis_result = chain_synopsis.stream({"all_elements": all_elements})
        return chain_synopsis_result
    except Exception as err:
        print('Error processing synopsis:', err)
        raise err
    
def get_llm_citation_2(all_elements_2):
    try:
        prompt_citation_2 = """I did a similarity search and obtained the results in {all_elements_2}. Provide only the section number and citation related to the project requirement."""   
        response_type_prompt = ChatPromptTemplate.from_template(prompt_citation_2)
        chain_citation = (response_type_prompt | llm | StrOutputParser())    
        chain_citation_result = chain_citation.stream({"all_elements_2": all_elements_2})
        return chain_citation_result
    
    except Exception as err:
        print('Error processing citation:', err)
        raise err
    
def get_llm_synopsis_2(all_elements_2):
    try:
        prompt_synopsis_2 = """I did a similarity search and obtained the results in {all_elements_2}. Provide a 50-word synopsis of the company's work related to the project requirement. """   
        response_type_prompt = ChatPromptTemplate.from_template(prompt_synopsis_2)
        chain_synopsis = (response_type_prompt | llm | StrOutputParser())    
        chain_synopsis_result = chain_synopsis.stream({"all_elements_2": all_elements_2})
        return chain_synopsis_result
    except Exception as err:
        print('Error processing synopsis:', err)
        raise err

def standalone_question_process(question):
    try:

        matched_docs = vectorstore.similarity_search(question)
        document = matched_docs[0]
        all_elements = document.page_content
        similarity = cosine_similarity_1(question,matched_docs,embeddings) 
        similarity_1 = round(similarity[0]['similarity_score'] * 100, 2) 
        similarity_2 = round(similarity[1]['similarity_score'] * 100, 2)     
        document_2 = matched_docs[1]
        all_elements_2 = document_2.page_content   
        str_similarity_1 = str(similarity_1)
        str_similarity_2 = str(similarity_2)
        citation_generator = get_llm_citation(all_elements)
        synopsis_generator = get_llm_synopsis(all_elements)
        citation_generator_2 = get_llm_citation_2(all_elements_2)
        synopsis_generator_2 = get_llm_synopsis_2(all_elements_2)
        citation = "".join([chunk for chunk in citation_generator])  # Join chunks into a full string
        synopsis = "".join([chunk for chunk in synopsis_generator])
        citation_2 = "".join([chunk for chunk in citation_generator_2])  # Join chunks into a full string
        synopsis_2 = "".join([chunk for chunk in synopsis_generator_2])
        return citation, synopsis, citation_2, synopsis_2, str_similarity_1, str_similarity_2

    except Exception as err:
        print('Error processing standalone question:', err)
        raise err
    
