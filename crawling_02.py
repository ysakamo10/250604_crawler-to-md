import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
import html2text
from typing import List

def parse_sitemap(xml_path: str) -> List[str]:
    """
    XML（sitemap）ファイルを読み込み、<loc> 要素の中身をすべて抽出して URL リストとして返す。
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # 名前空間を考慮（必要に応じて）
    ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

    urls = []
    # 名前空間ありの<loc>と、なければ通常の<loc>を両方チェック
    for loc in root.findall('.//sm:loc', ns) + root.findall('.//loc'):
        if loc.text:
            urls.append(loc.text.strip())
    return urls

def fetch_and_convert_to_markdown(url: str, timeout: int = 10) -> str:
    """
    指定された URL に HTTP GET リクエストを送り、ページ内の本文テキストを Markdown に変換して返す。
    （ここでは <body> 以下をまるっと Markdown 化する想定）
    """
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')
    body = soup.body
    if body is None:
        html_fragment = str(soup)
    else:
        # <body> 直下にある要素すべてを結合して取得
        html_fragment = ''.join(str(tag) for tag in body.find_all(recursive=False))

    converter = html2text.HTML2Text()
    converter.ignore_links = False    # リンクを残したい場合は False
    converter.ignore_images = True     # 画像は不要なら True
    converter.body_width = 0           # マークダウンの折り返しなし
    markdown_text = converter.handle(html_fragment)

    return markdown_text

if __name__ == "__main__":
    # ── 設定部分 ──
    sitemap_file = "sitemap.xml"  # あらかじめダウンロードしておいた sitemap.xml のパス
    PREFIX = "https://docs.dify.ai/ja-jp"  # この接頭辞で始まる URL だけを対象にする
    output_path = "output.md"  # 最終的にまとめた Markdown を書き出すファイル名
    # ── ここまで ──

    # 1) sitemap.xml から URL 一覧を取得
    url_list = parse_sitemap(sitemap_file)

    # 2) PREFIX で始まる URL のみをフィルタリング
    filtered_urls = [u for u in url_list if u.startswith(PREFIX)]

    if not filtered_urls:
        print(f"WARNING: {PREFIX} で始まる URL が見つかりませんでした。")
        exit(1)

    # 3) 各ページを取得して Markdown に変換し、一つのファイルにまとめて書き出す
    with open(output_path, "w", encoding="utf-8") as fout:
        for url in filtered_urls:
            print(f"Fetching → {url}")
            fout.write(f"# URL: {url}\n\n")  # Markdown の見出しとして URL を入れる
            try:
                md = fetch_and_convert_to_markdown(url)
                fout.write(md)
            except Exception as e:
                # エラーが起きたらログを残しつつ次の URL に進む
                error_msg = f">> エラー: {e}\n\n"
                fout.write(error_msg)
                print(f"  エラー発生: {e}")
            # URL ごとに区切り線を挿入
            fout.write("\n\n---\n\n")

    print(f"完了しました。生成された Markdown ファイル：{output_path}")
