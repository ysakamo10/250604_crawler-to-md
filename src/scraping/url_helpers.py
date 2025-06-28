import requests

def fetch_url(url: str) -> str:
    """指定したURLからHTMLを取得して返す"""
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.text