from pymongo import MongoClient
from llama_index.storage.docstore.mongodb import MongoDocumentStore

docstore = MongoDocumentStore.from_uri(
    uri="mongodb://memento:memento@172.22.233.246:27017?directConnection=true",
    db_name="memento",
    namespace="node_docstore",
)

node = docstore.get_document("429e70cb-1cb3-4d1d-899d-a917bd3d1515", raise_error=False)
print(node)