from app import create_app
from app.extensions import db
from app.models import (
    User,
    Collection,
    Item,
    UserCollection,
    OwnedItem,
    Submission,
    CorrectionRequest,
    Listing,
    Transaction,
    Trade
)
from werkzeug.security import generate_password_hash


app = create_app()


with app.app_context():

    print("Clearing existing seed data...")

    # Clear existing data
    db.session.query(Trade).delete()
    db.session.query(Transaction).delete()
    db.session.query(Listing).delete()
    db.session.query(CorrectionRequest).delete()
    db.session.query(Submission).delete()
    db.session.query(OwnedItem).delete()
    db.session.query(UserCollection).delete()
    db.session.query(Item).delete()
    db.session.query(Collection).delete()
    db.session.query(User).delete()

    db.session.commit()


    # =========================
    # USERS
    # =========================

    admin = User(
        name="admin",
        email="admin@collectix.com",
        password=generate_password_hash("Test1234!"),
        role="admin"
    )

    alice = User(
        name="alice",
        email="alice@collectix.com",
        password=generate_password_hash("Test1234!"),
        role="user"
    )

    bob = User(
        name="bob",
        email="bob@collectix.com",
        password=generate_password_hash("Test1234!"),
        role="user"
    )

    charlie = User(
        name="charlie",
        emailn="charlie@collectix.com",
        password=generate_password_hash("Test1234!"),
        role="user"
    )

    db.session.add_all([
        admin,
        alice,
        bob,
        charlie
    ])

    db.session.commit()


    # =========================
    # COLLECTIONS
    # =========================

    pokemon = Collection(
        name="Pokémon Scarlet & Violet",
        category="Trading Card",
        description="Pokémon Scarlet & Violet collectible card series.",
        image=None,
        status="approved",
        created_by=admin.id
    )

    naruto = Collection(
        name="Naruto Shippuden",
        category="Anime Figure",
        description="Naruto Shippuden collectible figures.",
        image="collection.jpg",
        status="approved",
        created_by=admin.id
    )

    crybaby = Collection(
        name="POP MART Crybaby Series",
        category="Blind Box",
        description="POP MART Crybaby collectible series.",
        image="crybaby.jpg",
        status="approved",
        created_by=admin.id
    )

    db.session.add_all([
        pokemon,
        naruto,
        crybaby
    ])

    db.session.commit()


    # =========================
    # ITEMS
    # =========================

    pikachu = Item(
        collection_id=pokemon.id,
        name="Pikachu",
        description="Pikachu collectible card.",
        image="pikachu.png",
        status="approved",
        created_by=admin.id
    )

    charizard = Item(
        collection_id=pokemon.id,
        name="Charizard",
        description="Charizard collectible card.",
        image="charizard.jpg",
        status="approved",
        created_by=admin.id
    )

    eevee = Item(
        collection_id=pokemon.id,
        name="Eevee",
        description="Eevee collectible card.",
        image=None,
        status="approved",
        created_by=admin.id
    )

    naruto_item = Item(
        collection_id=naruto.id,
        name="Naruto Uzumaki",
        description="Naruto Uzumaki collectible figure.",
        image="naruto.png",
        status="approved",
        created_by=admin.id
    )

    sasuke = Item(
        collection_id=naruto.id,
        name="Sasuke Uchiha",
        description="Sasuke Uchiha collectible figure.",
        image=None,
        status="approved",
        created_by=admin.id
    )

    sakura = Item(
        collection_id=naruto.id,
        name="Sakura Haruno",
        description="Sakura Haruno collectible figure.",
        image="sakura.jpg",
        status="approved",
        created_by=admin.id
    )

    kakashi = Item(
        collection_id=naruto.id,
        name="Kakashi Hatake",
        description="Kakashi Hatake collectible figure.",
        image="kakashi_test.png",
        status="approved",
        created_by=admin.id
    )

    crybaby_love = Item(
        collection_id=crybaby.id,
        name="Crybaby Love",
        description="Crybaby Love collectible figure.",
        image=None,
        status="approved",
        created_by=admin.id
    )

    crybaby_angel = Item(
        collection_id=crybaby.id,
        name="Crybaby Angel",
        description="Crybaby Angel collectible figure.",
        image=None,
        status="approved",
        created_by=admin.id
    )

    crybaby_bear = Item(
        collection_id=crybaby.id,
        name="Crybaby Pink Bear",
        description="Crybaby Pink Bear collectible figure.",
        image=None,
        status="approved",
        created_by=admin.id
    )

    db.session.add_all([
        pikachu,
        charizard,
        eevee,
        naruto_item,
        sasuke,
        sakura,
        kakashi,
        crybaby_love,
        crybaby_angel,
        crybaby_bear
    ])

    db.session.commit()


    # =========================
    # USER COLLECTIONS
    # =========================

    db.session.add_all([
        UserCollection(
            user_id=alice.id,
            collection_id=pokemon.id
        ),

        UserCollection(
            user_id=alice.id,
            collection_id=naruto.id
        ),

        UserCollection(
            user_id=bob.id,
            collection_id=naruto.id
        ),

        UserCollection(
            user_id=bob.id,
            collection_id=crybaby.id
        ),

        UserCollection(
            user_id=charlie.id,
            collection_id=pokemon.id
        )
    ])

    db.session.commit()


    # =========================
    # OWNED ITEMS
    # =========================

    db.session.add_all([
        OwnedItem(
            user_id=alice.id,
            item_id=pikachu.id,
            quantity=2
        ),

        OwnedItem(
            user_id=alice.id,
            item_id=eevee.id,
            quantity=1
        ),

        OwnedItem(
            user_id=bob.id,
            item_id=naruto_item.id,
            quantity=1
        ),

        OwnedItem(
            user_id=bob.id,
            item_id=kakashi.id,
            quantity=1
        ),

        OwnedItem(
            user_id=charlie.id,
            item_id=pikachu.id,
            quantity=1
        ),

        OwnedItem(
            user_id=charlie.id,
            item_id=charizard.id,
            quantity=1
        )
    ])

    db.session.commit()


    # =========================
    # LISTINGS
    # =========================

    listing_1 = Listing(
        user_id=bob.id,
        item_id=charizard.id,
        listing_type="sell",
        price=80.00,
        condition="Excellent",
        description="Charizard card in excellent condition.",
        status="available"
    )

    listing_2 = Listing(
        user_id=charlie.id,
        item_id=sasuke.id,
        listing_type="trade",
        price=None,
        condition="Good",
        description="Looking to trade for another Naruto figure.",
        status="available"
    )

    listing_3 = Listing(
        user_id=bob.id,
        item_id=sakura.id,
        listing_type="sell",
        price=50.00,
        condition="Good",
        description="Sakura collectible figure.",
        status="available"
    )

    db.session.add_all([
        listing_1,
        listing_2,
        listing_3
    ])

    db.session.commit()


    # =========================
    # TRADE
    # =========================

    trade = Trade(
        sender_id=alice.id,
        receiver_id=bob.id,
        offered_item_id=pikachu.id,
        requested_item_id=sasuke.id,
        status="pending"
    )

    db.session.add(trade)

    db.session.commit()


    # =========================
    # SUBMISSION
    # =========================

    submission = Submission(
        user_id=charlie.id,
        type="new_collection",
        collection_id=None,
        name="One Piece Figures",
        description="One Piece collectible figures.",
        image=None,
        status="pending",
        reviewed_by=None
    )

    db.session.add(submission)

    db.session.commit()


    # =========================
    # CORRECTION REQUEST
    # =========================

    correction = CorrectionRequest(
        user_id=alice.id,
        item_id=pikachu.id,
        type="text",
        description="The description of this item needs to be corrected.",
        image=None,
        status="pending",
        reviewed_by=None
    )

    db.session.add(correction)

    db.session.commit()


    print("================================")
    print("Seed database completed!")
    print("================================")
    print()
    print("Test accounts:")
    print("admin@collectix.com / Test1234!")
    print("alice@collectix.com / Test1234!")
    print("bob@collectix.com / Test1234!")
    print("charlie@collectix.com / Test1234!")