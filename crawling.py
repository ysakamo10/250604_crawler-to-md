import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
import html2text
from typing import List

def parse_sitemap(xml_path: str) -> List[str]:
    """
    XML（sitemap）ファイルを読み込み、<loc> 要素の中身をすべて抽出して URL リストとして返す。

    Args:
        xml_path (str): sitemap.xml のファイルパス

    Returns:
        List[str]: 抽出された URL のリスト
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # 名前空間がある場合に対応
    # 例: <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" ... >
    ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

    urls = []
    # <loc> 要素をすべて取得 (名前空間あり/なし両対応)
    for loc in root.findall('.//sm:loc', ns) + root.findall('.//loc'):
        if loc.text:
            urls.append(loc.text.strip())
    return urls

def fetch_and_convert_to_markdown(url: str, timeout: int = 10) -> str:
    """
    指定された URL に HTTP GET リクエストを送り、ページ内の本文テキストを Markdown に変換して返す。

    処理手順：
      1. requests で URL を取得
      2. BeautifulSoup で <body> 以下のテキストを抜き出す
      3. html2text で Markdown に変換

    Args:
        url (str): クローリング対象の URL
        timeout (int): requests.get のタイムアウト秒数 (デフォルト: 10)

    Returns:
        str: Markdown 形式に変換されたテキスト 
    """
    # 1. ページを取得
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()  # ステータスコードが 200 以外なら例外発生

    # 2. BeautifulSoup で HTML をパース
    soup = BeautifulSoup(response.content, 'html.parser')

    # 3. <body> 以下の HTML を文字列として取り出す
    body = soup.body
    if body is None:
        html_fragment = str(soup)  # body がなければページ全体
    else:
        html_fragment = ''.join(str(tag) for tag in body.find_all(recursive=False))

    # 4. html2text で Markdown に変換
    converter = html2text.HTML2Text()
    converter.ignore_links = False   # リンクも含めたい場合は False
    converter.ignore_images = True    # 画像は不要なら True
    converter.body_width = 0          # 折り返しなし
    markdown_text = converter.handle(html_fragment)

    return markdown_text

if __name__ == "__main__":
    # --- 使い方の例 ---

    # 1) sitemap.xml から URL 一覧を取得
    sitemap_file = "sitemap.xml"  # 適宜パスを変更してください
    url_list = parse_sitemap(sitemap_file)

    # 2) 取得した各 URL について Markdown テキストを抽出し、標準出力に表示
    for url in url_list:
        print(f"# URL: {url}\n")
        try:
            md = fetch_and_convert_to_markdown(url)
            print(md)
        except Exception as e:
            print(f"> エラー: {e}\n")
        print("\n" + "="*80 + "\n")
