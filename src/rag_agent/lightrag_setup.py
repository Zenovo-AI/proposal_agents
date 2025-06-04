"""
This module provides functionality for creating and configuring a Retrieval-Augmented Generation 
(RAG) instance using the LightRAG framework, with a focus on embedding functions and interacting 
with OpenAI's API for generating embeddings. The RAG setup involves creating a pipeline with 
embedding and LLM (Large Language Model) configurations for efficient information retrieval and 
question answering.

Key Features:
- Defines an embedding function using OpenAI's embedding API (`openai_embed`), which processes 
  a list of input texts and returns their corresponding embeddings.
- Uses the LightRAG framework to create an RAG instance for the purpose of document retrieval 
  and question answering. This includes configuring the RAG with embeddings and LLM models.
- Provides a `RAGFactory` class to instantiate and configure the RAG system, with shared embedding 
  configurations and handling pipeline initialization.
- The pipeline initialization is performed asynchronously to ensure efficient setup of storages 
  and pipeline status using `initialize_pipeline_status`.
- The `create_rag` method of `RAGFactory` creates the RAG instance, configures necessary parameters, 
  and initializes the pipeline.

Dependencies:
- `openai_embed`: A function to get text embeddings from OpenAI.
- `gpt_4o_complete`: A function from the LightRAG library to perform LLM-based completions.
- `LightRAG`: The core framework used for retrieval-augmented generation, enabling the RAG 
  pipeline for information retrieval and question answering.
- `initialize_pipeline_status`: A utility function for managing pipeline status and storage 
  initialization.

The module uses `asyncio` to handle the asynchronous initialization of the RAG pipeline and stores 
the embeddings with a maximum token size and specific dimension. The embeddings are generated using 
OpenAI's API, with the configuration managed through Streamlit's secrets storage.

Note:
- Ensure that the correct API keys (`OPENAI_API_KEY`, `OPENAI_API_BASE`) are available in 
  `st.secrets` for successful interaction with OpenAI services.
- This module is suitable for integrating LightRAG with OpenAI embeddings for advanced 
  document retrieval and answering systems, offering the flexibility to manage different 
  configurations and embedding models.
"""

import logging
import asyncio
import os
import numpy as np # type: ignore
from lightrag import LightRAG # type: ignore
from lightrag.kg.postgres_impl import PostgreSQLDB  # type: ignore
from lightrag.llm.openai import openai_embed, gpt_4o_complete # type: ignore
from lightrag.utils import EmbeddingFunc # type: ignore
from lightrag.kg.shared_storage import initialize_pipeline_status # type: ignore
from config.appconfig import settings as app_settings

# Embedding function using OpenAI
# def embedding_func(texts: list[str]) -> np.ndarray:
#     api_key = app_settings.openai_api_key
#     embeddings = openai_embed(
#         texts,
#         model="text-embedding-3-large",
#         api_key=api_key,
#         base_url = app_settings.openai_api_base
#     )
#     if embeddings is None:
#         logging.error("Received empty embeddings from API.")
#         return np.array([])
#     return embeddings

# class RAGFactory:
#     _shared_embedding = EmbeddingFunc(
#         embedding_dim=3072,
#         max_token_size=8192,
#         func=embedding_func
#     )

#     @classmethod
#     async def create_rag(cls, working_dir: str) -> LightRAG:
#         """Create a LightRAG instance with shared configuration"""
#         rag = LightRAG(
#             working_dir=working_dir,
#             addon_params={
#                 "insert_batch_size": 10
#             },
#             llm_model_func=gpt_4o_complete,
#             embedding_func=cls._shared_embedding
#         )

        # # Initialize storages and pipeline status (this must be async)
        # # asyncio.run(cls._initialize_storage_and_pipeline(rag))
        # await asyncio.create_task(cls._initialize_storage_and_pipeline(rag))

#         return rag
        
        # @staticmethod
        # async def _initialize_storage_and_pipeline(rag: LightRAG):
        #   """Async init for storages and pipeline status"""
        #   await rag.initialize_storages()
        #   await initialize_pipeline_status()


class RAGFactory:
    @classmethod
    async def create_rag(cls, config_path: str) -> LightRAG:
        logging.info("🚀 Starting RAGFactory.create_rag")
        # Load config from file
        # config = configparser.ConfigParser()
        db_config = {
             "database": app_settings.db_name,
              "user": app_settings.user,
              "password": app_settings.password,
              "host": app_settings.host,
              "port": app_settings.port_db
          }
        print("✅ DB Config:", db_config)
        logging.info("✅ DB Config: %s", db_config)

        postgres_db = PostgreSQLDB(config=db_config)
        await postgres_db.initdb()
        await postgres_db.check_tables()

        # Define embedding function
        embedding_func = EmbeddingFunc(
            embedding_dim=3072,
            max_token_size=8192,
            func=lambda texts: openai_embed(
                texts,
                model="text-embedding-3-large",
                api_key=app_settings.openai_api_key,
                base_url=app_settings.openai_api_base
            )
        )

        workspace_dir = app_settings.workspace
        os.makedirs(workspace_dir, exist_ok=True)
        print(f"✅ Working directory ensured at: {workspace_dir}")
        logging.info("✅ Working directory ensured at: %s", workspace_dir)
        print("⚙️ Initializing LightRAG with PostgreSQL storage...")
        logging.info("⚙️ Initializing LightRAG with PostgreSQL storage...")

        # Initialize LightRAG
        rag = LightRAG(
            working_dir=workspace_dir,
            addon_params={"insert_batch_size": 10},
            llm_model_func=gpt_4o_complete,
            embedding_func=embedding_func,
            kv_storage=app_settings.kv_storage,
            vector_storage=app_settings.vector_storage,
            graph_storage=app_settings.graph_storage,
            doc_status_storage=app_settings.doc_status_storage,
            db=postgres_db
        )

        await rag.initialize_storages()
        print("✅ RAG storage initialized")
        logging.info("✅ RAG storage initialized")
        logging.info("✅ Finished initializing LightRAG")
        return rag


