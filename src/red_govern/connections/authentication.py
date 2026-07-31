"""Authentication resolution for Red-Govern Redshift connections."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from red_govern.config.models import RedshiftConfig
from red_govern.exceptions import AuthenticationError

ResolvedAuthMethod = Literal["password", "iam", "profile"]


@dataclass(frozen=True, slots=True)
class AuthenticationDetails:
    """Resolved non-secret authentication information."""

    method: ResolvedAuthMethod
    password: str | None = None
    aws_profile: str | None = None
    cluster_identifier: str | None = None
    workgroup_name: str | None = None
    region: str | None = None
    db_user: str | None = None


def resolve_authentication(
    config: RedshiftConfig,
) -> AuthenticationDetails:
    """Resolve authentication mode without persisting credentials."""
    auth = config.authentication
    method = auth.method

    if method == "auto":
        password = os.getenv(auth.password_env)

        if password:
            method = "password"
        elif auth.aws_profile:
            method = "profile"
        elif auth.cluster_identifier or auth.workgroup_name:
            method = "iam"
        else:
            raise AuthenticationError(
                "Unable to determine authentication method. "
                f"Set {auth.password_env}, configure aws_profile, or "
                "select authentication.method explicitly."
            )

    if method == "password":
        password = os.getenv(auth.password_env)

        if not password:
            raise AuthenticationError(
                f"Password environment variable is not set: "
                f"{auth.password_env}"
            )

        return AuthenticationDetails(
            method="password",
            password=password,
        )

    if method == "profile":
        if not auth.aws_profile:
            raise AuthenticationError(
                "aws_profile is required for profile authentication."
            )

        return AuthenticationDetails(
            method="profile",
            aws_profile=auth.aws_profile,
            cluster_identifier=auth.cluster_identifier,
            workgroup_name=auth.workgroup_name,
            region=auth.region,
            db_user=auth.db_user,
        )

    if method == "iam":
        return AuthenticationDetails(
            method="iam",
            cluster_identifier=auth.cluster_identifier,
            workgroup_name=auth.workgroup_name,
            region=auth.region,
            db_user=auth.db_user,
        )

    if method == "data_api":
        raise AuthenticationError(
            "Data API authentication is not implemented in v0.1.0a1."
        )

    raise AuthenticationError(
        f"Unsupported authentication method: {method}"
    )
