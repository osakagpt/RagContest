import os

import openai


class OpenAIClient:
    def __init__(self, model: str = "text-embedding-3-small"):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai.OpenAI(api_key=api_key)
        self.EMBEDDING_MODEL = model

    def get_embedding(self, query: str, answer: str) -> list:
        task = "年齢を表す数字を正しく識別せよ"
        text = f"task: {task}\nquery: {query}\nanswer: {answer}"
        res = self.client.embeddings.create(input=[text], model=self.EMBEDDING_MODEL)
        return res.data[0].embedding
