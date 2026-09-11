FROM python:3.12-slim

WORKDIR /srv

COPY pyproject.toml ./
COPY app ./app
COPY static ./static
COPY butler_agent.py ./

RUN pip install --no-cache-dir \
    langchain langchain-community langchain-openai langchain-tavily \
    langgraph langsmith pillow python-dotenv tavily-python \
    fastapi "uvicorn[standard]" python-multipart

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
