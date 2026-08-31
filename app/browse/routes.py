from flask import render_template, request
from app.browse import browse_bp
from app.models import Collection, Item, Listing

#Browse all public collections
@browse_bp.route("/")
def browse_page():
    #Get the keyword from the search box
    query = request.args.get("q","").strip()
    
    #Get the selected category
    category = request.args.get("category", "").strip()

    #Get the selected sorting option
    sort = request.args.get("sort", "newest")
    
    #Start with approved public collections
    collections_query = Collection.query.filter_by(
        status="approved"
    )
    
    #Search by collection name
    if query:
        collections_query = collections_query.filter(
            Collection.name.ilike(f"%{query}%")
        )
         
    # Filter by category
    if category:
        collections_query = collections_query.filter(
            Collection.category.ilike(category)
        )

    #Sort the results
    if sort == "oldest":
        collections_query = collections_query.order_by(
            Collection.created_at.asc()
        )
    elif sort == "name":
        collections_query = collections_query.order_by(
            Collection.name.asc()
        )
    else:
        collections_query = collections_query.order_by(
            Collection.created_at.desc()
        )

    #Run the collection query
    collections = collections_query.all()

    #Get categories from approved collections
    categories = [
        row[0]
        for row in Collection.query.with_entities(
            Collection.category
        ).filter(
            Collection.status == "approved",
            Collection.category.isnot(None)
        ).distinct().order_by(
            Collection.category
        ).all()
    ]
            
    return render_template(
        "browse/browse.html",
        collections=collections,
        query=query,
        category=category,
        sort=sort,
        categories=categories
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
        "browse/items.html",
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
        "browse/marketplace.html",
        listings=listings,
        sort=sort
    )