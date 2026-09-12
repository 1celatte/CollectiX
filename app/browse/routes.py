import unicodedata
from flask import render_template, request
from app.browse import browse_bp
from app.models import Collection, Item, Listing, Tag
from datetime import datetime

#Remove diacritical marks (when search)
def normalize_text(text):
    text = text or ""
    normalized = unicodedata.normalize(
        "NFKD",
        text
    )


    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    ).casefold()

#Browse all public collections
@browse_bp.route("/")
def browse_page():
    #Read user's search and filter choices
    show = request.args.get("show", "all").strip()
    query = request.args.get("q", "").strip()
    tag = request.args.get("tag", "").strip()
    sort = request.args.get("sort", "newest").strip()
    
    results = []
    
    
    #Tags are read from the database
    tags = [
        row[0]
        for row in Tag.query.join(
            Collection,
            Collection.tag_id == Tag.id
        ).with_entities(
            Tag.name
        ).filter(
            Collection.status == "approved"
        ).distinct().order_by(
            Tag.name.asc()
        ).all()
    ]

    #Add collections to results
    if show in ("all", "collections"):
        collection_query = Collection.query.join(
            Tag,
            Collection.tag_id == Tag.id
        ).add_entity(
            Tag
        ).filter(
        Collection.status == "approved"
        )

        if tag:
            collection_query = collection_query.filter(
                Tag.name.ilike(tag)
            )

        for collection, tag_record in collection_query.all():
            #Compare search text without case or diacritics differences
            if query and normalize_text(query) not in normalize_text(collection.name):
                continue
            
            results.append({
                "type": "collection",
                "id": collection.id,
                "name": collection.name,
                "category": tag_record.name,
                "description": collection.description,
                "image": collection.image,
                "collection_name": collection.name,
                "price": None,
                "created_at": collection.created_at,
            })

    #Add collectible items to results
    if show in ("all", "items"):
        item_query = Item.query.join(
            Collection,
        Item.collection_id == Collection.id
    ).join(
        Tag,
        Collection.tag_id == Tag.id
    ).add_entity(
        Collection
    ).add_entity(
        Tag
    ).filter(
        Item.status == "approved",
        Collection.status == "approved"
    )


        if tag:
            item_query = item_query.filter(
                Tag.name.ilike(tag)
            )

        for item, collection, tag_record in item_query.all():
            #Compare search text without case or diacritics differences
            if query and normalize_text(query) not in normalize_text(item.name):
                 continue
            results.append({
                "type": "item",
                "id": item.id,
                "name": item.name,
                "category": tag_record.name,
                "description": item.description,
                "image": item.image,
                "collection_name": collection.name,
                "price": None,
                "created_at": item.created_at,
            })

    #Add marketplace listings to results
    if show in ("all", "marketplace"):
        listing_query = Listing.query.join(
            Item,
            Listing.item_id == Item.id
        ).join(
            Collection,
            Item.collection_id == Collection.id
        ).join(
            Tag,
            Collection.tag_id == Tag.id
        ).add_entity(
            Item
        ).add_entity(
            Collection
        ).add_entity(
            Tag
        ).filter(
            Listing.status == "available",
            Item.status == "approved",
            Collection.status == "approved"
        )
        
        if tag:
            listing_query = listing_query.filter(
                Tag.name.ilike(tag)
            )
            
        for listing, item, collection, tag_record in listing_query.all():
            #Compare search text without case or diacritics differences
            if query and normalize_text(query) not in normalize_text(item.name):
                 continue
             
            results.append({
                "type": "marketplace",
                "id": listing.id,
                "name": item.name,
                "category": tag_record.name,
                "description": listing.description or item.description,
                "image": item.image,
                "collection_name": collection.name,
                "price": listing.price,
                "created_at": listing.created_at,
            })

    #Sort the combined results
    if sort == "oldest":
        results.sort(
            key=lambda result: result["created_at"] or datetime.min
        )
    elif sort == "name":
        results.sort(
            key=lambda result: (result["name"] or "").lower()
        )
    elif sort == "lowest":
        results.sort(
            key=lambda result: (
                result["price"] is None,
                result["price"] or 0
            )
        )
    elif sort == "highest":
        results.sort(
            key=lambda result: (
                result["price"] is not None,
                result["price"] or 0
            ),
            reverse=True
        )
    else:
        results.sort(
            key=lambda result: result["created_at"] or datetime.min,
            reverse=True
        )

    return render_template(
        "browse.html",
        results=results,
        show=show,
        query=query,
        tag=tag,
        sort=sort,
        tags=tags
    )
    
#Display available marketplace listings
@browse_bp.route("/marketplace")
def browse_marketplace():
    #Get selected sorting option
    sort = request.args.get(
        "sort",
        "newest"
    )
      
        
    #Start with available listings
    listings_query = Listing.query.join(
        Item,
        Listing.item_id == Item.id
    ).add_entity(
        Item
    ).filter(
        Listing.status == "available"
    )

    #Sort marketplace listings
    if sort == "oldest":
        listings_query = listings_query.order_by(
            Listing.created_at.asc()
        )
    elif sort == "name":
        listings_query = listings_query.order_by(
            Item.name.asc()
        )
    elif sort == "lowest":
        listings_query = listings_query.order_by(
            Listing.price.asc().nulls_last()
        )
    elif sort == "highest":
        listings_query = listings_query.order_by(
            Listing.price.desc().nulls_last()
        )
    else:
        listings_query = listings_query.order_by(
            Listing.created_at.desc()
        )

    listings = listings_query.all()
        
    return render_template(
        "marketplace.html",
        listings=listings,
        sort=sort
    )