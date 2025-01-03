from typing import List
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

from dotenv import load_dotenv
load_dotenv(override=True)

class MarkdownVectorDB:
    def __init__(
        self, persist_directory: str="vector_store_data", markdown_folder: str="markdown_data"
    ):
        self.persist_directory = persist_directory
        self.markdown_folder = markdown_folder
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=600, chunk_overlap=200
        )
        self.vector_store = None

    def _initialize_vector_store(self):
        if not os.path.exists(self.persist_directory):
            os.makedirs(self.persist_directory)
        return Chroma(
            embedding_function=self.embeddings, persist_directory=self.persist_directory
        )

    def process_markdown_files(self):
        documents = []

        for filename in os.listdir(self.markdown_folder):
            if filename.endswith(".md"):
                filepath = os.path.join(self.markdown_folder, filename)

                with open(filepath, "r", encoding="utf-8") as file:
                    content = file.read()
                    chunks = self.text_splitter.split_text(content)

                    for chunk in chunks:
                        keywords = self.extract_keywords(chunk)
                        doc = Document(
                            page_content=chunk,
                            metadata={
                                "source": filename,
                                "keywords": ",".join(keywords),
                            },
                        )
                        documents.append(doc)

        return documents

    def generate_vector_database(self):
        documents = self.process_markdown_files()
        self.vector_store = self._initialize_vector_store()
        self.vector_store.add_documents(documents)
        self.vector_store.persist()
        print(f"Processed and added {len(documents)} chunks to the vector database.")

    def load_vector_database(self):
        print("Loading existing vector database...")
        self.vector_store = self._initialize_vector_store()

    def retrieve_documents(self, query: str, top_k: int = 5) -> List[Document]:
        if self.vector_store is None:
            raise ValueError(
                "Vector store is not initialized. Load or generate the vector store first."
            )
        results = self.vector_store.similarity_search(query, k=top_k)
        return results

    @staticmethod
    def extract_keywords(chunk: str, top_n: int = 10) -> List[str]:
        documents = [chunk]
        tfidf_vectorizer = TfidfVectorizer(stop_words="english", max_features=top_n)
        tfidf_matrix = tfidf_vectorizer.fit_transform(documents)
        feature_array = np.array(tfidf_vectorizer.get_feature_names_out())
        tfidf_sorting = np.argsort(tfidf_matrix.toarray()).flatten()[::-1]
        top_keywords = feature_array[tfidf_sorting][:top_n]
        return top_keywords.tolist()

    def recreate_or_load_vector_db(self, recreate=False):
        if recreate:
            print("Recreating vector database...")
            self.generate_vector_database()
        else:
            print("Loading vector database...")
            self.load_vector_database()


class Application:
    def __init__(self, recreate_vector_db=False):
        self.vector_db = MarkdownVectorDB()
        self.vector_db.recreate_or_load_vector_db(recreate=recreate_vector_db)

    def run(self):
        while True:
            query = input("Your query text here: ")
            retrieved_docs = self.vector_db.retrieve_documents(query)
            for i, doc in enumerate(retrieved_docs):
                print(f"Document {i+1}:")
                print(f"Content: {doc.page_content}")
                print(f"Metadata: {doc.metadata}")


if __name__ == "__main__":
    recreate = input("Recreate vector database? (yes/no): ").strip().lower() == "yes"
    app = Application(recreate_vector_db=recreate)
    app.run()
