# -*- coding: utf-8 -*-
import logging
import re
from bs4 import BeautifulSoup, Tag
from lncrawl.core.crawler import Crawler

logger = logging.getLogger(__name__)

SEARCH_A = "https://centralnovel.com/?s=%s"
SEARCH_B = "https://centralnovel.com/?s=%s&post_type=series"


class CentralNovel(Crawler):
    base_url = "https://centralnovel.com/"

    def initialize(self):
        # Remover elementos comuns de navegação/ruído
        self.cleaner.bad_css.update([
            "div.sharethis-inline-share-buttons",
            "div.code-block",
            "div.wp-block-code",
            "div.adblock",
            "div.related-posts",
            "nav.breadcrumb",
            "header",
            "footer",
        ])

    # ----------------------- BUSCA -----------------------
    def search_novel(self, query: str):
        q = (query or "").strip().lower().replace(" ", "+")
        if not q:
            return []
        results = []
        # Tenta padrão geral (?s=)
        for url in [SEARCH_A % q, SEARCH_B % q]:
            try:
                soup = self.get_soup(url)
            except Exception:
                continue
            # comum a temas de novel/madara
            for tab in soup.select(".c-tabs-item__content, .tab-summary, .c-tabs-item .c-tabs-item__content"):
                a = tab.select_one(".post-title h3 a, .post-title a, h3 a, h2 a")
                if not a:
                    continue
                latest = tab.select_one(".latest-chap .chapter a, .latest-chapter a")
                votes = tab.select_one(".rating .total_votes, .score font, .rating span")
                results.append({
                    "title": a.get_text(strip=True),
                    "url": self.absolute_url(a.get("href")),
                    "info": "%s%s" % (
                        (latest.get_text(strip=True) if latest else "N/A"),
                        (" | Rating: %s" % votes.get_text(strip=True)) if votes else "",
                    ),
                })
            # fallback genérico
            if not results:
                for a in soup.select(".post-title a, article h2 a, h3 a"):
                    href = a.get("href") or ""
                    if "/series/" in href:
                        results.append({
                            "title": a.get_text(strip=True),
                            "url": self.absolute_url(href),
                            "info": "N/A",
                        })
            if results:
                break
        return results

    # ------------------- INFO DA NOVEL -------------------
    def read_novel_info(self):
        logger.debug("Visiting %s", self.novel_url)
        soup = self.get_soup(self.novel_url)

        # --- Título ---
        title_tag = (
            soup.select_one("#manga-title h1")
            or soup.select_one(".post-title h1")
            or soup.select_one(".series-title h1")
            or soup.select_one("h1.entry-title")
            or soup.select_one("h1[itemprop='name']")
        )
        if title_tag:
            for sp in title_tag.select("span"):
                sp.extract()
            self.novel_title = title_tag.get_text(strip=True)

        if not self.novel_title:
            ogt = soup.select_one('meta[property="og:title"]')
            if ogt and ogt.get("content"):
                self.novel_title = ogt["content"].strip()
        if not self.novel_title and soup.title:
            self.novel_title = soup.title.get_text(strip=True).split(" – ")[0].strip()

        if not self.novel_title:
            raise Exception("Título da novel não encontrado.")

        logger.info("Novel title: %s", self.novel_title)

        # --- Capa ---
        image = (
            soup.select_one(".summary_image img")
            or soup.select_one(".series-thumb img")
            or soup.select_one("img.wp-post-image")
        )
        if isinstance(image, Tag):
            src = image.get("data-src") or image.get("src")
            self.novel_cover = self.absolute_url(src)
        if not self.novel_cover:
            og = soup.select_one('meta[property="og:image"]')
            if og and og.get("content"):
                self.novel_cover = self.absolute_url(og["content"])
        logger.info("Novel cover: %s", self.novel_cover)

        # --- Autor ---
        authors = [a.get_text(strip=True) for a in soup.select(".author-content a, .series-author a")]
        if not authors:
            for meta in soup.select('meta[property="article:author"]'):
                href = meta.get("content") or ""
                name = href.rstrip("/").split("/")[-1].replace("-", " ").title()
                if name:
                    authors.append(name)
        self.novel_author = ", ".join(dict.fromkeys([a for a in authors if a]))
        logger.info("Author(s): %s", self.novel_author or "N/A")

        # --- Capítulos & Volumes ---
        if not self._load_chapters_via_ajax():
            self._load_chapters_from_html(soup)

        if not self.volumes:
            self.volumes = [{"id": 1, "title": "Volume 1"}]

        try:
            for i, v in enumerate(self.volumes, start=1):
                if isinstance(v, dict):
                    v.setdefault("display_number", i)
        except Exception:
            pass

    # --------------- CONTEÚDO DO CAPÍTULO ---------------
    def download_chapter_body(self, chapter):
        soup = self.get_soup(chapter["url"])
        contents = (
            soup.select_one(".reading-content")
            or soup.select_one(".entry-content")
            or soup.select_one("article")
        )
        return self.cleaner.extract_contents(contents)

    # ---- Normalização de títulos ----
    def _clean_chapter_title(self, text: str) -> str:
        """
        Remove prefixos como Vol. 12 / Volume 12 e datas PT-BR no final,
        preservando o resto do título (ex.: Cap. 1.1.0 Prólogo! ou
        Capítulo 1 (Parte 1)).
        """
        if not text:
            return text
        t = text.strip()
        # Remove prefixo Vol. X / Volume X no começo
        t = re.sub(r'^\s*(?:Vol\.?|Volume)\s*\d+\s*[-–:]*\s*', '', t, flags=re.IGNORECASE)
        # Remove datas PT-BR no final (Agosto 10, 2025 | 10 de Agosto de 2025 | 10/08/2025)
        meses = r'Janeiro|Fevereiro|Março|Abril|Maio|Junho|Julho|Agosto|Setembro|Outubro|Novembro|Dezembro'
        padroes = [
            rf'\b(?:{meses})\s+\d{{1,2}},\s*\d{{4}}\s*$',
            rf'\b\d{{1,2}}\s+de\s+(?:{meses})\s+de\s+\d{{4}}\s*$',
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\s*$',
        ]
        for pat in padroes:
            t = re.sub(pat, '', t, flags=re.IGNORECASE)
        # limpeza final
        t = re.sub(r'\s{2,}', ' ', t).strip(' -–:').strip()
        return t

    # ==================== HELPERS ========================
    def _load_chapters_via_ajax(self) -> bool:
        try:
            chapter_list_url = self.absolute_url("ajax/chapters", self.novel_url)
            soup = self.post_soup(chapter_list_url, headers={"accept": "*/*"})
        except Exception as e:
            logger.debug("AJAX chapters falhou: %s", e)
            return False

        li_groups = soup.select("li.parent.has-child") or soup.select("li.parent")
        if not li_groups:
            return False

        volume_id = 0
        for li in reversed(li_groups):
            volume_id += 1
            volume_title = li.select_one("a.has-child") or li.select_one("> a") or li.select_one("h2, h3, .volume-title")
            vtitle = volume_title.get_text(strip=True) if volume_title else f"Volume {volume_id}"
            self.volumes.append({"id": volume_id, "title": vtitle})

            chapter_links = li.select(".wp-manga-chapter a[href], a.chapter[href]") or li.select("a[href]")
            for a in reversed(chapter_links):
                for span in a.find_all("span"):
                    span.extract()
                text = a.get_text(" ", strip=True)
                href = a.get("href")
                if not href or not text:
                    continue
                self.chapters.append({
                    "id": len(self.chapters) + 1,
                    "volume": volume_id,
                    "title": self._clean_chapter_title(text),
                    "url": self.absolute_url(href),
                })
        return len(self.chapters) > 0

    def _load_chapters_from_html(self, soup: BeautifulSoup) -> None:
        self.chapters = []
        self.volumes = []

        m = re.search(r"/series/([^/]+)/?", self.novel_url.rstrip("/"))
        base_slug = m.group(1) if m else ""

        anchors = soup.select("a[href]")
        items = []
        for a in anchors:
            href = (a.get("href") or "").strip()
            if not href or "://" not in href:
                continue
            if not base_slug or base_slug not in href:
                continue
            if "/series/" in href:
                continue
            for span in a.find_all("span"):
                span.extract()
            text = a.get_text(" ", strip=True)
            if not text:
                continue
            items.append((text, self.absolute_url(href)))

        seen = set()
        ordered = []
        for text, url in items:
            if url in seen:
                continue
            seen.add(url)
            ordered.append((text, url))

        if not ordered:
            return

        volume_ids = {}
        volumes = []

        def get_vol_id_from_text(txt: str):
            m1 = re.search(r"(?i)\bVol\.?\s*(\d+)", txt)
            m2 = re.search(r"(?i)\bVolume\s*(\d+)", txt)
            num = None
            if m1:
                num = int(m1.group(1))
            elif m2:
                num = int(m2.group(1))
            if not num:
                return 1
            if num not in volume_ids:
                volume_ids[num] = len(volume_ids) + 1
                volumes.append({"id": volume_ids[num], "title": f"Volume {num}"})
            return volume_ids[num]

        ordered = list(reversed(ordered))

        chap_id = 0
        for text, url in ordered:
            vol_id = get_vol_id_from_text(text)
            chap_id += 1
            self.chapters.append({
                "id": chap_id,
                "volume": vol_id,
                "title": self._clean_chapter_title(text),
                "url": url,
            })

        if not volumes:
            volumes = [{"id": 1, "title": "Volume 1"}]
        self.volumes = volumes


# Registro
Crawler = CentralNovel
