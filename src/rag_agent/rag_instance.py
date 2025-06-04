# from dotenv import load_dotenv  # type: ignore
# import asyncio
# from lightrag import LightRAG
# from lightrag.utils import EmbeddingFunc
# from lightrag.llm.openai import gpt_4o_complete, openai_embed
# from lightrag.kg.shared_storage import initialize_pipeline_status
# from config.appconfig import settings as app_settings
# import os

# # Load environment variables from .env file
# load_dotenv()

# class RAGManager:
#     _rag_instance: LightRAG = None

#     @classmethod
#     async def init_rag(cls):
#         if cls._rag_instance is None:
#             workspace_dir = app_settings.workspace
#             os.makedirs(workspace_dir, exist_ok=True)

#             rag = LightRAG(
#                 working_dir=workspace_dir,
#                 llm_model_func=gpt_4o_complete,
#                 llm_model_name="gpt-4o",
#                 llm_model_max_async=2,
#                 llm_model_max_token_size=128000,
#                 enable_llm_cache_for_entity_extract=True,
#                 embedding_func=EmbeddingFunc(
#                     embedding_dim=3072,
#                     max_token_size=8192,
#                     func=lambda texts: openai_embed(
#                         texts,
#                         model="text-embedding-3-large",
#                         api_key=app_settings.openai_api_key,
#                         base_url=app_settings.openai_api_base
#                     ),
#                 ),
#                 kv_storage="PGKVStorage",
#                 doc_status_storage="PGDocStatusStorage",
#                 graph_storage="PGGraphStorage",
#                 vector_storage="PGVectorStorage",
#                 auto_manage_storages_states=False,
#             )

#             await rag.initialize_storages()
#             await initialize_pipeline_status()
#             cls._rag_instance = rag

#         return cls._rag_instance

#     @classmethod
#     def get_rag(cls) -> LightRAG:
#         if cls._rag_instance is None:
#             raise RuntimeError("RAG instance has not been initialized. Call `await RAGManager.init_rag()` first.")
#         return cls._rag_instance


import os
from typing import Dict
from lightrag import LightRAG
from lightrag.utils import EmbeddingFunc
from lightrag.llm.openai import gpt_4o_complete, openai_embed
from lightrag.kg.shared_storage import initialize_pipeline_status
from config.appconfig import settings as app_settings
from database.db_helper import initialize_age

class RAGManager:
    _instances: Dict[str, LightRAG] = {}

    @classmethod
    async def get_or_create_rag(cls, db_user: str, db_name: str, db_pass: str, working_dir: str) -> LightRAG:
        if working_dir not in cls._instances:
            os.makedirs(working_dir, exist_ok=True)

            # Inject tenant-specific DB credentials for LightRAG
            os.environ["POSTGRES_USER"] = db_user
            os.environ["POSTGRES_PASSWORD"] = db_pass
            os.environ["POSTGRES_DATABASE"] = db_name

            # Ensure AGE and ag_catalog are ready
            initialize_age(db_user, db_name, db_pass)

            rag = LightRAG(
                working_dir=working_dir,
                llm_model_func=gpt_4o_complete,
                llm_model_name="gpt-4o",
                llm_model_max_async=2,
                llm_model_max_token_size=128000,
                enable_llm_cache_for_entity_extract=True,
                embedding_func=EmbeddingFunc(
                    embedding_dim=3072,
                    max_token_size=8192,
                    func=lambda texts: openai_embed(
                        texts,
                        model="text-embedding-3-large",
                        api_key=app_settings.openai_api_key,
                        base_url=app_settings.openai_api_base
                    ),
                ),
                kv_storage="PGKVStorage",
                doc_status_storage="PGDocStatusStorage",
                graph_storage="PGGraphStorage",
                vector_storage="PGVectorStorage",
                auto_manage_storages_states=False,
            )

            await rag.initialize_storages()
            await initialize_pipeline_status()

            cls._instances[working_dir] = rag
        return cls._instances[working_dir]




# from typing import Dict
# from dotenv import load_dotenv  # type: ignore
# from lightrag import LightRAG
# from lightrag.utils import EmbeddingFunc
# from lightrag.llm.openai import gpt_4o_complete, openai_embed
# from lightrag.kg.shared_storage import initialize_pipeline_status
# from config.appconfig import settings as app_settings
# import os

# # Load environment variables from .env file 
# load_dotenv()


# class RAGManager:
#     _instances: Dict[str, LightRAG] = {}

#     @classmethod
#     async def get_or_create_rag(cls, working_dir: str, db_name: str) -> LightRAG:
#         if working_dir not in cls._instances:
#             os.makedirs(working_dir, exist_ok=True)

#             rag = LightRAG(
#                 working_dir=working_dir,
#                 llm_model_func=gpt_4o_complete,
#                 llm_model_name="gpt-4o",
#                 llm_model_max_async=2,
#                 llm_model_max_token_size=128000,
#                 enable_llm_cache_for_entity_extract=True,
#                 embedding_func=EmbeddingFunc(
#                     embedding_dim=3072,
#                     max_token_size=8192,
#                     func=lambda texts: openai_embed(
#                         texts,
#                         model="text-embedding-3-large",
#                         api_key=app_settings.openai_api_key,
#                         base_url=app_settings.openai_api_base
#                     ),
#                 ),
#                 kv_storage="PGKVStorage",
#                 doc_status_storage="PGDocStatusStorage",
#                 graph_storage="PGGraphStorage",
#                 vector_storage="PGVectorStorage",
#                 storage_config={
#                     "workspace": db_name
#                 },
#                 auto_manage_storages_states=False,
#             )

#             await rag.initialize_storages()
#             await initialize_pipeline_status()

#             cls._instances[working_dir] = rag
#         return cls._instances[working_dir]