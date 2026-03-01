"""Auth module dependencies for DI."""

from typing import Annotated

from fastapi import Depends

from app.shared.dependencies import DBSessionDep
from app.modules.auth.repositories.magic_link_token_repository import (
    MagicLinkTokenRepository,
)
from app.modules.auth.repositories.user_repository import UserRepository
from app.modules.auth.services import MagicLinkService
from app.modules.auth.services.account_service import AccountService


def get_user_repository(db: DBSessionDep) -> UserRepository:
    return UserRepository(db)


def get_magic_link_token_repository(db: DBSessionDep) -> MagicLinkTokenRepository:
    return MagicLinkTokenRepository(db)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]
MagicLinkTokenRepositoryDep = Annotated[
    MagicLinkTokenRepository,
    Depends(get_magic_link_token_repository),
]


def get_magic_link_service(
    db: DBSessionDep,
    user_repo: UserRepositoryDep,
    token_repo: MagicLinkTokenRepositoryDep,
) -> MagicLinkService:
    return MagicLinkService(db=db, user_repo=user_repo, token_repo=token_repo)


def get_account_service(
    db: DBSessionDep,
    user_repo: UserRepositoryDep,
) -> AccountService:
    return AccountService(db=db, user_repo=user_repo)


MagicLinkServiceDep = Annotated[MagicLinkService, Depends(get_magic_link_service)]
AccountServiceDep = Annotated[AccountService, Depends(get_account_service)]
