from pydantic import BaseModel


class RecommendResponse(BaseModel):
    thread_id: str
    answer: str
