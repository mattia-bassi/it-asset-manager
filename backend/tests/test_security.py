import pytest
from app.core.security import hash_password, verify_password

def test_hash_password_valid():
    """Test that valid password is hashed correctly."""
    password = "testpassword123"
    hashed = hash_password(password)
    assert hashed != password
    assert hashed.startswith("$argon2")

def test_hash_password_empty():
    """Test that empty password raises ValueError."""
    with pytest.raises(ValueError, match="cannot be empty"):
        hash_password("")

def test_hash_password_short():
    """Test that password shorter than 8 chars raises ValueError."""
    with pytest.raises(ValueError, match="at least 8 characters"):
        hash_password("short")

def test_hash_password_whitespace_stripped():
    """Test that whitespace is stripped before validation."""
    password = "  testpass123  "
    hashed = hash_password(password)
    # Should hash the stripped version
    assert verify_password("testpass123", hashed)
    assert not verify_password("  testpass123  ", hashed)

def test_verify_password_correct():
    """Test that correct password verifies successfully."""
    password = "testpassword123"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True

def test_verify_password_incorrect():
    """Test that incorrect password fails verification."""
    password = "testpassword123"
    hashed = hash_password(password)
    assert verify_password("wrongpassword", hashed) is False

def test_verify_password_empty():
    """Test that empty password fails verification."""
    password = "testpassword123"
    hashed = hash_password(password)
    assert verify_password("", hashed) is False

def test_hash_and_verify_ok():
    """Test hash and verify cycle works correctly."""
    password = "securepassword123"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False

def test_wrong_password_fails():
    """Test that wrong password fails verification."""
    password = "correctpassword123"
    wrong_password = "wrongpassword456"
    hashed = hash_password(password)
    assert verify_password(wrong_password, hashed) is False

def test_long_password_over_200_chars_supported():
    """Test that passwords over 200 characters are supported (no 72-byte limit)."""
    long_password = "a" * 250  # 250 characters
    hashed = hash_password(long_password)
    assert hashed.startswith("$argon2")
    assert verify_password(long_password, hashed) is True
    assert verify_password(long_password + "x", hashed) is False
