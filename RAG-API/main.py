from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import oracledb
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.sql_database import SQLDatabase
from langchain.chains.sql_database.prompt import PROMPT
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.prompts import PromptTemplate
import logging
import os

app = FastAPI()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Oracle DB configuration(EDIT THIS AREA!!!)
db_uri = "oracle+oracledb://C##EMRES:MyPassword123@oracle-xe:1521/XE"
db = SQLDatabase.from_uri(db_uri)

# LLM setup
llm = ChatOpenAI(model_name="gpt-4", temperature=0)

# Create embeddings model
embeddings = OpenAIEmbeddings()

# Initialize toolkit and agent
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True
)

# Generate schema information for embedding
def get_schema_information():
    """Fetch schema information from the database for RAG context."""
    try:
        schema_info = db.get_table_info()
        sample_data = []
        
        # Get sample data from tables for better context
        for table in db.get_usable_table_names():
            try:
                sample_query = f"SELECT * FROM {table} WHERE ROWNUM <= 3"
                sample_result = db.run(sample_query)
                sample_data.append(f"Sample data from {table}:\n{sample_result}")
            except Exception as e:
                logger.warning(f"Could not get sample data for table {table}: {e}")
        
        # Combine schema and sample data
        return schema_info + "\n\n" + "\n\n".join(sample_data)
    except Exception as e:
        logger.error(f"Error getting schema information: {e}")
        return "Schema information unavailable."

# Create vector store from schema information
def initialize_vector_store():
    """Initialize the vector store with schema information."""
    try:
        schema_info = get_schema_information()
        # Split schema info into chunks for better retrieval
        chunks = [schema_info[i:i+1000] for i in range(0, len(schema_info), 1000)]
        
        # Create vector store
        vector_store = FAISS.from_texts(chunks, embeddings)
        logger.info("Vector store initialized successfully")
        return vector_store
    except Exception as e:
        logger.error(f"Error initializing vector store: {e}")
        raise

# Initialize the vector store
vector_store = initialize_vector_store()

# Create the RAG retrieval chain
retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)

# Custom RAG prompt template
rag_template = """
You are a helpful assistant that answers questions about a database.

Context from the database schema:
{context}

User question: {question}

First, think about the tables and columns that might be relevant to this question.
Then, formulate an SQL query to answer this question based on the schema information provided.
Finally, provide a concise and helpful answer.

Answer:
"""

RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=rag_template
)

class Query(BaseModel):
    question: str

@app.post("/query")
def query_database(query: Query):
    try:
        question = query.question
        logger.info(f"Received question: {question}")
        
        # Get relevant context from the vector store
        docs = retriever.get_relevant_documents(question)
        context = "\n".join([doc.page_content for doc in docs])
        
        logger.info(f"Retrieved context length: {len(context)}")
        
        # First approach: Use RAG context to guide the SQL agent
        augmented_question = f"""
            Answer the following question: {question}
            
            Here is some context about the database schema that might be helpful:
            {context}
            
            Use the database to find the answer.
        """
        
        result = agent.run(augmented_question)
        
        logger.info(f"Agent result: {result}")
        
        return {"response": result}
    
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "rag-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)