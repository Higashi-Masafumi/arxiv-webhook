import arxiv
import re
from models import ArxivInfo
from logging import getLogger


class ArxivInfoFetcher:
    def __init__(self):
        self.logger = getLogger(__name__)

    def update_info_by_url(self, arxiv_info: ArxivInfo) -> ArxivInfo:
        """Update the information of an existing ArxivInfo object.

        Args:
            arxiv_info (ArxivInfo): The ArxivInfo object to update.

        Raises:
            ValueError: If the arxiv URL is invalid.

        Returns:
            ArxivInfo: The updated ArxivInfo object.
        """
        # arxiv IDで検索
        arxiv_id = self._extract_arxiv_id(arxiv_info.url)
        if arxiv_id is None:
            self.logger.error(f"Invalid arxiv URL: {arxiv_info.url}")
            raise ValueError("Invalid arxiv URL")

        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(search.results())

        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(search.results())

        # 著者名をリストで取得
        authors = [author.name for author in paper.authors]

        return ArxivInfo(
            page_id=arxiv_info.page_id,
            title=paper.title,
            authors=authors,
            summary=paper.summary,
            url=paper.entry_id,
            publication_year=paper.published.year,
        )

    def _extract_arxiv_id(self, url: str) -> str | None:
        """arxivのURLからarxiv IDを抽出する"""
        match = re.search(r"(arxiv|alphaxiv)\.org/(abs|pdf)/([^?#\s]+)", url)
        if match:
            return match.group(3)  # 3番目のグループ(論文ID)を返す
        return None
