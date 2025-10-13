"""
Vault Client - CouchDB HTTP API Access for Server Automation

Provides HTTP API access to vault documents stored in CouchDB.
Used by brainplorp server for automation (email fetch, analytics, etc.)
"""

import time
import requests
from typing import Callable, Dict, List, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import quote


class VaultUpdateConflictError(Exception):
    """MVCC conflict that couldn't be resolved after all retries."""
    pass


class VaultDocumentNotFoundError(Exception):
    """Requested document does not exist."""
    pass


class VaultClient:
    """
    HTTP client for accessing vault documents in CouchDB.

    Handles MVCC conflicts with automatic retry and exponential backoff.
    Designed for server-side automation tasks.
    """

    def __init__(self, server_url: str, database: str, username: str, password: str):
        """
        Initialize vault client.

        Args:
            server_url: CouchDB server URL (e.g., https://couch-brainplorp-sync.fly.dev)
            database: Database name (e.g., user-jsd-vault)
            username: CouchDB username
            password: CouchDB password
        """
        self.server_url = server_url.rstrip('/')
        self.database = database
        self.base_url = f"{self.server_url}/{database}"

        # Setup session with connection pooling
        self.session = requests.Session()

        # Connection pooling: 10 connections with keep-alive
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=Retry(total=3, backoff_factor=0.3)
        )
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)

        # Authentication
        self.session.auth = (username, password)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def read_document(self, path: str) -> Dict:
        """
        Read a vault document.

        Args:
            path: Document path (e.g., "daily/2025-10-12.md")

        Returns:
            Document dict with _id, _rev, content, mtime, etc.

        Raises:
            VaultDocumentNotFoundError: If document doesn't exist
            requests.RequestException: If HTTP request fails
        """
        # URL-encode the path for CouchDB
        doc_id = quote(path, safe='')

        response = self.session.get(f"{self.base_url}/{doc_id}")

        if response.status_code == 404:
            raise VaultDocumentNotFoundError(f"Document not found: {path}")

        response.raise_for_status()
        return response.json()

    def write_document(self, path: str, content: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Write a new document or overwrite existing one.

        WARNING: This does NOT handle MVCC conflicts.
        Use update_document() for safe updates.

        Args:
            path: Document path (e.g., "inbox/2025-10.md")
            content: Document content (markdown text)
            metadata: Optional metadata (mtime, ctime, etc.)

        Returns:
            CouchDB response with ok, id, rev

        Raises:
            requests.RequestException: If write fails
        """
        doc_id = quote(path, safe='')

        doc = {
            "_id": doc_id,
            "type": "markdown",
            "path": path,
            "content": content,
        }

        if metadata:
            doc.update(metadata)

        # Try to get existing revision
        try:
            existing = self.read_document(path)
            doc["_rev"] = existing["_rev"]
        except VaultDocumentNotFoundError:
            pass  # New document, no revision needed

        response = self.session.put(f"{self.base_url}/{doc_id}", json=doc)
        response.raise_for_status()
        return response.json()

    def update_document(
        self,
        path: str,
        update_fn: Callable[[str], str],
        max_retries: int = 4
    ) -> Dict:
        """
        Update document with MVCC conflict retry.

        Implements exponential backoff retry strategy for handling
        concurrent updates from multiple clients.

        Args:
            path: Document path
            update_fn: Function that takes current content and returns updated content
            max_retries: Maximum number of retries (default: 4)

        Returns:
            CouchDB response after successful update

        Raises:
            VaultUpdateConflictError: If max retries exceeded
            VaultDocumentNotFoundError: If document doesn't exist
            requests.RequestException: If HTTP request fails

        Example:
            >>> def add_task(content):
            ...     return content + "\\n- [ ] New task"
            >>> client.update_document("inbox/2025-10.md", add_task)
        """
        for attempt in range(max_retries + 1):  # +1 for initial attempt
            try:
                # Read current document
                doc = self.read_document(path)
                current_rev = doc['_rev']
                current_content = doc.get('content', '')

                # Apply update function
                updated_content = update_fn(current_content)

                # Prepare updated document
                doc['content'] = updated_content
                doc['_rev'] = current_rev

                # Attempt to save
                doc_id = quote(path, safe='')
                response = self.session.put(f"{self.base_url}/{doc_id}", json=doc)

                if response.status_code == 409:
                    # Conflict - another client updated the document
                    if attempt < max_retries:
                        # Exponential backoff: 100ms, 200ms, 400ms, 800ms
                        delay = 0.1 * (2 ** attempt)
                        time.sleep(delay)
                        continue  # Retry
                    else:
                        # Max retries exceeded
                        raise VaultUpdateConflictError(
                            f"MVCC conflict after {max_retries + 1} attempts for document: {path}"
                        )

                response.raise_for_status()
                return response.json()

            except VaultDocumentNotFoundError:
                # Document doesn't exist - cannot update non-existent document
                raise

            except requests.RequestException as e:
                # HTTP error (not conflict) - don't retry
                raise

        # Should never reach here
        raise VaultUpdateConflictError(f"Unexpected error updating document: {path}")

    def list_documents(self, prefix: str = "") -> List[str]:
        """
        List all documents in vault, optionally filtered by prefix.

        Args:
            prefix: Only return documents starting with this prefix (e.g., "daily/")

        Returns:
            List of document IDs (paths)

        Example:
            >>> client.list_documents("daily/")
            ['daily/2025-10-01.md', 'daily/2025-10-02.md', ...]
        """
        response = self.session.get(f"{self.base_url}/_all_docs")
        response.raise_for_status()
        data = response.json()

        doc_ids = [row['id'] for row in data['rows'] if not row['id'].startswith('_')]

        if prefix:
            doc_ids = [doc_id for doc_id in doc_ids if doc_id.startswith(prefix)]

        return doc_ids

    def batch_read(self, paths: List[str]) -> Dict[str, Dict]:
        """
        Read multiple documents in a single request.

        More efficient than multiple individual reads.

        Args:
            paths: List of document paths

        Returns:
            Dict mapping path to document content

        Example:
            >>> client.batch_read(["daily/2025-10-01.md", "daily/2025-10-02.md"])
            {
                "daily/2025-10-01.md": {...document...},
                "daily/2025-10-02.md": {...document...}
            }
        """
        # URL-encode paths for CouchDB
        keys = [quote(path, safe='') for path in paths]

        response = self.session.post(
            f"{self.base_url}/_all_docs",
            json={"keys": keys, "include_docs": True}
        )
        response.raise_for_status()
        data = response.json()

        results = {}
        for row in data['rows']:
            if 'doc' in row:
                # Successfully fetched document
                doc = row['doc']
                results[doc['path']] = doc

        return results

    def document_exists(self, path: str) -> bool:
        """
        Check if document exists.

        Args:
            path: Document path

        Returns:
            True if document exists
        """
        try:
            self.read_document(path)
            return True
        except VaultDocumentNotFoundError:
            return False

    def delete_document(self, path: str) -> Dict:
        """
        Delete a document.

        Args:
            path: Document path

        Returns:
            CouchDB response

        Raises:
            VaultDocumentNotFoundError: If document doesn't exist
        """
        doc = self.read_document(path)
        doc_id = quote(path, safe='')

        response = self.session.delete(
            f"{self.base_url}/{doc_id}",
            params={"rev": doc["_rev"]}
        )
        response.raise_for_status()
        return response.json()
