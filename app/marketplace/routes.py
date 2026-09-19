from flask import render_template, request, redirect, url_for
from flask_login import login_required, current_user
from app.models import Item, OwnedItem, Listing, Transaction, User, Collection
from app.extensions import db
from app.marketplace import marketplace_bp
from sqlalchemy import or_
from sqlalchemy.orm import aliased  #for transaction history used(show buyer and seller)
from datetime import timedelta  #for me to change the time to Malaysia Time(cuz default is UTC+0)

#Display all available marketplace listings.
@marketplace_bp.route("/")
def marketplace_home():
    listings = Listing.query.join(
        Item,
        Listing.item_id == Item.id
    ).add_entity(
        Item
    ).filter(
        Listing.status == "available"
    ).order_by(
        Listing.created_at.desc()
    ).all()

    return render_template(
        "marketplace_list.html",
        listings=listings
    )
    
#Create Listing page.
#Login is required before the user can access this page.
@marketplace_bp.route("/create", methods=["GET", "POST"])
@login_required #(check whether user login or not; if not,system will ask user to login 1st)
def create_listing():
         
    #Get items owned by the currently logged-in user.
    owned_items = Item.query.join(
        OwnedItem,
        Item.id == OwnedItem.item_id
    ).filter(
        OwnedItem.user_id == current_user.id,
        OwnedItem.quantity > 0
    ).order_by(
        Item.name.asc()
    ).all()
    
    #Store available items under their collection ID.
    items_by_collection = {}
    
    for item in owned_items:
        items_by_collection.setdefault(
            item.collection_id,
            []
        ).append(item)
            
    #Get collections that contain available items to list.
    collections = Collection.query.filter(
        Collection.id.in_(list(items_by_collection))
    ).order_by(
        Collection.name.asc()
    ).all()
    
    #Only show items that not listed yet
    available_items = []

    for item in owned_items:
        active_listing_count = Listing.query.filter(
            Listing.user_id == current_user.id,
            Listing.item_id == item.id,
            Listing.status.in_(["available", "pending", "unavailable"])
        ).count()

        #Add the item only when it has no active listing
        if active_listing_count == 0:
            available_items.append(item)

    #The HTML dropdown will use this filtered item list.
    owned_items = available_items
    
    #Show the create form again with an error message.
    def show_form_error(message):
        return render_template(
            "marketplace_create.html",
            owned_items=owned_items,
            collections=collections,
            items_by_collection=items_by_collection,
            error=message
        )
        
    #When the user first time open the page, show the form
    if request.method == "GET":
            return render_template(
                "marketplace_create.html",
                owned_items=owned_items,
                collections=collections,
                items_by_collection=items_by_collection
            )
    
    #Read the values submitted by the user.
    item_id = request.form.get("item_id")
    condition = request.form.get("condition")
    listing_type = request.form.get("listing_type")
    description = request.form.get("description")
    price = request.form.get("price")

    #Check that the user selected an item.
    if not item_id:
        return show_form_error(
            "Please select an item before creating a listing."
        )

    #A Sell listing must have a price.
    if listing_type == "sell" and not price:
        return show_form_error(
            "Please enter a price for a Sell listing."
        )

    #Check that the selected item belongs to the current user.
    owned_item = OwnedItem.query.filter_by(
        user_id=current_user.id,
        item_id=item_id
    ).first()

    if not owned_item or owned_item.quantity <= 0:
        return show_form_error(
            "You can only create a listing for an item you own."
        )
        
    #Count existing listings that still reserve this owned item.
    active_listing_count = Listing.query.filter(
        Listing.user_id == current_user.id,
        Listing.item_id == owned_item.item_id,
        Listing.status.in_(["available", "pending", "unavailable"])
    ).count()

    #Prevent the user from creating multiple listings at the same time
    if active_listing_count > 0:
        return show_form_error(
            "This item already has an active listing."
        )
    
    #Convert the price text into a number before saving.
    listing_price = None

    if listing_type == "sell":
        try:
            listing_price = float(price)
        except ValueError:
            return show_form_error(
                "Please enter a valid price for a Sell listing."
            )

    #A trade listing must not have a price.
    elif listing_type == "trade":
        if price:
            return show_form_error(
                "Trade listings should not have a price!"
            )

        listing_price = None

    else:
        if listing_type not in ("sell", "trade"):
            return show_form_error(
                "Please choose a valid listing type."
            )


    #Create a new marketplace listing record.
    new_listing = Listing(
        user_id=current_user.id,
        item_id=owned_item.item_id,
        listing_type=listing_type,
        price=listing_price,
        condition=condition,
        description=description,
        status="available"
    )

    #Save the new listing into the database.
    db.session.add(new_listing)
    db.session.commit()

    return redirect(
        url_for("marketplace.my_listings")
    )

#Display listings created by the current user.
@marketplace_bp.route("/my-listings")
@login_required
def my_listings():

    #Get only listings that belong to the logged-in user.
    listings = db.session.query(
        Listing,
        Item
    ).join(
        Item,
        Listing.item_id == Item.id
    ).filter(
        Listing.user_id == current_user.id
    ).order_by(
        Listing.created_at.desc()
    ).all()

    return render_template(
        "my_listings.html",
        listings=listings
    )
    
#Mark one of the current user's listings as unavailable.
@marketplace_bp.route(
    "/<int:listing_id>/unavailable",
    methods=["POST"]
)
@login_required
def mark_listing_unavailable(listing_id):

    #Find the listing only if it belongs to the logged-in user.
    listing = Listing.query.filter_by(
        id=listing_id,
        user_id=current_user.id
    ).first_or_404()
    
    #Find the item connected to this listing.
    item = Item.query.filter_by(
        id=listing.item_id
    ).first_or_404()

    #Change status to unavailable
    listing.status = "unavailable"

    #Save the new status in the database.
    db.session.commit()

    #Return the user to their My Listings page.
    return redirect(
        url_for("marketplace.my_listings")
    )

#Make one of the current user's listings available again.
@marketplace_bp.route(
    "/<int:listing_id>/available",
    methods=["POST"]
)
@login_required
def mark_listing_available(listing_id):

    #Find the listing only if it belongs to the logged-in user.
    listing = Listing.query.filter_by(
        id=listing_id,
        user_id=current_user.id
    ).first_or_404()

    #Make the listing visible in the public marketplace again.
    listing.status = "available"

    #Save the updated status.
    db.session.commit()

    #Return the user to My Listings page.
    return redirect(
        url_for("marketplace.my_listings")
    ) 
    
#Delete one of the current user's listings.
@marketplace_bp.route(
    "/<int:listing_id>/delete",
    methods=["POST"]
)
@login_required
def delete_listing(listing_id):

    #Find the listing only if it belongs to the logged-in user.
    listing = Listing.query.filter_by(
        id=listing_id,
        user_id=current_user.id
    ).first_or_404()

    #Remove the listing record from the database.
    db.session.delete(listing)
    db.session.commit()

    #Return the user to My Listings page.
    return redirect(
        url_for("marketplace.my_listings")
    )
    
#Show or update one listing owned by the logged-in user.
@marketplace_bp.route(
    "/<int:listing_id>/edit",
    methods=["GET", "POST"]
)

@login_required
def edit_listing(listing_id):

    #Find the listing only when it belongs to the logged-in user.
    listing = Listing.query.filter_by(
        id=listing_id,
        user_id=current_user.id
    ).first_or_404()

    #Find the item connected to this listing.
    item = Item.query.filter_by(
        id=listing.item_id
    ).first_or_404()
    
    if request.method == "GET":
        return render_template(
            "marketplace_edit.html",
            listing=listing,
            item=item
        )

    #read the new values submitted by the edit form.
    condition = request.form.get("condition", "").strip()
    listing_type = request.form.get("listing_type", "").strip()
    description = request.form.get("description", "").strip()
    price = request.form.get("price", "").strip()

    #for sell must enter a price (cannot leave empty)
    if listing_type == "sell":
        try:
            listing.price = float(price)
        except ValueError:
            return "Please enter a valid price for a sell listing."

    #A trade listing must not have a price.
    elif listing_type == "trade":
        if price:
            return "Trade listings should not have a price."

        listing.price = None

    #Reject an invalid listing type.
    else:
        return "Please choose Sell or Trade."

    #Update the editable listing information.
    listing.condition = condition
    listing.listing_type = listing_type
    listing.description = description

    #Save the changes to the database.
    db.session.commit()

    #Return to My Listings after a successful update.
    return redirect(
        url_for("marketplace.my_listings")
    )




#NOW IS FOR BUY
#Show the details of one marketplace listing.
@marketplace_bp.route("/<int:listing_id>")
def view_listing(listing_id):

    #Find the marketplace listing using its ID.
    listing = Listing.query.filter_by(
        id=listing_id
    ).first_or_404()

    #Find the item connected to this listing.
    item = Item.query.filter_by(
        id=listing.item_id
    ).first_or_404()

    #Send the listing and item information to the detail page.
    return render_template(
        "marketplace_detail.html",
        listing=listing,
        item=item
    )

#Show the purchase confirmation page or complete the purchase
@marketplace_bp.route(
    "/<int:listing_id>/purchase",
    methods=["GET", "POST"]
)
@login_required
def purchase_listing(listing_id):

    #Only available sell listings can be purchased.
    listing = Listing.query.filter_by(
        id=listing_id,
        status="available",
        listing_type="sell"
    ).first_or_404()

    #A user cannot purchase their own listing.
    if listing.user_id == current_user.id:
        return "You cannot purchase your own listing."

    #Find the item connected to this listing.
    item = Item.query.filter_by(
        id=listing.item_id
    ).first_or_404()

    #GET: show the confirmation page.
    if request.method == "GET":
        return render_template(
            "marketplace_purchase_confirm.html",
            listing=listing,
            item=item
        )

    #POST: create a completed transaction record.
    new_transaction = Transaction(
        listing_id=listing.id,
        buyer_id=current_user.id,
        seller_id=listing.user_id,
        item_id=item.id,
        price=listing.price,
        status="completed"
    )

    #Change the listing so it cannot be purchased again.
    listing.status = "sold"

    #Save both the transaction and listing status together.
    db.session.add(new_transaction)
    db.session.commit()

    return "Purchase completed successfully."


#TRANSACTION HISTORY
#Show transactions where the current user is the buyer or seller.
@marketplace_bp.route("/transactions")
@login_required
def transaction_history():

    #Create two names for the User table: one for the buyer and one for the seller.
    Buyer = aliased(User)
    Seller = aliased(User)

    #Get transactions related to the logged-in user.
    transactions = db.session.query(
        Transaction,
        Item,
        Buyer,
        Seller
    ).join(
        Item,
        Transaction.item_id == Item.id
    ).join(
        Buyer,
        Transaction.buyer_id == Buyer.id
    ).join(
        Seller,
        Transaction.seller_id == Seller.id
    ).filter(
        or_(
            Transaction.buyer_id == current_user.id,
            Transaction.seller_id == current_user.id
        )
    ).order_by(
        Transaction.created_at.desc()
    ).all()

    #Send all transaction information to the history page.
    return render_template(
        "marketplace_history.html",
        transactions=transactions,
        malaysia_offset=timedelta(hours=8)
    )