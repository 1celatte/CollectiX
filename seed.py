from app import create_app
from app.extensions import db
from app.models import (
    User,
    Tag,
    Collection,
    Item,
    UserCollection,
    OwnedItem,
    Submission,
    Listing,
    Transaction,
    Trade,
    PaymentQR
)
from werkzeug.security import generate_password_hash
from app.utils import normalize_text


app = create_app()


with app.app_context():

    print("Clearing existing seed data...")

    # =========================
    # CLEAR EXISTING DATA
    # =========================

    db.session.query(PaymentQR).delete()
    db.session.query(Trade).delete()
    db.session.query(Transaction).delete()
    db.session.query(Listing).delete()
    db.session.query(Submission).delete()
    db.session.query(OwnedItem).delete()
    db.session.query(UserCollection).delete()
    db.session.query(Item).delete()
    db.session.query(Collection).delete()
    db.session.query(Tag).delete()
    db.session.query(User).delete()

    db.session.commit()


    # =========================
    # USERS
    # =========================

    admin = User(
        name="admin",
        email="admin@collectix.com",
        password=generate_password_hash("Test1234!"),
        role="admin",
        email_verified=True
    )

    admin2 = User(
        name="coco",
        email="cngchifei@gmail.com",
        password=generate_password_hash("Test1234!"),
        role="admin",
        email_verified=True
    )

    alice = User(
        name="alice",
        email="alice@collectix.com",
        password=generate_password_hash("Test1234!"),
        role="user",
        email_verified=True
    )

    bob = User(
        name="bob",
        email="bob@collectix.com",
        password=generate_password_hash("Test1234!"),
        role="user",
        email_verified=True
    )

    charlie = User(
        name="charlie",
        email="charlie@collectix.com",
        password=generate_password_hash("Test1234!"),
        role="user",
        email_verified=True
    )

    db.session.add_all([
        admin,
        admin2,
        alice,
        bob,
        charlie
    ])

    db.session.commit()


    # =========================
    # TAGS
    # =========================

    trading_cards = Tag(
        name="trading cards", 
        normalized_name="trading cards"
    )

    blind_box = Tag(
        name="blind box",
        normalized_name="blind box"
    )

    anime_figure = Tag(
        name="anime figure",
        normalized_name="anime figure"
    )

    db.session.add_all([
        trading_cards,
        blind_box,
        anime_figure
    ])

    db.session.commit()


    # =========================
    # COLLECTIONS
    # =========================

    pokemon = Collection(
        name="Pokémon Scarlet & Violet",
        normalized_name="pokemon scarlet & violet",
        tag_id=trading_cards.id,
        description="Pokémon Scarlet & Violet collectible card series.",
        image=None,
        status="approved",
        created_by=admin.id
    )

    naruto = Collection(
        name="Naruto Shippuden",
        normalized_name="naruto shippuden",
        tag_id=anime_figure.id,
        description="Naruto Shippuden collectible figures.",
        image="collection.jpg",
        status="approved",
        created_by=admin.id
    )

    crybaby = Collection(
        name="POP MART Crybaby Series",
        normalized_name="pop mart crybaby series",
        tag_id=blind_box.id,
        description="POP MART Crybaby collectible series.",
        image="crybaby.jpg",
        status="approved",
        created_by=admin.id
    )

    for collection in [pokemon, naruto, crybaby]:
        collection.normalized_name = normalize_text(collection.name)
    
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
        normalized_name="pikachu",
        description="Pikachu collectible card.",
        image="pikachu.png",
        status="approved",
        created_by=admin.id
    )

    charizard = Item(
        collection_id=pokemon.id,
        name="Charizard",
        normalized_name="charizard",
        description="Charizard collectible card.",
        image="charizard.jpg",
        status="approved",
        created_by=admin.id
    )

    eevee = Item(
        collection_id=pokemon.id,
        name="Eevee",
        normalized_name="eevee",
        description="Eevee collectible card.",
        image=None,
        status="approved",
        created_by=admin.id
    )

    naruto_item = Item(
        collection_id=naruto.id,
        name="Naruto Uzumaki",
        normalized_name="naruto uzumaki",
        description="Naruto Uzumaki collectible figure.",
        image="naruto.png",
        status="approved",
        created_by=admin.id
    )

    sasuke = Item(
        collection_id=naruto.id,
        name="Sasuke Uchiha",
        normalized_name="sasuke uchiha",
        description="Sasuke Uchiha collectible figure.",
        image=None,
        status="approved",
        created_by=admin.id
    )

    sakura = Item(
        collection_id=naruto.id,
        name="Sakura Haruno",
        normalized_name="sakura haruno",
        description="Sakura Haruno collectible figure.",
        image="sakura.jpg",
        status="approved",
        created_by=admin.id
    )

    kakashi = Item(
        collection_id=naruto.id,
        name="Kakashi Hatake",
        normalized_name="kakashi hatake",
        description="Kakashi Hatake collectible figure.",
        image="kakashi_test.png",
        status="approved",
        created_by=admin.id
    )

    crybaby_love = Item(
        collection_id=crybaby.id,
        name="Crybaby Love",
        normalized_name="crybaby love",
        description="Crybaby Love collectible figure.",
        image=None,
        status="approved",
        created_by=admin.id
    )

    crybaby_angel = Item(
        collection_id=crybaby.id,
        name="Crybaby Angel",
        normalized_name="crybaby angel",
        description="Crybaby Angel collectible figure.",
        image=None,
        status="approved",
        created_by=admin.id
    )

    crybaby_bear = Item(
        collection_id=crybaby.id,
        name="Crybaby Pink Bear",
        normalized_name="crybaby pink bear",
        description="Crybaby Pink Bear collectible figure.",
        image=None,
        status="approved",
        created_by=admin.id
    )


    for item in [
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
    ]:
        item.normalized_name = normalize_text(item.name)
    
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
            collection_id=pokemon.id
        ),

        UserCollection(
            user_id=bob.id,
            collection_id=crybaby.id
        ),

        UserCollection(
            user_id=charlie.id,
            collection_id=pokemon.id
        ),

        UserCollection(
            user_id=charlie.id,
            collection_id=naruto.id
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
            user_id=bob.id,
            item_id=charizard.id,
            quantity=1
        ),

        OwnedItem(
            user_id=bob.id,
            item_id=sakura.id,
            quantity=1
        ),

        OwnedItem(
            user_id=bob.id,
            item_id=sasuke.id,
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
        ),

        OwnedItem(
            user_id=charlie.id,
            item_id=sasuke.id,
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

    pending_collection = Collection(
        name="One Piece Figures",
        normalized_name=normalize_text("One Piece Figures"),
        tag_id=anime_figure.id,
        description="One Piece collectible figures.",
        image=None,
        status="pending",
        created_by=charlie.id
    )

    db.session.add(pending_collection)

    db.session.flush()


    submission = Submission(
        user_id=charlie.id,
        type="new_collection",
        collection_id=pending_collection.id,
        name="One Piece Figures",
        description="One Piece collectible figures.",
        image=None,
        tag_id=anime_figure.id,
        new_tag=None,
        status="pending",
        reviewed_by=None
    )

    db.session.add(submission)

    db.session.commit()


    # =========================
    # COMPLETE
    # =========================

    print("================================")
    print("Seed database completed!")
    print("================================")
    print()
    print("Test accounts:")
    print("admin@collectix.com / Test1234!")
    print("cngchifei@gmail.com / Test1234!")
    print("alice@collectix.com / Test1234!")
    print("bob@collectix.com / Test1234!")
    print("charlie@collectix.com / Test1234!")
