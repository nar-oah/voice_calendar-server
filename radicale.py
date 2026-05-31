from pathlib import Path
import bcrypt
import fcntl


USERS_FILE = Path("/etc/radicale/users")


def add_user(token: str) -> None:
    password = bcrypt.hashpw(token.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    line = f"{token}:{password}\n"
    with USERS_FILE.open("a+", encoding="utf-8") as file:
        fcntl.flock(file, fcntl.LOCK_EX)
        file.write(line)
        fcntl.flock(file, fcntl.LOCK_UN)


if __name__ == "__main__":
    add_user("test")
