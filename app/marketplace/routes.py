from flask import render_template, request
from flask_login import login_required, current_user
from app.models import Item, OwnedItem
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
            return render_template("marketplace_create.html")
    
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
    
    #Temporary test: confirm that the form data passed validation.
    return "Listing details are valid and ready to save."