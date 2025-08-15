
# -*- coding: utf-8 -*-
import logging
import re
from bs4 import BeautifulSoup, Tag
from lncrawl.core.crawler import Crawler

logger = logging.getLogger(__name__)

SEARCH_A = "https://novelmania.com.br/?s=%s"
SEARCH_B = "https://novelmania.com.br/novels?title=%s"


class Novelmania(Crawler):
    base_url = "https://novelmania.com.br/"

    def initialize(self):
        # Remover elementos comuns de navegação/ruído
        self.cleaner.bad_css.update([
            "header",
            "footer",
            "nav",
            "div.sharethis-inline-share-buttons",
            "div.adblock",
            "aside",
        ])
        # tags mantidas no conteúdo
        self.cleaner.unchanged_tags.update(["i", "em", "b", "strong"])

    # ----------------------- BUSCA -----------------------
    def search_novel(self, query: str):
        q = (query or "").strip().lower().replace(" ", "+")
        if not q:
            return []
        results = []

        # 1) tenta /novels?title=
        try:
            soup = self.get_soup(SEARCH_B % q)
            # itens de listagem (cartões) – título, autor, etc.
            # funciona mesmo sem JS
            for card in soup.select("a[href*='/novels/']"):
                title = card.get_text(" ", strip=True)
                href = card.get("href") or ""
                # filtra cartões válidos e evita link para Home
                if "/novels/" not in href:
                    continue
                # ignora anchors que não apresentem título legível
                if not title or len(title) < 3:
                    continue
                results.append({
                    "title": title,
                    "url": self.absolute_url(href),
                    "info": "N/A",
                })
        except Exception as e:
            logger.debug("search via /novels falhou: %s", e)

        # 2) fallback: busca global (?s=)
        if not results:
            try:
                soup = self.get_soup(SEARCH_A % q)
                for a in soup.select("a[href*='/novels/']"):
                    title = a.get_text(" ", strip=True)
                    href = a.get("href") or ""
                    if "/novels/" not in href:
                        continue
                    if not title or len(title) < 3:
                        continue
                    results.append({
                        "title": title,
                        "url": self.absolute_url(href),
                        "info": "N/A",
                    })
            except Exception as e:
                logger.debug("fallback ?s= falhou: %s", e)

        # remove duplicados preservando ordem
        seen = set()
        final = []
        for r in results:
            if r["url"] in seen:
                continue
            seen.add(r["url"])
            final.append(r)
        return final

    # ------------------- INFO DA NOVEL -------------------
    def read_novel_info(self):
        logger.debug("Visiting %s", self.novel_url)
        soup = self.get_soup(self.novel_url)

        # --- Título ---
        # Tenta seletores prováveis; remove spans internos
        title_tag = (
            soup.select_one("main h1")
            or soup.select_one(".items-start h1")
            or soup.select_one("h1.entry-title")
            or soup.select_one("h1")
        )
        if title_tag:
            for sp in title_tag.select("span"):
                sp.extract()
            self.novel_title = title_tag.get_text(strip=True)

        # fallback no <title>
        if not self.novel_title and soup.title:
            self.novel_title = soup.title.get_text(strip=True).split(" – ")[0].strip()
        if not self.novel_title:
            raise Exception("Título da novel não encontrado.")

        logger.info("Novel title: %s", self.novel_title)

        # --- Capa ---
        # Observado em prints: capa grande ao lado do título
        image = (
            soup.select_one("img.drop-shadow-ww-novel-cover-image")
            or soup.select_one(".summary_image img")
            or soup.select_one("img.wp-post-image")
            or soup.select_one("main img")
        )
        if isinstance(image, Tag):
            src = image.get("data-src") or image.get("src")
            if src:
                self.novel_cover = self.absolute_url(src)
        logger.info("Novel cover: %s", self.novel_cover)

        # --- Autor ---
        # No site aparece 'Autor:' seguido do nome
        author = None
        # tenta label 'Autor:' e pega próximo elemento
        for tag in soup.find_all(text=re.compile(r"(?i)Autor:")):
            node = tag.parent
            if node:
                sib = node.find_next_sibling()
                txt = (sib.get_text(" ", strip=True) if sib else node.get_text(" ", strip=True))
                txt = re.sub(r"(?i)Autor:\s*", "", txt).strip()
                if txt and len(txt) > 1:
                    author = txt
                    break
        if not author:
            # tenta meta tags
            metas = soup.select('meta[name="author"], meta[property="article:author"]')
            for m in metas:
                c = m.get("content") or ""
                if c:
                    author = c.strip()
                    break
        self.novel_author = author or "N/A"
        logger.info("Author(s): %s", self.novel_author)

        # --- Capítulos & Volumes ---
        # O site usa abas (Sobre | Capítulos | Comentários).
        # 1) tenta carregar diretamente uma variante com a aba de capítulos renderizada.
        if not self._load_chapters_try_variants():
            # 2) se não achou, tenta extrair capítulos presentes na própria página (quando a aba padrão já for capítulos).
            self._load_chapters_from_html(soup)

        if not self.chapters:
            raise Exception("Não foi possível extrair a lista de capítulos.")

        if not self.volumes:
            self.volumes = [{"id": 1, "title": "Volume 1"}]

    # --------------- CONTEÚDO DO CAPÍTULO ---------------
    def download_chapter_body(self, chapter):
        soup = self.get_soup(chapter["url"])
        contents = (
            soup.select_one(".reading-content")
            or soup.select_one("#chapter-content")
            or soup.select_one("article")
            or soup.select_one("main")
        )
        return self.cleaner.extract_contents(contents)

    # ==================== HELPERS ========================

    def _strip_dates_anywhere(self, text: str) -> str:
        """
        Remove datas (por extenso e numéricas) em QUALQUER parte da string.
        """
        if not text:
            return text
        meses = ("janeiro|fevereiro|março|marco|abril|maio|junho|julho|agosto|"
                 "setembro|outubro|novembro|dezembro")
        # por extenso
        text = re.sub(
            rf"""(?ix)
                \b\d{{1,2}}\s+de\s+(?:{meses})\s+de\s+\d{{4}}\b
                (?:\s*,\s*\d{{2}}:\d{{2}})?
            """,
            "",
            text,
        )
        # numérica
        text = re.sub(
            r"""(?ix)\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b(?:\s*,\s*\d{2}:\d{2})?""",
            "",
            text,
        )
        # limpar separadores repetidos
        text = re.sub(r'\s{2,}', ' ', text).strip()
        text = re.sub(r'^[,\-–:;\s]+|[,\-–:;\s]+$', '', text)
        return text


    def _clean_chapter_title(self, text: str) -> str:
        """
        Remove datas/horas PT-BR do final do título, ex.:
        "..., 17 De Janeiro De 2019, 20:19" ou "..., 31 de Dezembro de 2018, 23:07".
        Também remove vírgulas/traços excedentes após a limpeza.
        """
        if not text:
            return text

        # remove prefixo "Volume X " do início
        text = re.sub(r'^\s*volume\s+\d+\s+', '', text, flags=re.I).strip()
        return text
        # datas por extenso (dd de Mês de yyyy, hh:mm opcional)
        meses = ("janeiro|fevereiro|março|marco|abril|maio|junho|julho|agosto|"
                 "setembro|outubro|novembro|dezembro")
        date_suffix = re.compile(
            rf"""(?ix)
                (?:,\s*)?                      # vírgula antes da data (opcional)
                \d{{1,2}}\s+de\s+(?:{meses})\s+de\s+\d{{4}}  # 17 de Janeiro de 2019
                (?:,\s*\d{{2}}:\d{{2}})?       # , 20:19 (opcional)
                \s*$
            """
        )
        text = date_suffix.sub("", text).strip()

        # datas numéricas comuns: dd/mm/yyyy ou dd-mm-yyyy (com hora opcional)
        numeric_suffix = re.compile(r"""(?ix)(?:[,–-]\s*)?\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}(?:,\s*\d{2}:\d{2})?\s*$""")
        text = numeric_suffix.sub("", text).strip()

        # limpa separadores finais redundantes
        text = re.sub(r"[,\-\–]\s*$", "", text).strip()
        return text
    def _load_chapters_try_variants(self) -> bool:
        """Tenta abrir variantes típicas de URL/estado de aba para forçar
        o servidor a retornar a seção de capítulos renderizada no HTML."""
        variants = []
        u = self.novel_url.rstrip("/")
        variants.append(u + "?tab=chapters")
        variants.append(u + "&tab=chapters")
        variants.append(u + "#capitulos")
        variants.append(u + "#chapters")

        for url in variants:
            try:
                soup = self.get_soup(url)
                if self._parse_chapter_table(soup):
                    return True
            except Exception as e:
                logger.debug("Variant %s falhou: %s", url, e)
        return False

    def _load_chapters_from_html(self, soup: BeautifulSoup) -> None:
        self._parse_chapter_table(soup)

    def _parse_chapter_table(self, soup: BeautifulSoup) -> bool:
        """
        Extrai volumes e capítulos de uma estrutura tipo acordeão.
        Corrigido para:
          - limpar listas antes de popular
          - garantir apenas UM header por número de volume
          - mapear o corpo do acordeão de forma estável
          - deduplicar capítulos por URL
        """
        # zera listas
        self.volumes = []
        self.chapters = []

        volume_header_re = re.compile(r"(?i)\bvolume\s*(\d+)\b")

        # Coleta cabeçalhos candidatos
        candidates = soup.select(
            "button, .accordion-button, .card-header, "
            ".collapse-header, .volume-title, h2, h3, "
            ".MuiAccordionSummary-content"
        )

        # Mapa num->(title, body_tag)
        headers_map = {}
        for hdr in candidates:
            text = hdr.get_text(" ", strip=True)
            m = volume_header_re.search(text or "")
            if not m:
                continue
            num = int(m.group(1))
            if num in headers_map:
                # já temos esse volume mapeado; pula duplicatas
                continue

            # encontra o corpo correspondente
            body = None
            target = hdr.get("data-bs-target") or hdr.get("data-target") or hdr.get("aria-controls")
            if target:
                tid = target[1:] if target.startswith("#") else target
                body = soup.find(id=tid)
            if body is None:
                # heurística: próximo irmão com links
                sib = hdr.find_next_sibling()
                jumps = 0
                while sib and jumps < 5 and not sib.select("a[href]"):
                    sib = sib.find_next_sibling()
                    jumps += 1
                body = sib or hdr.parent

            headers_map[num] = (f"Volume {num}", body)

        # Fallback: estrutura Material-UI
        if not headers_map:
            for acc in soup.select(".MuiAccordion-root"):
                head = acc.select_one(".MuiAccordionSummary-content")
                text = head.get_text(" ", strip=True) if head else ""
                m = volume_header_re.search(text or "")
                if not m:
                    continue
                num = int(m.group(1))
                if num in headers_map:
                    continue
                headers_map[num] = (f"Volume {num}", acc)

        
        # Fallback 2: aceitar QUALQUER cabeçalho como uma seção/volume
        if not headers_map:
            idx = 0
            for hdr in candidates:
                title = (hdr.get_text(" ", strip=True) or "").strip() or f"Seção {idx+1}"
                # tenta localizar o corpo do acordeão como antes
                body = None
                target = hdr.get("data-bs-target") or hdr.get("data-target") or hdr.get("aria-controls")
                if target:
                    tid = target[1:] if target.startswith("#") else target
                    body = soup.find(id=tid)
                if body is None:
                    # heurística: próximo irmão com links
                    sib = hdr.find_next_sibling()
                    jumps = 0
                    while sib and jumps < 5 and not sib.select("a[href]"):
                        sib = sib.find_next_sibling()
                        jumps += 1
                    body = sib or hdr.parent
                headers_map[idx] = (title, body)
                idx += 1
# Ordena por número do volume
        ordered = sorted(headers_map.items(), key=lambda kv: kv[0])

        seen_urls = set()
        for _, (title, body) in ordered:
            vol_id = len(self.volumes) + 1
            self.volumes.append({"id": vol_id, "title": title})

            links = body.select("a[href]") if body else []
            for a in links:
                href = (a.get("href") or "").strip()
                text = a.get_text(" ", strip=True)
                if not href or not text:
                    continue
                if not re.search(r"/cap(itulo|tulo)|/chapter|/cap-", href, re.I):
                    continue
                full = self.absolute_url(href)
                if full in seen_urls:
                    continue
                seen_urls.add(full)
                self.chapters.append({
                    "id": len(self.chapters) + 1,
                    "volume": vol_id,
                    "title": self._clean_chapter_title(self._strip_dates_anywhere(text)),
                    "url": full,
                })

        # Fallback bruto: caso nenhuma estrutura de volume seja detectada
        if not self.chapters:
            links = soup.select("a[href]")
            for a in links:
                href = (a.get("href") or "").strip()
                text = a.get_text(" ", strip=True)
                if not href or not text:
                    continue
                if not re.search(r"/cap(itulo|tulo)|/chapter|/cap-", href, re.I):
                    continue
                full = self.absolute_url(href)
                if not self.volumes:
                    self.volumes = [{"id": 1, "title": "Volume 1"}]
                if full in seen_urls:
                    continue
                seen_urls.add(full)
                self.chapters.append({
                    "id": len(self.chapters) + 1,
                    "volume": 1,
                    "title": self._clean_chapter_title(self._strip_dates_anywhere(text)),
                    "url": full,
                })

        return len(self.chapters) > 0


# Registro
Crawler = Novelmania
