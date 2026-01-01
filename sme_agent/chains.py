from __future__ import annotations

import os
from typing import List

from langchain.chains import ConversationalRetrievalChain
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.retrievers import BaseRetriever
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from sme_agent.config import Settings
from sme_agent.prompts import SYSTEM_PROMPT
from sme_agent.services.knowledge import load_documents


class CustomThresholdRetriever(BaseRetriever):
    vectorstore: Chroma
    threshold: float = 0.3
    k: int = 4

    def _get_relevant_documents(self, query: str, *, run_manager=None) -> List[Document]:
        docs_and_scores = self.vectorstore.similarity_search_with_score(query, k=self.k)
        return [doc for doc, score in docs_and_scores if score < self.threshold]


def build_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history"),
            ("human", "Pregunta: {question}\nContexto:\n{context}\nRespuesta:"),
        ]
    )


def build_vectorstore(settings: Settings) -> Chroma:
    embedding = OpenAIEmbeddings(model=settings.embedding_model)

    if (
        os.path.isdir(settings.chroma_dir)
        and os.listdir(settings.chroma_dir)
        and not settings.rebuild_vectorstore
    ):
        return Chroma(persist_directory=settings.chroma_dir, embedding_function=embedding)

    os.makedirs(settings.chroma_dir, exist_ok=True)

    documents = load_documents(
        knowledge_dir=settings.knowledge_dir,
        web_sources=settings.web_sources,
        enable_web=settings.enable_web_sources,
    )
    if not documents:
        raise RuntimeError("No se cargaron documentos de conocimiento.")

    splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=150)
    splits = [doc for doc in splitter.split_documents(documents) if doc.page_content.strip()]
    if not splits:
        raise RuntimeError("No hay contenido util despues del split.")

    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embedding,
        persist_directory=settings.chroma_dir,
    )
    return vectorstore


def build_retriever(settings: Settings) -> CustomThresholdRetriever:
    vectorstore = build_vectorstore(settings)
    return CustomThresholdRetriever(
        vectorstore=vectorstore,
        threshold=settings.retriever_score_threshold,
        k=settings.retriever_k,
    )


def build_chain(settings: Settings, retriever: CustomThresholdRetriever, memory) -> ConversationalRetrievalChain:
    llm = ChatOpenAI(model=settings.model_name, temperature=settings.temperature)
    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": build_prompt()},
        return_source_documents=False,
    )
