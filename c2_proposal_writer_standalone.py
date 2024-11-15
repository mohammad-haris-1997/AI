from langchain_community.vectorstores.supabase import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings,ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from supabase import create_client
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.retrievers import ContextualCompressionRetriever
import os
from dotenv import load_dotenv
 
load_dotenv()
openaiapikey = os.getenv("OPENAI_API_KEY")
sbapikey = os.getenv("SUPABASE_API_KEY")  
sburl = 'https://lzxzuazspxjtfweroqcg.supabase.co'
supabase_client = create_client(sburl, sbapikey)

llm = ChatOpenAI(model="chatgpt-4o-latest", temperature=0.15, openai_api_key =openaiapikey)
embeddings = OpenAIEmbeddings(openai_api_key=openaiapikey)
vectorstore = SupabaseVectorStore(embedding=embeddings,client= supabase_client, table_name='proposal_doc', query_name='proposal_documents')
retriever = vectorstore.as_retriever();

standalonequestiontemplate = """ Given a question, convert it to a standalone question. question: {question} standalone question:"""
standalone_question_prompt = ChatPromptTemplate.from_template(standalonequestiontemplate)

answer_template = """ You are an intelligent chatbot that is an excellent proposal writer.

                            Constraints:
                            - Think step by step.
                            - Answer by using the {context}
                            - Reflect on your answer, and if you think you are hallucinating, repeat this answer.
                            - In your response, do not mention anything about the technical issues or errors you are facing 

                            Question: {question}?
                            """
        

answer_prompt = ChatPromptTemplate.from_template(answer_template)

def combinedocuments(docs):
    if isinstance(docs, list):
        return "\n\n".join(doc.page_content for doc in docs)
    return docs


def print_result(input_data):
    print("Intermediate result:", input_data)
    return input_data 

def standalone_question_process(question):
    try:
        compressor = LLMChainExtractor.from_llm(llm)
        compression_retriever = ContextualCompressionRetriever(base_compressor=compressor, base_retriever=retriever)

        standalone_question_chain = (standalone_question_prompt| llm | StrOutputParser())

        answer_chain = (answer_prompt | llm | StrOutputParser())
        standalone_question_result = standalone_question_chain.invoke({"question": question})
        compressed_docs = compression_retriever.invoke(standalone_question_result)  
        context = combinedocuments(compressed_docs)
        final_input = {"context": context, "question": question}
        response = answer_chain.stream(final_input)  
        return response           
        
    except Exception as err:
        print('Error processing standalone question:', err)
        raise err    
