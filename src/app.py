import streamlit as st
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

st.title("Difyドキュメント クローラー to Markdown")

uploaded_file = st.file_uploader("sitemap.xml を選択してください", type="xml")
prefix = st.text_input("対象 URL のプレフィックス", "https://docs.dify.ai/ja-jp")
output_filename = st.text_input("出力ファイル名", "output.md")

if st.button("変換を開始"):
    if uploaded_file is None:
        st.error("まず sitemap.xml をアップロードしてください。")
    else:
        with open("temp_sitemap.xml", "wb") as f:
            f.write(uploaded_file.read())

        # 1) URL 取得
        urls = parse_sitemap("temp_sitemap.xml")
        filtered = [u for u in urls if u.startswith(prefix)]
        if not filtered:
            st.warning(f"プレフィックス「{prefix}」で始まる URL が見つかりませんでした。")
        else:
            md_contents = []
            progress = st.progress(0)
            total = len(filtered)
            for idx, url in enumerate(filtered):
                st.write(f"▶ フェッチ中: {url}")
                try:
                    md = fetch_and_convert_to_markdown(url)
                    md_contents.append(f"# URL: {url}\n\n{md}\n\n---\n\n")
                except Exception as e:
                    md_contents.append(f"# URL: {url}\n\n>> エラー: {e}\n\n---\n\n")
                progress.progress((idx + 1) / total)

            # 結合してダウンロード可能に
            final_md = "".join(md_contents)
            st.download_button(
                label="Markdown ファイルをダウンロード",
                data=final_md,
                file_name=output_filename,
                mime="text/markdown",
            )
            st.success("完了しました！")
