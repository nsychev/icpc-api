"""Authenticators: password (SRP), refresh token, or a raw id token.

An authenticator is what the transport asks for a bearer token. It renews
proactively (``Settings.refresh_margin`` seconds before expiry) and again on demand
when the transport sees a 401.
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any

import httpx

from icpc import errors
from icpc.auth import cognito
from icpc.auth.cognito import Challenge, CognitoCall
from icpc.auth.srp import SrpSession
from icpc.auth.store import CredentialStore
from icpc.auth.tokens import TokenSet
from icpc.config import Settings

__all__ = ["AsyncCognitoAuth", "CognitoAuth", "StaticTokenAuth"]

_MFA_CHALLENGES = frozenset({cognito.SOFTWARE_TOKEN_MFA, cognito.SMS_MFA})


class StaticTokenAuth:
    """A fixed id token, e.g. copied out of a browser session.

    It cannot be renewed, so it stops working an hour after it was issued.
    """

    def __init__(self, token: str) -> None:
        self._token = token

    async def id_token(self) -> str:  # AsyncTokenProvider
        return self._token

    async def invalidate(self) -> None:
        raise errors.TokenExpired("the supplied id token was rejected and cannot be renewed")


class SyncStaticTokenAuth:
    """Sync counterpart of :class:`StaticTokenAuth`."""

    def __init__(self, token: str) -> None:
        self._token = token

    def id_token(self) -> str:  # TokenProvider
        return self._token

    def invalidate(self) -> None:
        raise errors.TokenExpired("the supplied id token was rejected and cannot be renewed")


class _Base:
    """State shared by the async and sync authenticators."""

    def __init__(
        self,
        *,
        username: str | None = None,
        password: str | None = None,
        tokens: TokenSet | None = None,
        store: CredentialStore | None = None,
        settings: Settings | None = None,
        save_password: bool = False,
        make_default: bool = False,
    ) -> None:
        self.settings = settings or Settings()
        self.store = store
        self.username = username
        # The subclasses only ever assign a `str` here, we want to keep the
        # attributes nullable.
        self._password: str | None = password
        self._tokens: TokenSet | None = tokens
        #: Persist the password on the next successful login, so the session can
        #: renew itself once the hour-long id token expires.
        self.save_password = save_password
        #: Make this the account used when no username is given.
        self.make_default = make_default
        if store is not None:
            account = store.load(username)
            if account is not None:
                if self._tokens is None:
                    self._tokens = account.tokens
                if self.username is None:
                    self.username = account.username
                # A stored password is what makes unattended renewal possible at
                # all: this pool has no working refresh-token flow.
                if self._password is None:
                    self._password = account.password

    @property
    def tokens(self) -> TokenSet | None:
        return self._tokens

    def _remember(self, tokens: TokenSet) -> TokenSet:
        self._tokens = tokens
        if tokens.username:
            self.username = tokens.username
        if self.store is not None:
            self.store.save_tokens(tokens, make_default=self.make_default)
            if self.save_password and self.username and self._password:
                self.store.save_password(self.username, self._password)
        return tokens

    def _srp(self, username: str, password: str) -> SrpSession:
        return SrpSession.create(username, password, self.settings.user_pool_id)

    def _need_password(self) -> tuple[str, str]:
        if not self.username or not self._password:
            raise errors.ConfigError(
                "no valid token and no username/password to obtain one; "
                "run `icpc auth login` or set ICPC_ID_TOKEN / ICPC_REFRESH_TOKEN"
            )
        return self.username, self._password

    @staticmethod
    def _expect_password_verifier(outcome: cognito.Outcome) -> Challenge:
        if not isinstance(outcome, Challenge):
            raise errors.AuthError("Cognito issued tokens without asking for the password")
        if outcome.name != cognito.PASSWORD_VERIFIER:
            raise errors.AuthError(f"unsupported Cognito challenge: {outcome.name}")
        return outcome

    def _finish(self, outcome: cognito.Outcome, username: str, mfa_code: str | None) -> TokenSet:
        if isinstance(outcome, TokenSet):
            return self._remember(outcome)
        if outcome.name in _MFA_CHALLENGES and mfa_code is None:
            raise errors.MfaRequired(outcome.name, outcome.session, username)
        raise errors.AuthError(f"unsupported Cognito challenge: {outcome.name}")


class AsyncCognitoAuth(_Base):
    """Async authenticator implementing :class:`~icpc.auth.provider.AsyncTokenProvider`."""

    def __init__(self, *, http: httpx.AsyncClient | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._owns_http = http is None
        self._http = http or httpx.AsyncClient(timeout=self.settings.timeout)
        self._lock = asyncio.Lock()

    async def _call(self, call: CognitoCall) -> dict[str, Any]:
        try:
            response = await self._http.post(
                self.settings.cognito_url, json=call.payload, headers=call.headers
            )
        except httpx.HTTPError as exc:
            raise errors.TransportError(f"cognito {call.target}: {exc}") from exc
        payload = response.json() if response.content else {}
        cognito.raise_for_error(response.status_code, payload)
        return payload

    async def login(self, username: str, password: str, *, mfa_code: str | None = None) -> TokenSet:
        """Full SRP password login. Raises :class:`~icpc.errors.MfaRequired` if the
        account has MFA and no ``mfa_code`` was supplied."""
        srp = self._srp(username, password)
        challenge = self._expect_password_verifier(
            cognito.parse_outcome(await self._call(cognito.initiate_srp(self.settings, srp)))
        )
        responses = srp.process_challenge(challenge.parameters)
        outcome = cognito.parse_outcome(
            await self._call(
                cognito.respond_password_verifier(self.settings, responses, challenge.session)
            )
        )
        if isinstance(outcome, Challenge) and outcome.name in _MFA_CHALLENGES and mfa_code:
            outcome = cognito.parse_outcome(
                await self._call(cognito.respond_mfa(self.settings, outcome, username, mfa_code))
            )
        self.username = username
        self._password = password
        return self._finish(outcome, username, mfa_code)

    async def complete_mfa(self, challenge: Challenge, username: str, code: str) -> TokenSet:
        """Answer a challenge carried by a previously raised :class:`MfaRequired`."""
        outcome = cognito.parse_outcome(
            await self._call(cognito.respond_mfa(self.settings, challenge, username, code))
        )
        return self._finish(outcome, username, code)

    async def refresh(self) -> TokenSet:
        """Renew the id token with ``REFRESH_TOKEN_AUTH``, falling back to a login."""
        current = self._tokens
        if current is not None and current.refresh_token:
            try:
                payload = await self._call(cognito.refresh(self.settings, current.refresh_token))
            except errors.InvalidCredentials as exc:
                # A revoked refresh token, or a pool where REFRESH_TOKEN_AUTH is
                # not enabled at all — which is the case for icpc.global. Fall
                # back to a password login, but keep the reason if there is none.
                if not (self.username and self._password):
                    raise errors.TokenExpired(
                        f"could not renew the token ({exc}); log in again with a "
                        f"password, or run `icpc auth login`"
                    ) from exc
            else:
                renewed = cognito.parse_outcome(payload, refresh_token=current.refresh_token)
                if isinstance(renewed, TokenSet):
                    return self._remember(renewed)
                raise errors.AuthError(
                    f"refresh returned a {renewed.name} challenge instead of tokens"
                )
        username, password = self._need_password()
        return await self.login(username, password)

    async def id_token(self) -> str:
        async with self._lock:
            current = self._tokens
            if current is not None and not current.expired(self.settings.refresh_margin):
                return current.id_token
            return (await self.refresh()).id_token

    async def invalidate(self) -> None:
        async with self._lock:
            if self._tokens is not None:
                self._tokens.expires_at = 0.0

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()


class CognitoAuth(_Base):
    """Sync authenticator implementing :class:`~icpc.auth.provider.TokenProvider`."""

    def __init__(self, *, http: httpx.Client | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._owns_http = http is None
        self._http = http or httpx.Client(timeout=self.settings.timeout)
        self._lock = threading.Lock()

    def _call(self, call: CognitoCall) -> dict[str, Any]:
        try:
            response = self._http.post(
                self.settings.cognito_url, json=call.payload, headers=call.headers
            )
        except httpx.HTTPError as exc:
            raise errors.TransportError(f"cognito {call.target}: {exc}") from exc
        payload = response.json() if response.content else {}
        cognito.raise_for_error(response.status_code, payload)
        return payload

    def login(self, username: str, password: str, *, mfa_code: str | None = None) -> TokenSet:
        """Full SRP password login. Raises :class:`~icpc.errors.MfaRequired` if the
        account has MFA and no ``mfa_code`` was supplied."""
        srp = self._srp(username, password)
        challenge = self._expect_password_verifier(
            cognito.parse_outcome(self._call(cognito.initiate_srp(self.settings, srp)))
        )
        responses = srp.process_challenge(challenge.parameters)
        outcome = cognito.parse_outcome(
            self._call(
                cognito.respond_password_verifier(self.settings, responses, challenge.session)
            )
        )
        if isinstance(outcome, Challenge) and outcome.name in _MFA_CHALLENGES and mfa_code:
            outcome = cognito.parse_outcome(
                self._call(cognito.respond_mfa(self.settings, outcome, username, mfa_code))
            )
        self.username = username
        self._password = password
        return self._finish(outcome, username, mfa_code)

    def complete_mfa(self, challenge: Challenge, username: str, code: str) -> TokenSet:
        """Answer a challenge carried by a previously raised :class:`MfaRequired`."""
        outcome = cognito.parse_outcome(
            self._call(cognito.respond_mfa(self.settings, challenge, username, code))
        )
        return self._finish(outcome, username, code)

    def refresh(self) -> TokenSet:
        """Renew the id token with ``REFRESH_TOKEN_AUTH``, falling back to a login."""
        current = self._tokens
        if current is not None and current.refresh_token:
            try:
                payload = self._call(cognito.refresh(self.settings, current.refresh_token))
            except errors.InvalidCredentials as exc:
                # A revoked refresh token, or a pool where REFRESH_TOKEN_AUTH is
                # not enabled at all — which is the case for icpc.global. Fall
                # back to a password login, but keep the reason if there is none.
                if not (self.username and self._password):
                    raise errors.TokenExpired(
                        f"could not renew the token ({exc}); log in again with a "
                        f"password, or run `icpc auth login`"
                    ) from exc
            else:
                renewed = cognito.parse_outcome(payload, refresh_token=current.refresh_token)
                if isinstance(renewed, TokenSet):
                    return self._remember(renewed)
                raise errors.AuthError(
                    f"refresh returned a {renewed.name} challenge instead of tokens"
                )
        username, password = self._need_password()
        return self.login(username, password)

    def id_token(self) -> str:
        with self._lock:
            current = self._tokens
            if current is not None and not current.expired(self.settings.refresh_margin):
                return current.id_token
            return self.refresh().id_token

    def invalidate(self) -> None:
        with self._lock:
            if self._tokens is not None:
                self._tokens.expires_at = 0.0

    def close(self) -> None:
        if self._owns_http:
            self._http.close()
