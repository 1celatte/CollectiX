from flask import render_template, request
from app.browse import browse_bp
from app.models import Collection, Item, Listing
from datetime import datetime

#Browse all public collections
@browse_bp.route("/")
def browse_page():
    #Read user's search and filter choices
    show = request.args.get("show", "all").strip()
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    collection_id = request.args.get("collection_id", "").strip()
    sort = request.args.get("sort", "newest").strip()
    
    results = []
    
    #Approved collections for collection filter
    collections = Collection.query.filter_by(
        status="approved"
    ).order_by(
        Collection.name.asc()
    ).all()
    
    #Categories are read from the database
    categories = [
        row[0]
        for row in Collection.query.with_entities(
            Collection.category
        ).filter(
            Collection.status == "approved",
            Collection.category.isnot(None)
        ).distinct().order_by(
            Collection.category.asc()
        ).all()
    ]

    #Add collections to results
    if show in ("all", "collections"):
        collection_query = Collection.query.filter_by(
            status="approved"
        )

        if query:
            collection_query = collection_query.filter(
                Collection.name.ilike(f"%{query}%")
            )

        if category:
            collection_query = collection_query.filter(
                Collection.category.ilike(category)
            )

        for collection in collection_query.all():
            results.append({
                "type": "collection",
                "id": collection.id,
                "name": collection.name,
                "category": collection.category,
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
        ).add_entity(
            Collection
        ).filter(
            Item.status == "approved",
            Collection.status == "approved"
        )

        if query:
            item_query = item_query.filter(
                Item.name.ilike(f"%{query}%")
            )

        if category:
            item_query = item_query.filter(
                Collection.category.ilike(category)
            )

        if collection_id:
            item_query = item_query.filter(
                Item.collection_id == collection_id
            )

        for item, collection in item_query.all():
            results.append({
                "type": "item",
                "id": item.id,
                "name": item.name,
                "category": collection.category,
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
        ).add_entity(
            Item
        ).add_entity(
            Collection
        ).filter(
            Listing.status == "available",
            Item.status == "approved",
            Collection.status == "approved"
        )

        if query:
            listing_query = listing_query.filter(
                Item.name.ilike(f"%{query}%")
            )

        if category:
            listing_query = listing_query.filter(
                Collection.category.ilike(category)
            )

        if collection_id:
            listing_query = listing_query.filter(
                Item.collection_id == collection_id
            )

        for listing, item, collection in listing_query.all():
            results.append({
                "type": "marketplace",
                "id": listing.id,
                "name": item.name,
                "category": collection.category,
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
        category=category,
        collection_id=collection_id,
        sort=sort,
        categories=categories,
        collections=collections
    )
    
#Display and search approved collectible items
@browse_bp.route("/items")
def browse_items():
    #Get the keyword from the search box
    query = request.args.get("q", "").strip()
    collection_id = request.args.get(
        "collection_id",
        ""
    ).strip()
    
    items_query = Item.query.filter_by(
        status="approved"
    )
    
    #Search by item name
    if query:
        items_query = items_query.filter(
            Item.name.ilike(f"%{query}%")
        )

    #Filter items by collection
    if collection_id:
        items_query = items_query.filter(
            Item.collection_id == collection_id
        )

    items = items_query.order_by(
        Item.created_at.desc()
    ).all()

    #Get collections for the dropdown menu
    collections = Collection.query.filter_by(
        status="approved"
    ).order_by(
        Collection.name.asc()
    ).all()

    return render_template(
        "items.html",
        items=items,
        query=query,
        collections=collections,
        selected_collection=collection_id
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