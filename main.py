import os
from logging import INFO, FileHandler, getLogger
from typing import Awaitable, Callable
import sentry_sdk
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request, Response
from notion_py_client import NotionAsyncClient
from notion import NotionPaperRepository
from arxiv_fetcher import ArxivInfoFetcher

load_dotenv()

app = FastAPI()

# Notion client setup
notion = NotionAsyncClient(auth=os.getenv("NOTION_TOKEN"))
logger = getLogger(__name__)
logger.addHandler(FileHandler("app.log"))
logger.setLevel(INFO)
sentry_sdk.init(
    dsn="https://d3eb762daf497b091c917c72d13f7168@o4509661921083392.ingest.us.sentry.io/4510221999865856",
    send_default_pii=True,
)


def get_notion_repository() -> NotionPaperRepository:
    return NotionPaperRepository(notion_client=notion)


def arxiv_fetcher() -> ArxivInfoFetcher:
    return ArxivInfoFetcher()


@app.middleware("http")
async def check_attempt(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    # Simple middleware to log incoming requests
    logger.info(f"Incoming request: {request.method} {request.url}")
    # Post以外は無視する
    if request.method != "POST":
        return await call_next(request)
    request_data = await request.json()
    logger.info(f"Request data: {request_data}")
    response = await call_next(request)
    return response


@app.get("/")
async def root():
    return {"message": "ArXiv Webhook Service"}


@app.post("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/sentry-debug")
async def sentry_debug():
    division_by_zero = 1 / 0


@app.post("/webhook")
async def webhook(
    request: Request,
    notion_repo: NotionPaperRepository = Depends(get_notion_repository),
    fetcher: ArxivInfoFetcher = Depends(arxiv_fetcher),
):
    data = await request.json()
    # webhook payloadのデータを取得
    arxiv_info = notion_repo.parse_payload(data)
    logger.info(f"page_id: {arxiv_info.page_id}, arxiv_url: {arxiv_info.url}")
    # arxivから最新情報を取得
    updated_info = fetcher.update_info_by_url(arxiv_info)
    # Notionのページを更新
    await notion_repo.update_paper(updated_info)

    return {"message": "Webhook received"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
