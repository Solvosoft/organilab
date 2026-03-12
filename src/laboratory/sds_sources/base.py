import logging
import os
import tempfile

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger("organilab")

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
              'image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'es-CR,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Sec-Ch-Ua': '"Chromium";v="131", "Not_A Brand";v="24"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Linux"',
    'DNT': '1',
}

RETRY_STRATEGY = Retry(
    total=2,
    backoff_factor=3,
    status_forcelist=[429, 500, 502, 503],
)


class SDSSource:
    """Base class for SDS (Safety Data Sheet) download sources."""

    name = "base"
    timeout = 30

    def search(self, cas_number, substance_name="", pdf_path=None):
        """Search for an SDS by CAS number and/or substance name.

        Args:
            cas_number: CAS number to search for
            substance_name: optional substance name for fallback searches
            pdf_path: optional path to existing SDS PDF for metadata extraction

        Returns a dict with at least {'url': ..., 'metadata': {...}} or None if not found.
        """
        raise NotImplementedError

    def download(self, search_result, dest_path):
        """Download the SDS PDF to dest_path.

        Returns True if the download was successful and the file is a valid PDF.
        """
        url = search_result.get('url')
        if not url:
            return False
        try:
            session = self._get_session()
            session.headers['Accept'] = 'application/pdf,*/*;q=0.8'
            r = session.get(url, timeout=self.timeout, stream=True)
            if r.status_code != 200:
                logger.warning("[%s] Download failed: HTTP %s for %s", self.name, r.status_code, url)
                return False
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            if not self._is_valid_pdf(dest_path):
                logger.warning("[%s] Downloaded file is not a valid PDF: %s", self.name, url)
                os.remove(dest_path)
                return False
            return True
        except requests.RequestException as e:
            logger.warning("[%s] Download error for %s: %s", self.name, url, e)
            if os.path.exists(dest_path):
                os.remove(dest_path)
            return False

    def _is_valid_pdf(self, path):
        try:
            with open(path, 'rb') as f:
                header = f.read(5)
            return header == b'%PDF-'
        except Exception:
            return False

    def _get_session(self):
        session = requests.Session()
        session.headers.update(DEFAULT_HEADERS)
        adapter = HTTPAdapter(max_retries=RETRY_STRATEGY)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session
