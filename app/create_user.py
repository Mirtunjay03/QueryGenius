import getpass
import sys

from email_validator import EmailNotValidError, validate_email

from app import create_app
from app.extensions import db
from app.models import User


def main():
    raw_email = input("User email: ").strip()
    try:
        email = validate_email(raw_email, check_deliverability=False).normalized.lower()
    except EmailNotValidError as exc:
        print(f"Invalid email address: {exc}", file=sys.stderr)
        return 1

    password = getpass.getpass("Password (at least 12 characters): ")
    confirmation = getpass.getpass("Confirm password: ")
    if not 12 <= len(password) <= 128:
        print("Password must contain between 12 and 128 characters.", file=sys.stderr)
        return 1
    if password != confirmation:
        print("Passwords do not match.", file=sys.stderr)
        return 1

    app = create_app()
    with app.app_context():
        existing = db.session.execute(
            db.select(User).filter_by(email=email)
        ).scalar_one_or_none()
        if existing:
            print("A user with that email already exists.", file=sys.stderr)
            return 1

        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"Created user {email}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
