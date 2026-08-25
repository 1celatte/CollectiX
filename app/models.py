from datetime import datetime
from app.extensions import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    profile_picture = db.Column(db.String(255), nullable=True)


class Collection(db.Model):
    __tablename__ = "collections"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(80))
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
    status = db.Column(db.String(20), default="pending", nullable=False)

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Item(db.Model):
    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)

    collection_id = db.Column(
        db.Integer,
        db.ForeignKey("collections.id"),
        nullable=False
    )

    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
    status = db.Column(db.String(20), default="pending", nullable=False)

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class UserCollection(db.Model):
    __tablename__ = "user_collections"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    collection_id = db.Column(
        db.Integer,
        db.ForeignKey("collections.id"),
        nullable=False
    )

    added_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "collection_id",
            name="uq_user_collection"
        ),
    )


class OwnedItem(db.Model):
    __tablename__ = "owned_items"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    item_id = db.Column(
        db.Integer,
        db.ForeignKey("items.id"),
        nullable=False
    )

    quantity = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    added_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "item_id",
            name="uq_owned_item"
        ),
    )


class Submission(db.Model):
    __tablename__ = "submissions"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    type = db.Column(
        db.String(20),
        nullable=False
    )  # new_collection / new_item

    collection_id = db.Column(
        db.Integer,
        db.ForeignKey("collections.id"),
        nullable=True
    )

    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(255))

    status = db.Column(
        db.String(20),
        default="pending",
        nullable=False
    )  # pending / approved / rejected

    reviewed_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class CorrectionRequest(db.Model):
    __tablename__ = "correction_requests"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    item_id = db.Column(
        db.Integer,
        db.ForeignKey("items.id"),
        nullable=False
    )

    type = db.Column(
        db.String(20),
        nullable=False
    )  # text / image / both

    description = db.Column(db.Text, nullable=False)

    image = db.Column(db.String(255), nullable=True)

    status = db.Column(
        db.String(20),
        default="pending",
        nullable=False
    )  # pending / approved / rejected

    reviewed_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Listing(db.Model):
    __tablename__ = "listings"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    item_id = db.Column(
        db.Integer,
        db.ForeignKey("items.id"),
        nullable=False
    )

    listing_type = db.Column(
        db.String(10),
        nullable=False
    )  # sell / trade

    price = db.Column(
        db.Float,
        nullable=True
    )

    condition = db.Column(
        db.String(50),
        default="Good"
    )

    description = db.Column(db.Text)

    status = db.Column(
        db.String(20),
        default="available",
        nullable=False
    )  # available / pending / sold / traded

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)

    listing_id = db.Column(
        db.Integer,
        db.ForeignKey("listings.id"),
        nullable=False
    )

    buyer_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    seller_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    item_id = db.Column(
        db.Integer,
        db.ForeignKey("items.id"),
        nullable=False
    )

    price = db.Column(
        db.Float,
        nullable=False
    )

    status = db.Column(
        db.String(20),
        default="pending",
        nullable=False
    )  # pending / completed / cancelled

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class Trade(db.Model):
    __tablename__ = "trades"

    id = db.Column(db.Integer, primary_key=True)

    sender_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    receiver_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    offered_item_id = db.Column(
        db.Integer,
        db.ForeignKey("items.id"),
        nullable=False
    )

    requested_item_id = db.Column(
        db.Integer,
        db.ForeignKey("items.id"),
        nullable=False
    )

    status = db.Column(
        db.String(20),
        default="pending",
        nullable=False
    )  # pending / accepted / rejected / completed

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )