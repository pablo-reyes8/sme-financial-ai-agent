from __future__ import annotations

from typing import Iterable, List

import bs4
import requests
from langchain_community.document_loaders import DirectoryLoader, TextLoader, WebBaseLoader
from langchain_core.documents import Document


def load_local_documents(knowledge_dir: str) -> List[Document]:
    loader = DirectoryLoader(
        knowledge_dir,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    return loader.load()


def load_web_documents(web_sources: Iterable[str]) -> List[Document]:
    session = requests.Session()
    loader = WebBaseLoader(
        web_paths=tuple(web_sources),
        bs_kwargs={"parse_only": bs4.SoupStrainer("body")},
        session=session,
    )
    return loader.load()


def load_documents(knowledge_dir: str, web_sources: Iterable[str], enable_web: bool) -> List[Document]:
    documents = load_local_documents(knowledge_dir)
    if enable_web:
        documents.extend(load_web_documents(web_sources))
    return documents
