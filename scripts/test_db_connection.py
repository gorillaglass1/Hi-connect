import asyncio
import socket
import sys
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import DB_URL, engine


def _target() -> dict:
    return {
        "driver": getattr(DB_URL, "drivername", str(DB_URL).split(":", 1)[0]),
        "host": getattr(DB_URL, "host", None),
        "port": getattr(DB_URL, "port", None),
        "username": getattr(DB_URL, "username", None),
        "database": getattr(DB_URL, "database", None),
    }


def _connection_kind(host: str | None, port: int | None, username: str | None) -> str:
    if host is None:
        return "unknown"
    if ".pooler.supabase.com" in host and port == 5432:
        return "supabase session pooler"
    if ".pooler.supabase.com" in host and port == 6543:
        return "supabase transaction pooler"
    if host.startswith("db.") and host.endswith(".supabase.co"):
        return "supabase direct connection"
    if username and "." in username and "pooler" in host:
        return "supabase pooler"
    return "postgresql"


def _print_diagnosis_for_dns_failure(host: str | None) -> None:
    if host and host.startswith("db.") and host.endswith(".supabase.co"):
        print(
            "Likely cause: this environment cannot resolve the Supabase direct "
            "connection host. Use the Transaction pooler connection string."
        )
        print(
            "Expected pooler shape: "
            "postgresql://postgres.<project-ref>:[비밀번호]@"
            "aws-0-<region>.pooler.supabase.com:6543/postgres"
        )
    else:
        print("Likely cause: host is wrong, not reachable from this network, or DNS is unavailable.")


async def main() -> None:
    target = _target()
    host = target["host"]
    port = target["port"] or 5432

    print("DB target:", target)
    print("Connection kind:", _connection_kind(host, port, target["username"]))

    try:
        addresses = socket.getaddrinfo(host, port)
        print("DNS lookup OK:", addresses[0][4][0])
    except OSError as exc:
        print("DNS lookup failed:", exc)
        _print_diagnosis_for_dns_failure(host)
        raise SystemExit(1) from exc

    try:
        with socket.create_connection((host, port), timeout=5):
            print("TCP connection OK")
    except OSError as exc:
        print("TCP connection failed:", exc)
        print("Likely cause: firewall, blocked port, wrong pooler/direct port, or network routing.")
        raise SystemExit(1) from exc

    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("DB connection OK:", result.scalar_one())
    except Exception as exc:
        print("DB connection failed:", type(exc).__name__, exc)
        message = str(exc)
        if "ENOIDENTIFIER" in message or "no tenant identifier" in message:
            print(
                "Likely cause: Supabase pooler requires the project ref in the "
                "username. Use username like postgres.<project-ref>, not postgres."
            )
            print(
                "For this project, it is likely: postgres.dqbcigpltvtbnxptvyos"
            )
        else:
            print(
                "Likely cause: wrong username/password, wrong database, SSL/pooler "
                "setting, or Supabase project credentials."
            )
        raise SystemExit(1) from exc
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
