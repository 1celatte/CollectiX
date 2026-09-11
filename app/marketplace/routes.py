from flask import render_template, request, redirect, url_for
from flask_login import login_required, current_user
from app.models import Item, OwnedItem, Listing
from app.extensions import db
from app.marketplace import marketplace_bp


#Temporary route used to test the Marketplace module.
@marketplace_bp.route("/")
def marketplace_home():
    return "Marketplace module is working!"

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
    
    #When the user first time open the page, show the form
    if request.method == "GET":
            return render_template(
                "marketplace_create.html",
                owned_items=owned_items
            )
    
    #Read the values submitted by the user.
    item_id = request.form.get("item_id")
    condition = request.form.get("condition")
    listing_type = request.form.get("listing_type")
    description = request.form.get("description")
    price = request.form.get("price")

    #Check that the user selected an item.
    if not item_id:
        return "Please select an item before creating a listing."

    #A Sell listing must have a price.
    if listing_type == "sell" and not price:
        return "Please enter a price for a Sell listing."

    #Check that the selected item belongs to the current user.
    owned_item = OwnedItem.query.filter_by(
        user_id=current_user.id,
        item_id=item_id
    ).first()

    if not owned_item or owned_item.quantity <= 0:
        return "You can only create a listing for an item you own."
    
    #Convert the price text into a number before saving.
    listing_price = None

    if listing_type == "sell":
        try:
            listing_price = float(price)
        except ValueError:
            return "Please enter a valid price for a Sell listing."

    elif listing_type == "trade" and price:
        try:
            listing_price = float(price)
        except ValueError:
            return "Please enter a valid price."

    else:
        if listing_type not in ("sell", "trade"):
            return "Please choose a valid listing type."


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

    return "Listing created successfully."

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

    # Change its status so it is no longer available.
    listing.status = "unavailable"

    # Save the new status in the database.
    db.session.commit()

    # Return the user to their My Listings page.
    return redirect(
        url_for("marketplace.my_listings")
    )