import sys
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from app.scripts.seed_admin import main

def test_seed_admin_creates_user():
    """Test that seed admin creates user when it doesn't exist."""
    mock_db = MagicMock(spec=Session)
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_first = MagicMock(return_value=None)  # User doesn't exist
    
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first = mock_first
    
    with patch('app.scripts.seed_admin.SessionLocal', return_value=mock_db):
        with patch('app.scripts.seed_admin.settings') as mock_settings:
            mock_settings.admin_username = "admin"
            mock_settings.admin_password = "validpassword123"
            with patch('app.scripts.seed_admin.hash_password') as mock_hash:
                mock_hash.return_value = "$argon2id$v=19$m=65536,t=3,p=4$testhash"
                main()
    
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.close.assert_called_once()
    
    # Verify password_hash is argon2
    added_user = mock_db.add.call_args[0][0]
    assert added_user.password_hash.startswith("$argon2")

def test_seed_admin_skips_if_exists():
    """Test that seed admin skips if user already exists."""
    mock_db = MagicMock(spec=Session)
    mock_query = MagicMock()
    mock_filter = MagicMock()
    existing_user = MagicMock()
    mock_first = MagicMock(return_value=existing_user)  # User exists
    
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first = mock_first
    
    with patch('app.scripts.seed_admin.SessionLocal', return_value=mock_db):
        with patch('app.scripts.seed_admin.settings') as mock_settings:
            mock_settings.admin_username = "admin"
            mock_settings.admin_password = "validpassword123"
            main()
    
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()
    mock_db.close.assert_called_once()

def test_seed_admin_empty_password_exits():
    """Test that seed admin exits with code 1 if password is empty."""
    with patch('app.scripts.seed_admin.settings') as mock_settings:
        mock_settings.admin_password = ""
        mock_settings.admin_username = "admin"
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1

def test_seed_admin_short_password_exits():
    """Test that seed admin exits with code 1 if password is too short."""
    with patch('app.scripts.seed_admin.settings') as mock_settings:
        mock_settings.admin_password = "short"
        mock_settings.admin_username = "admin"
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 1

def test_seed_admin_password_hash_is_argon2():
    """Test that seed admin creates password hash with Argon2 format."""
    mock_db = MagicMock(spec=Session)
    mock_query = MagicMock()
    mock_filter = MagicMock()
    mock_first = MagicMock(return_value=None)
    
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_filter
    mock_filter.first = mock_first
    
    with patch('app.scripts.seed_admin.SessionLocal', return_value=mock_db):
        with patch('app.scripts.seed_admin.settings') as mock_settings:
            mock_settings.admin_username = "admin"
            mock_settings.admin_password = "validpassword123"
            with patch('app.scripts.seed_admin.hash_password') as mock_hash:
                mock_hash.return_value = "$argon2id$v=19$m=65536,t=3,p=4$testhash"
                main()
    
    # Verify the hash_password was called and result is argon2
    mock_hash.assert_called()
    added_user = mock_db.add.call_args[0][0]
    assert added_user.password_hash.startswith("$argon2")
