# Unit Testing Fundamentals - Start Here!

## What Unit Tests Actually Test

Unit tests test **individual functions** in isolation, without:
- ❌ Databases
- ❌ Network calls  
- ❌ File systems
- ❌ External APIs

## Your Authentication Logic - Unit Testable Functions

Looking at your `app/auth.py`, these are perfect for unit testing:

```python
# These functions can be unit tested easily:
def validate_regno(regno: str) -> Optional[str]
def validate_password(password: str) -> Optional[str]  
def hash_password(password: str) -> str
def verify_password(plain_password: str, hashed_password: str) -> bool
```

## Why Start With Unit Tests?

1. **Fast** - Run in milliseconds
2. **Simple** - No setup/teardown
3. **Reliable** - No external dependencies
4. **Easy to debug** - Test one thing at a time
5. **Great for learning** - Clear cause and effect

## Unit Test Examples

```python
# Fast, simple, reliable
def test_validate_regno_valid():
    error = validate_regno("AB1234567890123")
    assert error is None

def test_validate_regno_too_short():
    error = validate_regno("AB123")
    assert "15 characters" in error

def test_password_hashing():
    password = "SecurePass123!"
    hashed = hash_password(password)
    
    assert hashed != password  # Not plain text
    assert len(hashed) > 50    # Reasonable hash length
    assert verify_password(password, hashed) == True
```

## What You've Been Doing (Integration Tests)

```python
# Slow, complex, many moving parts
def test_user_registration():
    # Involves: FastAPI, database, HTTP, async operations
    response = client.post("/auth/register", json=data)
    assert response.status_code == 200
```

This tests **the entire system working together** - much more complex!
