## Oracle RAG SQL API

This project implements a FastAPI application that allows users to query an Oracle database using natural language questions. It leverages Retrieval-Augmented Generation (RAG) with Langchain, OpenAI's GPT-4 model, and a FAISS vector store to understand the database schema and generate appropriate SQL queries.

### Features

* **Natural Language Querying:** Ask questions about your Oracle database in plain English.
* **RAG Implementation:** Uses database schema information stored in a FAISS vector store to provide context to the language model, improving SQL query generation accuracy.
* **Langchain SQL Agent:** Utilizes Langchain's SQLDatabaseToolkit and create\_sql\_agent for interacting with the Oracle database.
* **FastAPI Backend:** Provides a simple and efficient API endpoint (`/query`) for submitting questions.
* **Dockerized:** Easy setup and deployment using Docker and Docker Compose[cite: 1].

### Technologies Used

* Python
* FastAPI
* Langchain
* OpenAI (GPT-4)
* Oracle Database [cite: 1]
* FAISS (for vector storage)
* Docker [cite: 1]
* oracledb
* Uvicorn

### Setup and Installation

1.  **Prerequisites:**
    * Docker and Docker Compose installed.
    * An running Oracle database instance accessible on the network.
    * An OpenAI API key.

2.  **Configure Environment Variables:**
    * Create a `.env` file in the project root or set the environment variables directly in the `docker-compose.yaml` file[cite: 1]:
        * `ORACLE_USER`: Your Oracle database username[cite: 1].
        * `ORACLE_PASSWORD`: Your Oracle database password[cite: 1].
        * `ORACLE_DSN`: Your Oracle database connection string (e.g., `your_oracle_host:1521/YourServiceName`)[cite: 1]. Make sure this matches the service name/SID and host accessible from the Docker container. The example uses `oracle-xe/XE` assuming an external network setup[cite: 1].
        * `OPENAI_API_KEY`: Your OpenAI API key[cite: 1].

3.  **Configure Docker Network:**
    * The `docker-compose.yaml` assumes an external Docker network named `oracle-network` exists, which the Oracle database container is also connected to[cite: 1]. You might need to create it (`docker network create oracle-network`) or adjust the network configuration based on your setup.

4.  **Build and Run the Container:**
    ```bash
    docker-compose up --build -d
    ```

### Usage

* Send a POST request to the `/query` endpoint with a JSON payload containing the question.
    * **URL:** `http://localhost:8001/query` (or your mapped host/port)
    * **Method:** POST
    * **Body:**
        ```json
        {
          "question": "Your natural language question about the database"
        }
        ```
* **Example using curl:**
    ```bash
    curl -X POST "http://localhost:8001/query" \
         -H "Content-Type: application/json" \
         -d '{"question": "How many customers are there?"}'
    ```

* The API will return a JSON response containing the answer derived from the database.

### Health Check

* You can check the health of the API by sending a GET request to the `/health` endpoint:
    ```bash
    curl http://localhost:8001/health
    ```
    * Expected Response: `{"status":"healthy","service":"rag-api"}`

### How it Works

1.  When the application starts, it connects to the Oracle database.
2.  It fetches the database schema information (table names, columns, types) and sample data.
3.  This schema information is chunked, embedded using OpenAI embeddings, and stored in a FAISS vector store in memory.
4.  When a user submits a question via the `/query` endpoint:
    * The question is used to retrieve relevant schema chunks (context) from the FAISS vector store.
    * The original question and the retrieved context are passed to the Langchain SQL agent.
    * The agent, using the LLM (GPT-4) and the provided context, formulates an SQL query.
    * The agent executes the SQL query against the Oracle database.
    * The agent processes the query result and returns a natural language answer.

### Requirements

See `requirements.txt` for Python package dependencies.
