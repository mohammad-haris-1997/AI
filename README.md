
# Large Language Models for Retrieval and Understanding of Complex Data (AI-Based Knowledge Retrieval System)

This project aims to build an Artificial Intelligence (AI) and Large Language Model (LLM) system that can retrieve complex and dynamic biomedical data from external sources such as databases and APIs like OpenFDA and PubMed. Efficient biomedical data retrieval is important for healthcare and scientific research. This project aims to address the challenges of data retrieval in the Biomedical sector. Data retrieval within this sector is often characterized by its complex, dynamic, and constantly changing nature. The LLM system will leverage Natural Language Query Processing (NLQP), Retrieval Augmentation Generation (RAG) and LLM models such as GPT-4 in order simplify user interactions as well as streamline and simplify the data retrieval process. The system provides an intuitive chatbot interface for users to input their questions using everyday human language.


<img width="1055" alt="Screenshot 2024-04-28 at 9 52 31 PM" src="https://github.com/mohammad-haris-1997/Capstone/assets/163910277/d0f8da57-78e3-47f4-b02e-7a13e35bee7d">



## Acknowledgements

 - DAEN 690 - 008: Data Analytics Engineering Project
 - Professor: Isaac Gang
## Authors
**Team KnowledgeBlend AI:**
* Nafisa Ahmed (nahmed@gmu.edu)
* Jaswanth Erusu (jerusu@gmu.edu)
* Eshwari Gone (egone@gmu.edu)
* Mohammad Haris (m2@gmu.edu)
* Rithwik Reddy Nathi (rnathi@gmu.edu)
* Gayasri Subburayalu (gsubbura@gmu.edu)



## Content

* **main.py** - The code in the main.py file uses a prompt that asks the LLM to determine the route it will take based on the user's question. The possible routes in our case would be: An API call or calling an external source using a retriever based on the pre-trained knowledge that it possesses. The API call in our case would be either PubMed or OpenFDA. The external source file could be any file/documentation/ schema from which we need an answer or provide context to the LLM to generate a relevant answer. So, prompt 1 asks LLM to print the route. If the route is an API call (PubMed or OpenFDA), then prompt 2 would get triggered. In prompt 2 we are directing the LLM to generate an API URL for PubMed/ OpenFDA by providing the format for the desired URL response. Once the URL is generated, the answer is mostly either in JSON format or XML format. Therefore, we are using a JSON/XML parser to extract the elements and print them in a more readable format.  
* **data.py** - If the route chosen by the LLM is direct i.e. the user’s question is not related to OpenFDA or PubMed, then the standalone question function is triggered. In this function, the user’s question is first converted into a standalone question, making the question very clear, concise and to the point. Next, a retriever pipeline is created that has access to the vector database (Supabase), which is pgvector in our case, so that relevant context can be retrieved from the database. The data file stored in the database would be a text file and can vary based on each use case. This is known as the RAG framework. Lastly, the answer chain is used to get an answer from the LLM, by providing the user’s question and the context retrieved by the retriever as the input. Once we have the response, we ask the LLM in prompt 5 to criticize its own answer. Once criticized, in prompt 6, we ask the LLM to generate a more accurate and reliable response by considering the initial response and the criticism generated through prompt 5.

## How to run the code/system

* Ensure Python 3.11.5 or above is installed.
* Install aiofiles package (pip install aiofiles).
* Install supabase package (pip install supabase).
    * Generate Supabase API key and supabase url by going to the supabase website.
* Generate OpenAI API key.
* Install lanchain_text_splitters (pip install langchain_text_splitters).
* Install langchain_Community (pip install langchain_sommunity)
* Install langchain_openai (pip install langchain_openai).
* Run the below SQL query in the Supabase SQL editor tab:

-- Enable the pgvector extension to work with embedding vectors 
create extension if not exists vector; 
DROP FUNCTION IF EXISTS match_documents(vector, int, jsonb);

-- Create a table to store your documents 
create table 
documents ( 
id uuid DEFAULT uuid_generate_v4() primary key, 
content text, -- corresponds to Document.pageContent 
metadata jsonb, -- corresponds to Document.metadata 
embedding vector (1536) -- 1536 works for OpenAI embeddings, change as needed 
); 

-- Create a function to search for documents 
create function match_documents ( 
query_embedding vector (1536), 
match_count int DEFAULT null, 
filter jsonb default '{}' 
) returns table ( 
id uuid, 
content text, 
metadata jsonb, 
similarity float 
) language plpgsql as $$ 
#variable_conflict use_column 
begin 
return query 
select 
id, 
content, 
metadata, 
1 - (documents.embedding <=> query_embedding) as similarity 
from documents 
where metadata @> filter 
order by documents.embedding <=> query_embedding; 
end; 
$$; 
create or replace function delete_documents_with_same_content(p_content text) 
returns void as $$ 
begin 
delete from documents where content = p_content; 
end; 
$$ language plpgsql;
* Name the SQL script in Supabase as match_documents.
    * After running the script in Supabase, a table will be created in the table editor column.
* Once the query is run, the document content should get stored in the table in chunks.

