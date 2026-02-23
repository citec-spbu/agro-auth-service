import uuid
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from aiokafka import AIOKafkaProducer

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.database import get_async_session
from src.kafka.deps import get_kafka_producer
from src.kafka.config import kafka_settings
from src.models.users import User
from src.schemas.token import TokenPayloadSchema, TokenSchema
from src.schemas.user import UserCreateSchema, UserUpdateSchema
from src.token.config import jwt_settings
from src.token.token import Token
from src.utils.roles import RoleEnum


class AuthService:
    def __init__(
        self,
        session: AsyncSession = Depends(get_async_session),
        producer: AIOKafkaProducer = Depends(get_kafka_producer),
    ):
        self.session = session
        self.producer = producer

    async def read_user(self, id: int = None, email: str = None) -> User:
        if id:
            result = await self.session.execute(
                select(User)
                .where(User.id == id)
            )
        else:
            result = await self.session.execute(
                select(User)
                .where(User.email == email)
            )
        user = result.scalar()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

    async def create_user(
        self,
        schema: UserCreateSchema,
        creator_id: int = None
    ) -> User:
        try:
            user_duplicate = await self.read_user(email=schema.email)
        except HTTPException:
            user = User(
                email=schema.email,
                password_hashed=Token.get_password_hash(schema.text_password),
                role=schema.role.value,
                created_by=creator_id
            )
            self.session.add(user)
            await self.session.commit()

            await self.producer.send_and_wait(
                kafka_settings.REQUESTS_TOPIC,
                {
                    "email": user.email,
                    "user_id": str(user.id),
                    "trace_id": str(uuid.uuid4()),
                },
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email '{user_duplicate.email}' already exists"
            )
        return user

    async def login(self, email: str, password_text: str) -> TokenSchema:
        try:
            user = await self.read_user(email=email)
        except HTTPException:
            user = None
        if not user or not Token.verify_password(password_text, user.password_hashed):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        now = datetime.now()
        payload = TokenPayloadSchema(
            iat=now,
            exp=now + timedelta(minutes=jwt_settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            sub=str(user.id),
            role=user.role,
            email=user.email,
            org=user.created_by if user.created_by else user.id
        )
        return Token.create_token(payload)

    async def update_user(self, id: int, schema: UserUpdateSchema) -> None:
        user = await self.read_user(id=id)
        user.email = schema.email
        user.password_hashed = Token.get_password_hash(schema.text_password)
        await self.session.commit()

    async def delete_user(self, id: int) -> None:
        await self.session.execute(
            delete(User)
            .where(User.id == id)
        )
        await self.session.commit()

    async def read_created_users(self, id: int) -> list[User]:
        users = await self.session.execute(
            select(User)
            .where(User.created_by == id)
        )
        return users.scalars()

    async def delete_worker(self, organization_id: int, worker_id: int) -> None:
        worker = await self.read_user(id=worker_id)
        if worker.created_by != organization_id or worker.role != RoleEnum.WORKER.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with id: {worker_id} is not your worker"
            )
        await self.delete_user(worker_id)