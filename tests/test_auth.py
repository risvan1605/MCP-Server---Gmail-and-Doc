"""Tests for the OAuth authentication module."""

from unittest.mock import MagicMock, patch

import pytest

from google_mcp_server.auth.oauth import (
    get_credentials,
    get_docs_service,
    get_gmail_service,
    reset_services,
)


class TestGetCredentials:
    """Tests for the get_credentials function."""

    def setup_method(self):
        """Reset cached services before each test."""
        reset_services()

    @patch("google_mcp_server.auth.oauth.TOKEN_PATH")
    @patch("google_mcp_server.auth.oauth.CREDENTIALS_PATH")
    def test_raises_when_no_credentials_file(self, mock_creds_path, mock_token_path):
        """Should raise FileNotFoundError if credentials.json is missing."""
        mock_token_path.exists.return_value = False
        mock_creds_path.exists.return_value = False

        with pytest.raises(FileNotFoundError, match="credentials file not found"):
            get_credentials()

    @patch("google_mcp_server.auth.oauth.Credentials")
    @patch("google_mcp_server.auth.oauth.TOKEN_PATH")
    def test_loads_cached_valid_token(self, mock_token_path, mock_creds_cls):
        """Should load and return a valid cached token."""
        mock_token_path.exists.return_value = True

        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_creds.expired = False
        mock_creds_cls.from_authorized_user_file.return_value = mock_creds

        result = get_credentials()

        assert result == mock_creds
        mock_creds_cls.from_authorized_user_file.assert_called_once()

    @patch("google_mcp_server.auth.oauth._save_token")
    @patch("google_mcp_server.auth.oauth.Request")
    @patch("google_mcp_server.auth.oauth.Credentials")
    @patch("google_mcp_server.auth.oauth.TOKEN_PATH")
    def test_refreshes_expired_token(
        self, mock_token_path, mock_creds_cls, mock_request, mock_save
    ):
        """Should refresh an expired token that has a refresh_token."""
        mock_token_path.exists.return_value = True

        mock_creds = MagicMock()
        mock_creds.valid = False
        mock_creds.expired = True
        mock_creds.refresh_token = "refresh_token_value"
        mock_creds_cls.from_authorized_user_file.return_value = mock_creds

        # After refresh, creds become valid
        def make_valid(request):
            mock_creds.valid = True
            mock_creds.expired = False

        mock_creds.refresh.side_effect = make_valid

        result = get_credentials()

        assert result == mock_creds
        mock_creds.refresh.assert_called_once()
        mock_save.assert_called_once_with(mock_creds)


class TestServiceBuilders:
    """Tests for get_gmail_service and get_docs_service."""

    def setup_method(self):
        """Reset cached services before each test."""
        reset_services()

    @patch("google_mcp_server.auth.oauth.build")
    @patch("google_mcp_server.auth.oauth.get_credentials")
    def test_get_gmail_service_builds_once(self, mock_get_creds, mock_build):
        """Should build the Gmail service once and cache it."""
        mock_creds = MagicMock()
        mock_get_creds.return_value = mock_creds
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        result1 = get_gmail_service()
        result2 = get_gmail_service()

        assert result1 == mock_service
        assert result2 == mock_service
        mock_build.assert_called_once_with("gmail", "v1", credentials=mock_creds)

    @patch("google_mcp_server.auth.oauth.build")
    @patch("google_mcp_server.auth.oauth.get_credentials")
    def test_get_docs_service_builds_once(self, mock_get_creds, mock_build):
        """Should build the Docs service once and cache it."""
        mock_creds = MagicMock()
        mock_get_creds.return_value = mock_creds
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        result1 = get_docs_service()
        result2 = get_docs_service()

        assert result1 == mock_service
        assert result2 == mock_service
        mock_build.assert_called_once_with("docs", "v1", credentials=mock_creds)

    @patch("google_mcp_server.auth.oauth.build")
    @patch("google_mcp_server.auth.oauth.get_credentials")
    def test_reset_services_clears_cache(self, mock_get_creds, mock_build):
        """Should clear cached services so they rebuild on next call."""
        mock_get_creds.return_value = MagicMock()
        mock_build.return_value = MagicMock()

        get_gmail_service()
        reset_services()
        get_gmail_service()

        assert mock_build.call_count == 2
