from tavily import TavilyClient
from config import TAVILY_API_KEY, TAVILY_SEARCH_DEPTH, TAVILY_MAX_RESULTS

_client = None


def _get_client() -> TavilyClient:
    global _client
    if _client is None:
        _client = TavilyClient(api_key=TAVILY_API_KEY)
    return _client


def web_search(query: str) -> str:
    """
    Search the internet via Tavily and return a formatted string
    containing title, URL, and snippet for each result.
    """
    try:
        client = _get_client()
        results = client.search(
            query=query,
            search_depth=TAVILY_SEARCH_DEPTH,
            max_results=TAVILY_MAX_RESULTS,
        )
        if not results.get("results"):
            return "No results found."

        lines = []
        for i, r in enumerate(results["results"], 1):
            lines.append(
                f"[{i}] {r.get('title', 'No title')}\n"
                f"    URL: {r.get('url', '')}\n"
                f"    {r.get('content', '')[:400]}"
            )
        return "\n\n".join(lines)

    except Exception as e:
        return f"Web search error: {e}"
