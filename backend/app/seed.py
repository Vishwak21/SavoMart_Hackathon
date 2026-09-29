from sqlalchemy import select, text

from app.database import Base, SessionLocal, engine
from app.demo_users import DEMO_USERS
from app.models import User


def seed_demo_users() -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))

    Base.metadata.create_all(engine)

    with SessionLocal() as session:
        for demo_user in DEMO_USERS:
            user = session.scalar(
                select(User).where(User.email == demo_user["email"])
            )
            if user is None:
                session.add(
                    User(
                        name=demo_user["name"],
                        email=demo_user["email"],
                        role=demo_user["role"],
                    )
                )
            else:
                user.name = demo_user["name"]
                user.role = demo_user["role"]
        session.commit()


if __name__ == "__main__":
    seed_demo_users()
    print("PostGIS is enabled and demo users are ready.")