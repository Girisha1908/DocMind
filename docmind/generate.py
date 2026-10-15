"""Answer generation with Mistral. Needs MISTRAL_API_KEY (in .env); retrieval does not."""

from functools import cache

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from .config import ANSWER_MODEL

load_dotenv()

ABSTAIN = "I couldn't find this in the handbook."

PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You answer questions from GitLab employees using ONLY the numbered handbook excerpts provided.\n"
     "Cite the excerpts you used like [1] or [2]. Be concise and specific.\n"
     "If the excerpts do not contain the answer, reply exactly: " + ABSTAIN),
    ("human", "Excerpts:\n{context}\n\nQuestion: {question}"),
])


@cache
def llm(model: str = ANSWER_MODEL):
    from langchain_mistralai import ChatMistralAI

    return ChatMistralAI(model=model, temperature=0)


def format_context(docs: list[Document]) -> str:
    return "\n\n".join(f"[{i}] {d.metadata['title']} ({d.metadata['url']})\n{d.page_content}" for i, d in enumerate(docs, 1))


def answer(question: str, docs: list[Document]) -> str:
    return llm().invoke(PROMPT.invoke({"context": format_context(docs), "question": question})).content
