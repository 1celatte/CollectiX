from flask import render_template, request
from app.browse import browse_bp
from app.models import Collection, Item

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

    #Run the database query
    collections = collections_query.all()

    #Send all the collections(results) to HTML page
    return render_template(
        "browse/browse.html",
        collections=collections,
        query=query,
        category=category,
        sort=sort
    )
    
#Display all the approved collectible items
@browse_bp.route("/items")
def browse_items():
    items = Item.query.filter_by(
        status="approved"
    ).order_by(
        Item.created_at.desc()
    ).all()

    return render_template(
        "browse/items.html",
        items=items
    )