from langchain_text_splitters import RecursiveCharacterTextSplitter
from supabase import create_client
from data import determine_endpoint, open_fda_question_process, standalone_question_process
from langchain_community.vectorstores.supabase import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings, OpenAI,ChatOpenAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
# from langchain_core.runnables import RunnableSequence, RunnablePassthrough
# from langchain.chains import create_structured_output_runnable
import aiofiles
import asyncio

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
            return output  # Return the processed output
    except Exception as err:
        print('Error reading file:', err)
        raise

        
    except Exception as err:
        print('Error processing standalone question:', err)
        raise err

async def main():
    file_path = '/Users/mohammadharis/Downloads/sample.txt'

    try:
        output = await process_text_file(file_path)
        
        SupabaseVectorStore.from_documents(
            output,
            OpenAIEmbeddings(openai_api_key=openaiapikey),
            client=supabase_client,
            table_name='documents'
        )
        
        question = 'who is rafel nadal?'

        endpoint = determine_endpoint(question)
        from pprint import pprint
        if endpoint:
            pprint("From Endpoint")
            question_response = open_fda_question_process(question, endpoint)
            pprint(question_response)
        else:
            pprint("From document / LLM")
            resp = standalone_question_process(question)
            pprint(resp)

    except Exception as err:
        print('Error in main function:', err)

asyncio.run(main())
