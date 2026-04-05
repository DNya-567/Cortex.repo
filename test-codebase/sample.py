"""User management module with authentication."""


def validate_email(email: str) -> bool:
    """Validate email format."""
    return "@" in email and "." in email.split("@")[1]


def hash_password(password: str) -> str:
    """Hash password for storage."""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()


class User:
    """Represents a user in the system."""

    def __init__(self, username: str, email: str, password: str):
        """Initialize a new user."""
        self.username = username
        self.email = email
        self.password_hash = hash_password(password)
        self.is_active = True

    def verify_password(self, password: str) -> bool:
        """Verify if provided password matches stored hash."""
        return hash_password(password) == self.password_hash

    def deactivate(self):
        """Deactivate the user account."""
        self.is_active = False


class UserRepository:
    """Repository for managing user persistence."""

    def __init__(self):
        """Initialize the repository."""
        self.users = {}

    def add_user(self, user: User) -> bool:
        """Add a new user to the repository."""
        if user.username in self.users:
            return False
        self.users[user.username] = user
        return True

    def get_user(self, username: str) -> User | None:
        """Get a user by username."""
        return self.users.get(username)

    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate a user."""
        user = self.get_user(username)
        if user is None or not user.is_active:
            return False
        return user.verify_password(password)


def create_default_users() -> UserRepository:
    """Create default users for testing."""
    repo = UserRepository()
    user1 = User("alice", "alice@example.com", "password123")
    user2 = User("bob", "bob@example.com", "secure456")
    repo.add_user(user1)
    repo.add_user(user2)
    return repo

