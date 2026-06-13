"""Parent-Child 청킹 (parent 1000자 / child 300자, 부분 겹침)."""
from langchain_text_splitters import RecursiveCharacterTextSplitter

_SEPARATORS = ["\n\n", "\n", ".", " "]

_parent_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=200, separators=_SEPARATORS
)
_child_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300, chunk_overlap=50, separators=_SEPARATORS
)


def split_text(pages):
    parents, children = [], []
    for page in pages:
        for parent_text in _parent_splitter.split_text(page["text"]):
            parent_id = len(parents)
            parents.append({"text": parent_text, "page": page["page"]})
            for child_text in _child_splitter.split_text(parent_text):
                children.append({
                    "text":      child_text,
                    "page":      page["page"],
                    "parent_id": parent_id,
                })
    return parents, children
