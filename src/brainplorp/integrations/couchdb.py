"""
CouchDB HTTP Client

Handles CouchDB administration tasks like creating databases and users.
"""

import requests
from typing import Dict, Optional
from requests.exceptions import RequestException


class CouchDBError(Exception):
    """Base exception for CouchDB operations."""
    pass


class CouchDBAuthError(CouchDBError):
    """Authentication failed."""
    pass


class CouchDBClient:
    """
    Client for CouchDB administrative operations.

    Used during setup to create databases and configure users.
    """

    def __init__(self, server_url: str, admin_username: str, admin_password: str):
        """
        Initialize CouchDB admin client.

        Args:
            server_url: CouchDB server URL (e.g., https://couch-brainplorp-sync.fly.dev)
            admin_username: CouchDB admin username
            admin_password: CouchDB admin password
        """
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
        self.session.auth = (admin_username, admin_password)
        self.session.headers.update({'Content-Type': 'application/json'})

    def test_connection(self) -> bool:
        """
        Test connection to CouchDB server.

        Returns:
            True if server is accessible and credentials are valid

        Raises:
            CouchDBAuthError: If authentication fails
            CouchDBError: If connection fails
        """
        try:
            response = self.session.get(f"{self.server_url}/")

            if response.status_code == 401:
                raise CouchDBAuthError("Authentication failed - invalid admin credentials")

            response.raise_for_status()
            data = response.json()

            # Verify it's actually CouchDB
            if 'couchdb' not in data:
                raise CouchDBError(f"Server at {self.server_url} is not CouchDB")

            # Ensure system databases exist
            self._ensure_system_databases()

            return True

        except requests.exceptions.ConnectionError as e:
            raise CouchDBError(f"Cannot connect to CouchDB server: {e}")
        except RequestException as e:
            raise CouchDBError(f"CouchDB connection error: {e}")

    def _ensure_system_databases(self) -> None:
        """
        Ensure required system databases exist.

        CouchDB needs _users database for user management.
        """
        system_dbs = ['_users']
        for db in system_dbs:
            if not self.database_exists(db):
                try:
                    self.create_database(db)
                except CouchDBError:
                    # Non-fatal - admin might have restricted permissions
                    pass

    def database_exists(self, database: str) -> bool:
        """
        Check if database exists.

        Args:
            database: Database name

        Returns:
            True if database exists
        """
        try:
            response = self.session.head(f"{self.server_url}/{database}")
            return response.status_code == 200
        except RequestException:
            return False

    def create_database(self, database: str) -> bool:
        """
        Create a new database.

        Args:
            database: Database name

        Returns:
            True if created or already exists

        Raises:
            CouchDBError: If creation fails
        """
        try:
            response = self.session.put(f"{self.server_url}/{database}")

            if response.status_code == 201:
                # Successfully created
                return True
            elif response.status_code == 412:
                # Already exists
                return True
            else:
                response.raise_for_status()
                return True

        except RequestException as e:
            raise CouchDBError(f"Failed to create database '{database}': {e}")

    def create_user(self, username: str, password: str, roles: Optional[list] = None) -> bool:
        """
        Create a CouchDB user.

        Args:
            username: Username
            password: Password
            roles: List of roles (default: empty list)

        Returns:
            True if created successfully

        Raises:
            CouchDBError: If user creation fails
        """
        if roles is None:
            roles = []

        user_doc = {
            "_id": f"org.couchdb.user:{username}",
            "name": username,
            "password": password,
            "roles": roles,
            "type": "user"
        }

        try:
            response = self.session.put(
                f"{self.server_url}/_users/org.couchdb.user:{username}",
                json=user_doc
            )

            if response.status_code in (201, 202):
                return True
            elif response.status_code == 409:
                # User already exists - update password
                return self._update_user_password(username, password, roles)
            else:
                response.raise_for_status()
                return True

        except RequestException as e:
            raise CouchDBError(f"Failed to create user '{username}': {e}")

    def _update_user_password(self, username: str, password: str, roles: list) -> bool:
        """
        Update existing user's password.

        Args:
            username: Username
            password: New password
            roles: User roles

        Returns:
            True if updated

        Raises:
            CouchDBError: If update fails
        """
        try:
            # Get current user document
            response = self.session.get(
                f"{self.server_url}/_users/org.couchdb.user:{username}"
            )
            response.raise_for_status()
            user_doc = response.json()

            # Update password
            user_doc['password'] = password
            user_doc['roles'] = roles

            # Save updated document
            response = self.session.put(
                f"{self.server_url}/_users/org.couchdb.user:{username}",
                json=user_doc
            )
            response.raise_for_status()
            return True

        except RequestException as e:
            raise CouchDBError(f"Failed to update user '{username}': {e}")

    def grant_database_access(self, database: str, username: str) -> bool:
        """
        Grant user full access to database.

        Args:
            database: Database name
            username: Username to grant access

        Returns:
            True if access granted

        Raises:
            CouchDBError: If grant fails
        """
        try:
            # Get current security document
            response = self.session.get(f"{self.server_url}/{database}/_security")

            if response.status_code == 200:
                security_doc = response.json()
            else:
                # Create new security document
                security_doc = {
                    "admins": {"names": [], "roles": []},
                    "members": {"names": [], "roles": []}
                }

            # Ensure security_doc has proper structure
            if "admins" not in security_doc:
                security_doc["admins"] = {"names": [], "roles": []}
            if "members" not in security_doc:
                security_doc["members"] = {"names": [], "roles": []}

            # Ensure members has names and roles keys
            if "names" not in security_doc["members"]:
                security_doc["members"]["names"] = []
            if "roles" not in security_doc["members"]:
                security_doc["members"]["roles"] = []

            # Ensure admins has names and roles keys
            if "names" not in security_doc["admins"]:
                security_doc["admins"]["names"] = []
            if "roles" not in security_doc["admins"]:
                security_doc["admins"]["roles"] = []

            # Add user to members (can read/write)
            if username not in security_doc["members"]["names"]:
                security_doc["members"]["names"].append(username)

            # Save updated security document
            response = self.session.put(
                f"{self.server_url}/{database}/_security",
                json=security_doc
            )
            response.raise_for_status()
            return True

        except RequestException as e:
            raise CouchDBError(f"Failed to grant access for '{username}' to '{database}': {e}")

    def setup_vault_database(self, database: str, username: str, password: str) -> bool:
        """
        Complete setup: create database, create user, grant access.

        Args:
            database: Database name (e.g., user-jsd-vault)
            username: Username
            password: Password

        Returns:
            True if setup completed successfully

        Raises:
            CouchDBError: If any step fails
        """
        # Create database
        self.create_database(database)

        # Create user
        self.create_user(username, password, roles=[])

        # Grant user access to database
        self.grant_database_access(database, username)

        return True
