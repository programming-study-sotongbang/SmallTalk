"""
키워드 기반 워커(서브 에이전트) 검색 엔진.

등록된 워커의 이름과 설명을 TF-IDF 벡터로 인덱싱하고,
쿼리와의 코사인 유사도를 기반으로 관련 워커를 검색합니다.
"""

from __future__ import annotations

from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class SearchableItem:
    """검색 가능한 항목 (워커 정보)"""

    name: str
    description: str

    @property
    def search_text(self) -> str:
        """검색에 사용할 텍스트 (이름 + 설명)"""
        return f"{self.name} {self.description}"


@dataclass
class SearchResult:
    """검색 결과"""

    item: SearchableItem
    score: float


class KeywordSearchEngine:
    """TF-IDF 기반 키워드 검색 엔진"""

    def __init__(self) -> None:
        self._items: list[SearchableItem] = []
        self._vectorizer: TfidfVectorizer | None = None
        self._tfidf_matrix = None

    def index(self, items: list[SearchableItem]) -> None:
        """
        검색 대상 항목들을 인덱싱합니다.

        Args:
            items: 인덱싱할 항목 목록.
        """
        self._items = list(items)

        if not self._items:
            self._vectorizer = None
            self._tfidf_matrix = None
            return

        self._vectorizer = TfidfVectorizer(
            token_pattern=r"(?u)\b\w+\b",  # 1글자 토큰도 포함 (한국어 대응)
        )
        texts = [item.search_text for item in self._items]
        self._tfidf_matrix = self._vectorizer.fit_transform(texts)

    def add_item(self, item: SearchableItem) -> None:
        """
        단일 항목을 추가하고 인덱스를 재구축합니다.

        Args:
            item: 추가할 항목.
        """
        self._items.append(item)
        self.index(self._items)

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """
        쿼리와 가장 관련 있는 항목을 검색합니다.

        Args:
            query: 검색 쿼리 문자열.
            top_k: 반환할 최대 결과 수.

        Returns:
            유사도 점수 내림차순으로 정렬된 검색 결과 목록.
        """
        if not self._items or self._vectorizer is None or self._tfidf_matrix is None:
            return []

        query_vec = self._vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self._tfidf_matrix).flatten()

        # 유사도 > 0인 결과만 필터링 후 상위 K개
        scored = [
            (idx, score)
            for idx, score in enumerate(similarities)
            if score > 0
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        return [
            SearchResult(item=self._items[idx], score=score)
            for idx, score in scored[:top_k]
        ]
