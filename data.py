import re
import requests
import urllib.parse
from langchain_community.vectorstores.supabase import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings, OpenAI,ChatOpenAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from supabase import create_client


# Determining OpenFda endpoint and further processing
def determine_endpoint(question):
    endpoint = None
    lower_question = question.lower()

    # Use regex to match patterns related to 'drug labels'
    if re.search(r'drug label(s?)', lower_question):
        endpoint = 'drug_label_search'
    elif re.search(r'food enforcement report(s?)', lower_question):
        endpoint = 'food_enforcement_reports'
    elif re.search(r'food adverse event(s?)', lower_question):
        endpoint = 'food_adverse_events'
    elif re.search(r'drug enforcement report(s?)', lower_question):
        endpoint = 'drug_enforcement_reports'
    else:
        return None
    print("Endpoint determined:", endpoint)
    return endpoint


def open_fda_question_process(question, endpoint):
    try:
        # Define openFDA API documentation
        openFDA_docs = {
            "API": {
                "title": "openFDA API",
                "description": "openFDA provides APIs to access FDA data on drugs, devices, and foods.",
                "endpoints": {
                    "drug_label_search": {
                        "description": "Search for drug labels",
                        "method": "GET",
                        "path": "/drug/label.json",
                        "parameters": [
                            {"name": "search", "type": "string", "description": "Search term"},
                            {"name": "limit", "type": "integer", "description": "Limit number of results"}
                        ]
                    },
                    "food_enforcement_reports": {
                        "description": "Search for food enforcement reports including recalls and safety alerts",
                        "method": "GET",
                        "path": "/food/enforcement.json",
                        "parameters": [
                            {"name": "search", "type": "string", "description": "Search term, such as a product name or reason for enforcement"},
                            {"name": "limit", "type": "integer", "description": "Limit number of results"}
                        ]
                    },
                    "food_adverse_events": {
                        "description": "Search for reports of adverse events related to food products (hypothetical endpoint)",
                        "method": "GET",
                        "path": "/food/event.json",
                        "parameters": [
                            {"name": "search", "type": "string", "description": "Search term, such as a specific food product or symptom"},
                            {"name": "limit", "type": "integer", "description": "Limit number of results"}
                        ]
                    },
                    "drug_enforcement_reports": {
                        "description": "Search for drug enforcement reports including recalls and safety alerts",
                        "method": "GET",
                        "path": "/drug/enforcement.json",
                        "parameters": [
                            {"name": "search", "type": "string", "description": "Search term, such as a product name or reason for enforcement"},
                            {"name": "limit", "type": "integer", "description": "Limit number of results"}
                        ]
                    }
                }
            }
        }

        openFDA_base_url = "https://api.fda.gov"
        openFDA_api_key = "Obdyv3449WDnJrGfCICdfWI1N8KkTDrFSULRD8yK"  # Replace with your openFDA API key
        headers = {"Authorization": f"Bearer {openFDA_api_key}"}
        # endpoint = determine_endpoint(question)
        search_match = re.search(r"'([^']+)'", question)  # Matches text within single quotes
        limit_match = re.search(r"return only (\d+)", question)
        search = search_match.group(1) if search_match else ""  # Default to empty string if no match
        limit = int(limit_match.group(1)) if limit_match else 5
        if not search:
            parameters = {"limit": limit}
        else:
            parameters = {"search": search, "limit": limit}
        url = f"{openFDA_base_url}{openFDA_docs['API']['endpoints'][endpoint]['path']}?{urllib.parse.urlencode(parameters)}"
        response = requests.get(url, headers=headers, verify = False)
        response.raise_for_status()  # Raise an error if response status code is not ok
        data = response.json()

        return data

    except Exception as error:
        print('Error processing openFDA API question:', error)
        raise error    



# Credentials
openaiapikey = "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"
sbapikey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx6eHp1YXpzcHhqdGZ3ZXJvcWNnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDcyNTQ1OTYsImV4cCI6MjAyMjgzMDU5Nn0.BcbuKaBsdYcPta5GlVXQ8Wa9RSqFTtLDWAouG21Csfw'
sburl = 'https://lzxzuazspxjtfweroqcg.supabase.co'
supabase_client = create_client(sburl, sbapikey)


# Processing standalone question, if the question asked is not based or triggers API's
def standalone_question_process(question):
    try:
        llm = ChatOpenAI(model="gpt-4", temperature=0, openai_api_key =openaiapikey)
        embeddings = OpenAIEmbeddings(openai_api_key=openaiapikey)
        vectorstore = SupabaseVectorStore(embedding=embeddings,client= supabase_client, table_name='documents', query_name='match_documents')
        retriever = vectorstore.as_retriever();
        standalonequestiontemplate = """ Given a question, convert it to a standalone question. question: {question} standalone question:"""
        standalone_question_prompt = ChatPromptTemplate.from_template(standalonequestiontemplate)

        answer_template = """You are a helpful bot please answer the questions based on context, otherwise answer by browsing through the internet but keep the answer precise, asking the user to confirm it once on their end. context: {context} question: {question} answer:"""
        answer_prompt = ChatPromptTemplate.from_template(answer_template)

        def combinedocuments(docs):
            if isinstance(docs, list):
                page_content = str()
                for i in docs:
                    page_content += i.page_content + "\n\n"
                return page_content
            else:
                return docs

        standalone_question_chain = (standalone_question_prompt | llm | StrOutputParser())
        retriever_chain = ( retriever | combinedocuments | llm | StrOutputParser() )

        answer_chain = (answer_prompt | llm | StrOutputParser())
        
        standalone_question_result = standalone_question_chain.invoke({"question": question})  # Use .run() method to execute the chain

        context = retriever_chain.invoke(standalone_question_result)  # Use .run() method to execute the chain

        final_input = {"context": context, "question": question}
        response = answer_chain.invoke(final_input)  # Use .run() method to execute the chain

        return response
        
    except Exception as err:
        print('Error processing standalone question:', err)
        raise err    
