from langchain_community.vectorstores.supabase import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings, OpenAI,ChatOpenAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from supabase import create_client


openaiapikey = "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"
sbapikey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx6eHp1YXpzcHhqdGZ3ZXJvcWNnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MDcyNTQ1OTYsImV4cCI6MjAyMjgzMDU5Nn0.BcbuKaBsdYcPta5GlVXQ8Wa9RSqFTtLDWAouG21Csfw'
sburl = 'https://lzxzuazspxjtfweroqcg.supabase.co'
supabase_client = create_client(sburl, sbapikey)



def standalone_question_process(question):
    try:
        llm = ChatOpenAI(model="gpt-4-0125-preview", temperature=0, openai_api_key =openaiapikey)
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

        def print_result(input_data):
            print("Intermediate result:", input_data)
            return input_data 
    
        standalone_question_chain = (standalone_question_prompt| llm | StrOutputParser())

        retriever_chain = (retriever| combinedocuments | llm |StrOutputParser())

        answer_chain = (answer_prompt | llm | StrOutputParser())
        
        standalone_question_result = standalone_question_chain.invoke({"question": question})  
        
        context = retriever_chain.invoke(standalone_question_result)  

        final_input = {"context": context, "question": question}
        response = answer_chain.invoke(final_input) 
        # print(response)                         

        prompt_5 = """ Here is the answer intended for the question: {question}. Answer generated was: {response}. Please Check the answer carefully for correctness, style, and efficiency, and give constructive criticism for how to improve it."""

        response_type_prompt4 = ChatPromptTemplate.from_template(prompt_5)
        chain5 = (response_type_prompt4 | llm | StrOutputParser())
        chain5_result = chain5.invoke({"question":question, "response":response})
        
        prompt_6 = """Based on the previous given answer: {response} and criticism you have provided :{chain5_result}. Please generate the response again."""
        response_type_prompt5 = ChatPromptTemplate.from_template(prompt_6)
        chain6 = (response_type_prompt5| llm | StrOutputParser())
        chain6_result = chain6.invoke({"response":response, "chain5_result":chain5_result})

        return chain6_result
        
    except Exception as err:
        print('Error processing standalone question:', err)
        raise err    
