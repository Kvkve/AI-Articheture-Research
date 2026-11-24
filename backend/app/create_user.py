"""Create a user from the command line.

Run from the backend folder:

    uv run python -m app.create_user <username>

The password is asked for twice and is never a command-line argument, because
arguments stay in the shell history.
"""

import argparse
import sys
from getpass import getpass

from app.config import Settings
from app.database import connect, create_tables
from app.users import InvalidUserError, UserExistsError, create_user


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a user of the backend.")
    parser.add_argument("username", help="the name the user signs in with")
    username = parser.parse_args(arguments).username

    password = getpass("Password: ")
    password_again = getpass("Password again: ")
    if password != password_again:
        print("The two passwords differ. No user was created.", file=sys.stderr)
        return 1

    settings = Settings()
    connection = connect(settings.database_file)
    try:
        # The tables may not exist yet if the backend has never started.
        create_tables(connection)
        create_user(connection, username, password)
    except (InvalidUserError, UserExistsError) as error:
        print(f"{error} No user was created.", file=sys.stderr)
        return 1
    finally:
        connection.close()

    print(f"Created the user {username.strip()!r}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
