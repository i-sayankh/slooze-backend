import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models import Role, Country
from app.schemas.auth import CountryEnum, RoleEnum


ROLES = [role.value for role in RoleEnum]
COUNTRIES = [country.value for country in CountryEnum]


async def seed_roles_and_countries():
    async with AsyncSessionLocal() as session:

        # Seed Roles
        for role_name in ROLES:
            result = await session.execute(select(Role).where(Role.name == role_name))
            existing_role = result.scalar_one_or_none()

            if not existing_role:
                session.add(Role(name=role_name))
                print(f"Inserted role: {role_name}")

        # Seed Countries
        for country_name in COUNTRIES:
            result = await session.execute(
                select(Country).where(Country.name == country_name)
            )
            existing_country = result.scalar_one_or_none()

            if not existing_country:
                session.add(Country(name=country_name))
                print(f"Inserted country: {country_name}")

        await session.commit()
        print("Seeding completed successfully.")


if __name__ == "__main__":
    asyncio.run(seed_roles_and_countries())
