import logging
import os
import re
import subprocess
import time

try:
    from curl_cffi import requests as cffi_requests
except ImportError:
    cffi_requests = None

from .base import DEFAULT_HEADERS, SDSSource

logger = logging.getLogger("organilab")

# Merck/Sigma-Aldrich SDS search and download.
# sigmaaldrich.com uses anti-bot protection that detects TLS fingerprints.
# We use curl_cffi with Chrome impersonation to bypass this blocking.
# The search uses the Sigma-Aldrich website to find product numbers by CAS,
# then downloads the SDS PDF using the product number.

SEARCH_URL = (
    "https://www.sigmaaldrich.com/CR/es/search/{cas}"
    "?focus=products&page=1&perpage=5&sort=relevance&term={cas}&type=cas_number"
)

SDS_URL = "https://www.sigmaaldrich.com/CR/es/sds/{brand}/{product_number}"

IMPERSONATE = "chrome131"
MAX_RETRIES = 1
RETRY_DELAY = 3
MAX_PRODUCTS_TO_TRY = 15
BRAND_SLUGS = ['sial', 'aldrich', 'mm', 'sigma', 'supelco']

# Pattern to find brandKey/productNumber pairs close together in JSON
BRAND_THEN_PRODUCT = re.compile(
    r'"brandKey"\s*:\s*"([^"]+)"'
    r'(?:(?!"brandKey").){0,500}'
    r'"productNumber"\s*:\s*"([^"]+)"',
    re.DOTALL,
)

# Patterns to extract product number and brand from existing SDS PDF text
# Spanish format: "Referencia  : 49148-U"
PDF_PRODUCT_ES = re.compile(r'[Rr]eferencia\s*:\s*(\S+)')
PDF_BRAND_ES = re.compile(r'[Mm]arca\s*:\s*(.+)')
# English format: values appear as ": VALUE" after "Product Number" and "Brand" labels
PDF_PRODUCT_EN = re.compile(r'Product\s+Number')
PDF_BRAND_EN = re.compile(r'Brand')

# Map brand names found in PDFs to URL slugs used by sigmaaldrich.com
BRAND_SLUG_MAP = {
    'sigma-aldrich': 'sial',
    'sigma': 'sial',
    'aldrich': 'aldrich',
    'supelco': 'supelco',
    'merck': 'mm',
    'millipore': 'mm',
    'milliporesigma': 'mm',
    'fluka': 'sial',
    'emt': 'mm',
}


def _brand_to_slug(brand_name):
    """Convert a brand name from the PDF to the URL slug."""
    key = brand_name.strip().lower()
    return BRAND_SLUG_MAP.get(key, key)


class MerckSource(SDSSource):
    name = "merck"
    timeout = 45

    def _get_cffi_session(self):
        session = cffi_requests.Session(impersonate=IMPERSONATE)
        session.headers.update(DEFAULT_HEADERS)
        return session

    def _request_with_retry(self, session, url, **kwargs):
        """Make a request with one retry on timeout."""
        for attempt in range(MAX_RETRIES + 1):
            try:
                return session.get(url, timeout=self.timeout, **kwargs)
            except cffi_requests.errors.RequestsError:
                if attempt < MAX_RETRIES:
                    logger.debug("[merck] Timeout for %s, retrying in %ds...", url, RETRY_DELAY)
                    time.sleep(RETRY_DELAY)
                else:
                    raise

    def _extract_product_from_pdf(self, pdf_path):
        """Extract product number and brand from an existing SDS PDF.

        Sigma-Aldrich PDFs have labels (Product Number/Referencia, Brand/Marca)
        and values (": VALUE") on separate lines in Section 1. We detect the
        labels and then collect colon-prefixed values in order.

        Returns (product_number, brand_slug) or (None, None).
        """
        try:
            result = subprocess.run(
                ['pdftotext', '-l', '1', '-q', pdf_path, '-'],
                capture_output=True, text=True, timeout=15,
            )
            text = result.stdout
        except Exception:
            return None, None

        if not text.strip():
            return None, None

        # First try same-line format: "Referencia  : VALUE" / "Marca  : VALUE"
        product_number = None
        brand = None
        m = PDF_PRODUCT_ES.search(text)
        if m:
            product_number = m.group(1).strip()
        m = PDF_BRAND_ES.search(text)
        if m:
            brand = m.group(1).strip()

        if product_number and brand:
            slug = _brand_to_slug(brand)
            logger.debug("[merck] Extracted from PDF (inline): product=%s, brand=%s (slug=%s)",
                         product_number, brand, slug)
            return product_number, slug

        # Separate-line format: labels and ": value" on different lines.
        # pdftotext may reorder two-column layouts, so labels (Referencia, Marca)
        # and their values (: 49148-U, : Supelco) can appear far apart.
        # Strategy: find all labels and all colon-values in the first page,
        # then match by position order.
        lines = text.split('\n')
        has_product_label = False
        has_brand_label = False
        colon_values = []

        for line in lines:
            stripped = line.strip()

            # Detect labels (English or Spanish)
            if PDF_PRODUCT_EN.search(stripped) or stripped == 'Referencia':
                has_product_label = True
            elif PDF_BRAND_EN.search(stripped) or stripped == 'Marca':
                has_brand_label = True
            elif stripped.startswith(':') and len(stripped) > 1:
                colon_values.append(stripped[1:].strip())

            # Stop at Section 2
            if re.search(r'SECCI[OÓ]N\s+2|SECTION\s+2', stripped):
                break

        # Colon values order varies between Spanish and English PDFs.
        # Identify brand by matching known brand names, and product number
        # as the short alphanumeric value that isn't a brand or CAS number.
        if has_product_label and has_brand_label and len(colon_values) >= 2:
            detected_brand = None
            detected_product = None

            for val in colon_values[:5]:
                val_lower = val.strip().lower()
                # Check if it's a known brand
                if not detected_brand and val_lower in BRAND_SLUG_MAP:
                    detected_brand = val.strip()
                    continue
                # Check for hyphenated brand names (e.g. "Sigma-Aldrich")
                if not detected_brand and '-' in val_lower and val_lower.replace('-', '') in \
                        {k.replace('-', ''): k for k in BRAND_SLUG_MAP}:
                    detected_brand = val.strip()
                    continue
                # Short alphanumeric value = likely product number
                # Skip CAS numbers (digits-digits-digits) and long text
                if not detected_product and len(val) <= 20 and \
                        not re.match(r'^\d+-\d+-\d+$', val) and \
                        re.match(r'^[\w.\-]+$', val):
                    detected_product = val.strip()

            if detected_product and detected_brand:
                slug = _brand_to_slug(detected_brand)
                logger.debug("[merck] Extracted from PDF (section): product=%s, brand=%s (slug=%s)",
                             detected_product, detected_brand, slug)
                return detected_product, slug

        return None, None

    def search(self, cas_number, substance_name="", pdf_path=None):
        if not cas_number:
            return None

        # Try to extract product info from existing PDF first
        if pdf_path and os.path.exists(pdf_path):
            product_number, brand_slug = self._extract_product_from_pdf(pdf_path)
            if product_number and brand_slug:
                logger.debug("[merck] Using product from PDF: %s/%s", brand_slug, product_number)
                return {
                    'url': None,
                    'products': [(brand_slug, product_number)],
                    'from_pdf': True,
                    'metadata': {
                        'product_number': product_number,
                        'brand': brand_slug,
                        'cas': cas_number,
                    },
                }

        # Fallback: search the website
        url = SEARCH_URL.format(cas=cas_number)
        session = self._get_cffi_session()
        session.headers.update({
            'Referer': 'https://www.sigmaaldrich.com/CR/es',
            'Sec-Fetch-Site': 'same-origin',
        })
        try:
            r = self._request_with_retry(session, url)
            if r.status_code != 200:
                logger.debug("[merck] Search returned HTTP %s for CAS %s", r.status_code, cas_number)
                return None
        except Exception as e:
            logger.warning("[merck] Search error for CAS %s: %s", cas_number, e)
            return None

        # Extract all brand/product pairs from the response
        products = self._extract_products(r.text)
        if not products:
            logger.debug("[merck] No product found for CAS %s", cas_number)
            return None

        return {
            'url': None,  # Will be resolved in download by trying each product
            'products': products,
            'from_pdf': False,
            'metadata': {
                'product_number': products[0][1],
                'brand': products[0][0],
                'cas': cas_number,
            },
        }

    def download(self, search_result, dest_path):
        """Download SDS PDF, trying multiple products until one succeeds."""
        if not search_result:
            return False
        products = search_result.get('products', [])
        cas = search_result.get('metadata', {}).get('cas', '')
        session = self._get_cffi_session()
        session.headers.update({
            'Accept': 'application/pdf,*/*;q=0.8',
            'Referer': SEARCH_URL.format(cas=cas) if cas else 'https://www.sigmaaldrich.com/CR/es',
            'Sec-Fetch-Site': 'same-origin',
        })

        for brand, product_number in products[:MAX_PRODUCTS_TO_TRY]:
            url = SDS_URL.format(brand=brand.lower(), product_number=product_number)
            try:
                r = self._request_with_retry(session, url)
                if r.status_code != 200:
                    logger.debug("[merck] SDS HTTP %s for %s/%s", r.status_code, brand, product_number)
                    continue
                with open(dest_path, 'wb') as f:
                    f.write(r.content)
                if self._is_valid_pdf(dest_path):
                    logger.debug("[merck] Found SDS at %s/%s", brand, product_number)
                    search_result['url'] = url
                    return True
                else:
                    logger.debug("[merck] Not a valid PDF: %s/%s", brand, product_number)
                    os.remove(dest_path)
            except Exception as e:
                logger.debug("[merck] Download error for %s/%s: %s", brand, product_number, e)
                if os.path.exists(dest_path):
                    os.remove(dest_path)

        logger.warning("[merck] No SDS PDF found for CAS %s after trying %d products",
                       cas, min(len(products), MAX_PRODUCTS_TO_TRY))
        return False

    def _extract_products(self, html):
        """Extract (brand, product_number) pairs from the search page.

        Uses two strategies:
        1. The original regex that finds adjacent brandKey/productNumber pairs.
        2. Extracts all productNumbers independently and pairs each with all
           known brand slugs, since brandKey and productNumber often appear in
           separate JSON sections and the regex misses them.

        Returns a list of unique pairs, deduplicated and preserving order.
        """
        seen = set()
        products = []

        # Strategy 1: adjacent brandKey/productNumber pairs (original regex)
        for m in BRAND_THEN_PRODUCT.finditer(html):
            brand, product = m.group(1).lower(), m.group(2)
            key = (brand, product)
            if key not in seen:
                seen.add(key)
                products.append(key)

        # Strategy 2: extract all productNumbers and pair with all brand slugs
        all_pn = set(re.findall(r'"productNumber"\s*:\s*"([^"]+)"', html))
        for pn in all_pn:
            for slug in BRAND_SLUGS:
                key = (slug, pn)
                if key not in seen:
                    seen.add(key)
                    products.append(key)

        return products
