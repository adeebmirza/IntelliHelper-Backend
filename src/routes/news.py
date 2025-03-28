from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import requests
from src.Intelli_News.intelli_news_function import search_bing_news

news_router = APIRouter(prefix="/Intelli_news", tags=["News"])

@news_router.get("/")
async def get_news(query: Optional[str] = Query(None)):
    """
    Fetch news based on query.
    If no query is provided, it fetches the latest news.
    """
    try:
        news_results = search_bing_news(query if query else "latest news")
        return {"results": news_results}
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Lost Internet Connection")

@news_router.get("/category/{category}")
async def get_news_by_category(category: str):
    """
    Fetch news based on category.
    """
    try:
        news_results = search_bing_news(category)
        return {"results": news_results}
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Lost Internet Connection")
