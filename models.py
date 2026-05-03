from sqlalchemy import Column, BigInteger, String, DateTime, func, Integer, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    is_subscribed = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    history = relationship("SearchHistory", back_populates="user", cascade="all, delete-orphan")


class School(Base):
    __tablename__ = "schools"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    price_per_week = Column(Integer, nullable=False)
    rating = Column(Float, nullable=False)
    age_group = Column(String, nullable=False)
    durations = Column(String, nullable=False)
    description = Column(String, nullable=True)

    favorites = relationship("Favorite", back_populates="school", cascade="all, delete-orphan")


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="favorites")
    school = relationship("School", back_populates="favorites")


class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    age = Column(String, nullable=True)
    city = Column(String, nullable=True)
    duration = Column(String, nullable=True)
    sort_type = Column(String, nullable=True)
    results_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="history")