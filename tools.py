from langchain.tools.retriever import create_retriever_tool
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_pinecone import PineconeVectorStore
from langchain.tools import tool
from prompts import TOOLS_VERSION_ONE
import os
from io import BytesIO
import matplotlib.pyplot as plt

class Tools:
    @staticmethod
    def setup_tools():
        retriever_tool_web_search = create_retriever_tool(
            GetRetriever("seedworld-whitepaper-rag"),  #
            "seedworld-whitepaper-search",
            TOOLS_VERSION_ONE,
        )

        tools = [retriever_tool_web_search]
        return tools
    
    @staticmethod
    def setup_tools_data_analysis():
        print("Starting setup_tools_data_analysis")
        
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"Current directory: {current_dir}")
        
        # Construct the path to the documents folder
        # Change this line to look for 'documents' in the same directory as the script
        documents_dir = os.path.join(current_dir, 'documents')
        print(f"Documents directory: {documents_dir}")
        
        # Construct the full path to the order_details.txt file
        file_path = os.path.join(documents_dir, 'order_details.csv')
        print(f"File path: {file_path}")
        
        # Check if the file exists
        if not os.path.exists(file_path):
            print(f"File not found at: {file_path}")
            print("Listing contents of documents directory:")
            try:
                print(os.listdir(documents_dir))
            except FileNotFoundError:
                print(f"Documents directory not found: {documents_dir}")
            raise FileNotFoundError(f"The file {file_path} does not exist.")
        
        print("File found, attempting to read")
        file_contents = read_text_file(file_path)
        print("File read successfully")
        # Wrap the content in the expected format
        wrapped_content = [Document(file_contents)]

        # Split the contents into documents
        documents = RecursiveCharacterTextSplitter(
            chunk_size=100000, chunk_overlap=200
        ).split_documents(wrapped_content)

        # Create FAISS vectors and retriever
        vector = FAISS.from_documents(documents, OpenAIEmbeddings())
        retriever = vector.as_retriever()

        retriever_tool = create_retriever_tool(
            retriever,
            "order_details_search",
            "Search and analyze the complete order details dataset. This tool provides access to all order information including dates, customer data, product categories, quantities, prices, and sales figures. Use it for summarizing overall sales, identifying trends, analyzing customer behavior, or querying specific order details."
        )
        tools = [retriever_tool]
        return tools
    
class Document:
    def __init__(self, content, metadata=None):
        self.page_content = content
        self.metadata = metadata if metadata is not None else {}
    
def GetRetriever(index_name):
    embeddings=OpenAIEmbeddings()
    vectorstore = PineconeVectorStore(index_name=index_name, embedding=embeddings)
    retriever = vectorstore.as_retriever()
    return retriever

def read_text_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


