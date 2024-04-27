import re
import aiofiles
import asyncio
from supabase import create_client
from langchain_text_splitters import RecursiveCharacterTextSplitter             
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores.supabase import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_openai import OpenAIEmbeddings, OpenAI,ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from data1 import standalone_question_process
import re
import xml.etree.ElementTree as ET
import requests
from pprint import pprint

openaiapikey = "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"
sbapikey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx6eHp1YXpzcHhqdGZ3ZXJvcWNnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDcyNTQ1OTYsImV4cCI6MjAyMjgzMDU5Nn0.BcbuKaBsdYcPta5GlVXQ8Wa9RSqFTtLDWAouG21Csfw'
sburl = 'https://lzxzuazspxjtfweroqcg.supabase.co'
supabase_client = create_client(sburl, sbapikey)

async def process_text_file(path):
    try:
        async with aiofiles.open(path, mode='r', encoding='utf-8') as file:
            text = await file.read()
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
            output = splitter.create_documents([text])
            return output  
    except Exception as err:
        print('Error reading file:', err)
        raise

async def main():
    llm1 = ChatOpenAI(model="gpt-4-0125-preview", temperature=0, openai_api_key =openaiapikey)
    file_path = '/Users/mohammadharis/Downloads/lion.txt'

    try:
        output = await process_text_file(file_path)                             
        
        SupabaseVectorStore.from_documents(
            output,
            OpenAIEmbeddings(openai_api_key=openaiapikey),
            client=supabase_client,
            table_name='documents'
        )
        
        question = "When does female lion first give birth?"

        prompt_1 = """For the following user query, you need to find out if it is best answered directly, or using one of the two available external RAG tools which are API connections to OpenFDA and PubMed."\n"
                                Your reply should contain no verbose but consist of only one word without quotes which is one of the 3 mentioned choices:"\n"
                                1. Answering directly: Your response should be: “<direct>" "\n"
                                2. Use of OpenFDA: Your response should be: “<openfda>" "\n"
                                3. Use of PubMed: Your response should be: “<pubmed>" "\n"
                                Here's the original user query: {question}
                               """    
        
        response_type_prompt = ChatPromptTemplate.from_template(prompt_1)        
        chain1 = ( response_type_prompt| llm1 | StrOutputParser())
        chain1_result = chain1.invoke({"question": question})
        print(chain1_result)
        if "<pubmed>" in chain1_result or "<openfda>" in chain1_result:
            prompt_2 = """  You are trying to automate a system that tries to help a user to operate the PubMed or OpenFDA database system. For a given user question, you should reply with a computed API request URL that best reflects the user intent. Do NOT include any verbose, answer ONLY with the computed API request URL
                            Examples for other cases to show the use of the API are: 
                            "Please generate a request API URL for pubmed id - 32607962"
                            Desired Response: https://pubmed.ncbi.nlm.nih.gov/32607962/
                            “find publications from 2022-2023 in the journal Nature related to zika virus”
                            Desired response: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=(%22Nature%22[Journal])+AND+%22zika+virus%22[Title/Abstract]+AND+(%222022/01/01%22[Date+-+Publication]+:%222023/12/31%22[Date+-+Publication])&retmax=100&usehistory=y
                            What API request URL to PubMed or OpenFda could best help to answer the following question: {question}. """
            
            response_type_prompt1 = ChatPromptTemplate.from_template(prompt_2)
            chain2 = (response_type_prompt1 | llm1 | StrOutputParser())
            chain2_result = chain2.invoke({"question":question})

            def is_xml_content(content):
                return content.strip().startswith("<") and content.strip().endswith(">")
            
            def extract_all_elements_from_xml(url):
                try:
                    response = requests.get(url)
                    if response.status_code == 200:
                        if is_xml_content(response.text) == True:
                            root = ET.fromstring(response.content)
                            elements= {}
                            for element in root.iter():
                                if element.tag == "IdList":
                                    id_list = [id_element.text.strip() for id_element in element.findall("Id")]
                                    if len(id_list) > 1:
                                        elements[element.tag] = id_list
                                    else:
                                        return elements
                                else:
                                    elements[element.tag] = element.text.strip() if element.text else None
                                    for key, value in element.attrib.items():
                                        elements[f"{element.tag}_attribute_{key}"] = value.strip() if value else None
                            return elements
                        else:
                            return None
                    else:
                        return None
                except Exception as e:
                    return None
                
            def extract_all_elements_from_json(url):
                try:
                    response = requests.get(url)
                    if response.status_code == 200:
                        json_data = response.json()
                        if json_data:  # Check if JSON data is not empty
                            elements = {}
                            extract_elements(json_data, elements)
                            return elements
                        else:
                            return None
                    else:
                        return None
                except Exception as e:
                    return None

            def extract_elements(data, elements, parent_key=""):
                if isinstance(data, dict):
                    for key, value in data.items():
                        new_key = f"{parent_key}_{key}" if parent_key else key
                        if isinstance(value, (dict, list)):
                            extract_elements(value, elements, new_key)
                        else:
                            elements[new_key] = value.strip() if isinstance(value, str) else value
                elif isinstance(data, list):
                    for i, item in enumerate(data):
                        new_key = f"{parent_key}_{i}" if parent_key else str(i)
                        if isinstance(item, (dict, list)):
                            extract_elements(item, elements, new_key)
                        else:
                            elements[new_key] = item.strip() if isinstance(item, str) else item
            
            url = chain2_result
            all_elements = extract_all_elements_from_xml(url)
            extracted_data = extract_all_elements_from_json(url)
            #print(all_elements)

            if all_elements or extracted_data:
                prompt_3 = """I issued the API requests and obtained the results either in {all_elements} or {extracted_data}. Please print all the elements in a new line along with its contents such that it is easily understood by the user"""   
            
                response_type_prompt2 = ChatPromptTemplate.from_template(prompt_3)
                chain3 = (response_type_prompt2 | llm1 | StrOutputParser())
                chain3_result = chain3.invoke({"all_elements":all_elements,"extracted_data": extracted_data })
                print(chain3_result)
            else:
                print(chain2_result)

        else:
            resp = standalone_question_process(question)
            pprint(resp)


    except Exception as err:
        print('Error in main function:', err)

asyncio.run(main())
