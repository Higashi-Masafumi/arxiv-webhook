import os
import re
from logging import INFO, FileHandler, getLogger

import arxiv
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from notion_client import Client

from models import ArxivInfo

load_dotenv()

app = FastAPI()

# Notion client setup
notion = Client(auth=os.getenv("NOTION_TOKEN"))
logger = getLogger(__name__)
logger.addHandler(FileHandler("app.log"))
logger.setLevel(INFO)


def extract_arxiv_id(url: str) -> str | None:
    """arxivのURLからarxiv IDを抽出する

    Args:
        url (str): arxivのURL

    Returns:
        str | None: arxiv ID
    >>> extract_arxiv_id("https://arxiv.org/abs/2505.22618")
    "2505.22618"
    >>> extract_arxiv_id("https://arxiv.org/pdf/2104.09864")
    "2104.09864"
    >>> extract_arxiv_id("https://arxiv.org/abs/math/0703456")
    "0703456"
    >>> extract_arxiv_id("https://arxiv.org/pdf/cs/0512345")
    "0512345"
    >>> extract_arxiv_id("https://example.com/not-arxiv")
    None
    """
    # https://arxiv.org/abs/2505.22618 形式のURLからIDを抽出
    # https://arxiv.org/pdf/2104.09864 形式のURLからIDを抽出
    # 古い形式（math/0703456、cs/0512345など）にも対応
    match = re.search(r"arxiv\.org/(abs|pdf)/([^?#\s]+)", url)
    if match:
        return match.group(2)  # 2番目のグループ（論文ID）を返す
    return None


def fetch_arxiv_paper_info(arxiv_id: str) -> ArxivInfo:
    """arxivライブラリを使って論文情報を取得する"""
    # arxiv IDで検索
    search = arxiv.Search(id_list=[arxiv_id])
    paper = next(search.results())

    # 著者名をリストで取得
    authors = [author.name for author in paper.authors]

    return ArxivInfo(
        title=paper.title,
        authors=authors,
        summary=paper.summary,
        publication_year=paper.published.year,
    )


def update_notion_page(page_id: str, arxiv_info: ArxivInfo):
    # まずページがあるかチェックする
    try:
        notion.pages.retrieve(page_id=page_id)
    except Exception as e:
        logger.error(f"Failed to retrieve Notion page {page_id}: {str(e)}")
        raise
    # ページがある場合は更新する
    notion.pages.update(
        page_id=page_id,
        properties=arxiv_info.to_notion_properties(),
    )


@app.get("/")
async def root():
    return {"message": "ArXiv Webhook Service"}


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    # webhook payloadのデータを取得
    page_id = data["data"]["id"]
    page_url = data["data"]["url"]
    arxiv_url = data["data"]["properties"]["Link"]["url"]
    logger.info(f"page_id: {page_id}, page_url: {page_url}, arxiv_url: {arxiv_url}")
    # arxiv_urlからarxiv_idを抽出
    arxiv_id = extract_arxiv_id(arxiv_url)
    # arxiv_idがNoneの場合はエラーを返す
    if arxiv_id is None:
        logger.error(f"arxiv_id is None: {arxiv_url}")
        return {"message": "Invalid arxiv url"}
    # arxiv_idで論文情報を取得
    logger.info(f"fetching arxiv paper info: {arxiv_id}")
    arxiv_info = fetch_arxiv_paper_info(arxiv_id)
    # notionページを更新
    update_notion_page(page_id, arxiv_info)
    logger.info(
        f"updated notion page: {page_id}, page_url: {page_url}, arxiv_id: {arxiv_id}, arxiv_url: {arxiv_url}"
    )
    return {"message": "Webhook received"}
