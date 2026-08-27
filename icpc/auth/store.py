"""On-disk credential store.

Credentials live in ``~/.config/icpc/credentials.json`` (or under
``$XDG_CONFIG_HOME``), mode 0600 in a 0700 directory, keyed by username so more
than one account can be cached without a profile concept. One account is the
default — the one most recently logged in — so having several cached is never
ambiguous.

The file holds the Cognito tokens and, optionally, the account password.

**The password is stored base64-encoded, which is obfuscation and not encryption.**
Anyone who can read the file can recover it in one step. It is stored at all
because this Cognito app client rejects ``REFRESH_TOKEN_AUTH``: the id token dies
after an hour and SRP needs the plaintext password to mint another, so an
unattended job has no other way to carry on. The alternative in practice is
``ICPC_PASSWORD=…`` on a command line, which additionally leaks into shell
history and every child process.
"""

from __future__ import annotations

import base64
import binascii
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from icpc.auth.tokens import TokenSet

__all__ = ["Account", "CredentialStore", "default_config_dir"]

PASSWORD_KEY = "password_base64"

#: Bumped only if the on-disk shape changes incompatibly.
VERSION = 1


def default_config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME")
    return (Path(base) if base else Path.home() / ".config") / "icpc"


@dataclass(slots=True)
class Account:
    """One cached account."""

    username: str
    tokens: TokenSet | None = None
    #: Plaintext, decoded on read. ``None`` when the account was saved without one.
    password: str | None = None

    @property
    def can_renew(self) -> bool:
        """Whether this account can mint a fresh token unattended.

        False means the session dies when the id token expires, an hour after it
        was issued.
        """
        return self.password is not None


class CredentialStore:
    """A small JSON file of ``{username: {tokens…, password}}``."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_config_dir() / "credentials.json"

    # ------------------------------------------------------------- file io --

    def _read(self) -> tuple[dict[str, dict[str, Any]], str | None]:
        """Return ``(accounts, default_username)``.

        Accepts the older flat ``{username: {...}}`` shape too, so an existing
        file keeps working.
        """
        try:
            raw = self.path.read_text(encoding="utf-8")
        except (FileNotFoundError, NotADirectoryError):
            return {}, None
        try:
            data = json.loads(raw)
        except ValueError:
            return {}, None
        if not isinstance(data, dict):
            return {}, None
        accounts = data.get("accounts")
        if isinstance(accounts, dict):
            default = data.get("default")
            return accounts, default if isinstance(default, str) else None
        # Pre-versioned flat layout: every top-level key is an account.
        return {k: v for k, v in data.items() if isinstance(v, dict)}, None

    def _write(self, accounts: dict[str, dict[str, Any]], default: str | None) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Create the temp file 0600 from the start: writing the password and
        # tightening the mode afterwards would leave a readable window.
        fd, tmp_name = tempfile.mkstemp(dir=self.path.parent, prefix=".credentials-")
        tmp = Path(tmp_name)
        try:
            os.fchmod(fd, 0o600)
            if default not in accounts:
                default = None
            payload = {"version": VERSION, "default": default, "accounts": accounts}
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
            # Write-then-rename, so a crash cannot leave a truncated file behind.
            tmp.replace(self.path)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise

    # ------------------------------------------------------------ accounts --

    def _entry(self, username: str | None) -> tuple[str, dict[str, Any]] | None:
        accounts, default = self._read()
        if not accounts:
            return None
        if username is None:
            # The default is the account most recently logged in. Falling back to
            # "the only one" keeps a single-account file working even if the
            # default was never recorded.
            key = default if default in accounts else next(iter(accounts))
            if default not in accounts and len(accounts) != 1:
                return None
            return key, accounts[key]
        entry = accounts.get(username)
        return (username, entry) if entry is not None else None

    def load(self, username: str | None = None) -> Account | None:
        """Return the cached account for ``username``, or the default one."""
        found = self._entry(username)
        if found is None:
            return None
        key, entry = found
        try:
            tokens = TokenSet.from_dict(entry) if entry.get("id_token") else None
        except (KeyError, TypeError, ValueError):
            tokens = None
        return Account(
            username=entry.get("username") or key,
            tokens=tokens,
            password=_decode(entry.get(PASSWORD_KEY)),
        )

    def load_tokens(self, username: str | None = None) -> TokenSet | None:
        account = self.load(username)
        return account.tokens if account else None

    def save_tokens(self, tokens: TokenSet, *, make_default: bool = False) -> None:
        """Store or refresh an account's tokens, leaving any saved password alone."""
        key = tokens.username or "default"
        accounts, default = self._read()
        entry = accounts.setdefault(key, {})
        entry.update(tokens.to_dict())
        # The first account cached becomes the default; a later one only takes
        # over when it asks to, which is what a fresh `auth login` does.
        self._write(accounts, key if make_default or default is None else default)

    def save_password(self, username: str, password: str) -> None:
        """Store the password so the session can renew itself.

        See the module docstring: this is base64, not encryption.
        """
        accounts, default = self._read()
        entry = accounts.setdefault(username, {})
        entry["username"] = username
        entry[PASSWORD_KEY] = base64.b64encode(password.encode()).decode()
        self._write(accounts, default)

    def set_default(self, username: str) -> bool:
        """Make ``username`` the account used when none is named."""
        accounts, _ = self._read()
        if username not in accounts:
            return False
        self._write(accounts, username)
        return True

    def default_username(self) -> str | None:
        accounts, default = self._read()
        if default in accounts:
            return default
        return next(iter(accounts)) if len(accounts) == 1 else None

    def forget_password(self, username: str | None = None) -> bool:
        """Drop the stored password but keep the tokens. True if one was removed."""
        accounts, default = self._read()
        keys = list(accounts) if username is None else [username]
        removed = False
        for key in keys:
            if accounts.get(key, {}).pop(PASSWORD_KEY, None) is not None:
                removed = True
        if removed:
            self._write(accounts, default)
        return removed

    def delete(self, username: str | None = None) -> bool:
        """Forget one account, or all of them. True if anything was removed."""
        accounts, default = self._read()
        if not accounts:
            return False
        if username is None:
            self.path.unlink(missing_ok=True)
            return True
        if accounts.pop(username, None) is None:
            return False
        self._write(accounts, None if default == username else default)
        return True

    def usernames(self) -> list[str]:
        accounts, _ = self._read()
        return sorted(accounts)


def _decode(value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return base64.b64decode(value, validate=True).decode()
    except (binascii.Error, ValueError, UnicodeDecodeError):
        return None
