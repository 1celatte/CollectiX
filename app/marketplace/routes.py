from flask import render_template, request, redirect, url_for, abort
from flask_login import login_required, current_user
from app.models import Item, OwnedItem, Listing, Transaction, User, Collection, UserCollection, PaymentQR, Trade
from app.extensions import db
from app.marketplace import marketplace_bp
from sqlalchemy import or_
from sqlalchemy.orm import aliased  #for transaction history used(show buyer and seller)
from datetime import timedelta  #to change the time to Malaysia Time(cuz default is UTC+0)
import os  #create the image folder and file path
from uuid import uuid4  #give each uploaded image a unique filename
from werkzeug.utils import secure_filename  #make the uploaded filename safe


#======================================================================
# DISPLAY ALL AVAILABLE MARKETPLACE LISTINGS
#======================================================================
@marketplace_bp.route("/")
def marketplace_home():
    listings = Listing.query.join(
        Item,
        Listing.item_id == Item.id
    ).join(
        User,
        Listing.user_id == User.id
    ).add_entity(
        Item
    ).filter(
        Listing.status == "available",
        User.is_banned == False
    ).order_by(
        Listing.created_at.desc()
    ).all()

    return render_template(
        "view_marketplace.html",
        listings=listings
    )
    
#====================================================================================================================================

# FIND A MISSING ITEM IN THE MARKETPLACE(let user find the item they want to buy in the marketplace)

#=======================================================================================================================================

@marketplace_bp.route(
    "/find/<int:collection_id>/<int:item_id>"
)
@login_required
def find_missing_item(collection_id, item_id):

    # Get the selected item
    item = Item.query.filter_by(
        id=item_id,
        collection_id=collection_id,
        status="approved"
    ).first_or_404()

    # Get the collection
    collection = Collection.query.get_or_404(
        collection_id
    )

    # Find available marketplace listings
    listings = Listing.query.join(
        User,
        Listing.user_id == User.id
    ).filter(
        Listing.item_id == item.id,
        Listing.status == "available",
        User.is_banned == False
    ).order_by(
        Listing.created_at.desc()
    ).all()

    return render_template(
        "marketplace_find_item.html",
        collection=collection,
        item=item,
        listings=listings
    )
    
#======================================================================
# CREATE LISTING
#======================================================================
@marketplace_bp.route("/create", methods=["GET", "POST"])
@login_required #(check whether user login or not; if not,system will ask user to login 1st)
def create_listing():
    
    #Check whether the seller has uploaded their DuitNow for buyer to pay later
    payment_qr = PaymentQR.query.filter_by(
        user_id=current_user.id
    ).first()
       
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
    
    #Only show items that not listed yet
    available_items = []

    for item in owned_items:
        active_listing_count = Listing.query.filter(
            Listing.user_id == current_user.id,
            Listing.item_id == item.id,
            Listing.status.in_(["available", "pending", "unavailable"])
        ).count()

        #Get the quantity the current user owns for this item.
        owned_item = OwnedItem.query.filter_by(
            user_id=current_user.id,
            item_id=item.id
        ).first()

        #Show the item while the user has more copies than active listings.
        if owned_item and active_listing_count < owned_item.quantity:
            available_items.append(item)

    #The HTML dropdown will use this filtered item list.
    owned_items = available_items
    
    #COLLECTION ID, NAME, ITEM
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
        
    #Show the create form again with an error message.
    def show_form_error(message):
        return render_template(
            "create_new_listing.html",
            owned_items=owned_items,
            collections=collections,
            items_by_collection=items_by_collection,
            error=message
        )
        
    #When the user first time open the create listing page, show the form
    if request.method == "GET":
            return render_template(
        "create_new_listing.html",
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
    
    #Only Sell listings require a DuitNow QR.
    if listing_type == "sell" and not payment_qr:
        return redirect(
            url_for(
                "marketplace.payment_qr_settings",
                required="must_upload_qr"
            )
        )
    
    #Get the image file selected by the user.
    image_file = request.files.get("image")
    
    image_filename = None

    if image_file and image_file.filename:
        original_filename = secure_filename(
            image_file.filename
        )

        image_filename = (
            f"{uuid4().hex}_{original_filename}"
        )

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

    #Prevent listings from exceeding the quantity the user owns.
    if active_listing_count >= owned_item.quantity:
        return show_form_error(
            "You have already listed all copies of this item."
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
        image=image_filename,
        status="available"
    )

    #Save the new listing into the database.
    db.session.add(new_listing)
    db.session.commit()

    #Save the uploaded image file in the app static folder.
    if image_file and image_filename:
        upload_folder = os.path.join(
            marketplace_bp.root_path,
            "static",
            "uploads",
            "listings"
        )

        os.makedirs(
            upload_folder,
            exist_ok=True
        )

        image_file.save(
            os.path.join(
                upload_folder,
                image_filename
            )
        )
        
    return redirect(
        url_for("marketplace.my_listings")
    )

#======================================================================
# MY LISTINGS :  display listings created by the current user
#======================================================================
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

#====================================================================== 
# SHOW THE SELLER DUITNOW QR
#======================================================================
@marketplace_bp.route(
    "/payment-qr",
    methods=["GET", "POST"]
)
@login_required
def payment_qr_settings():

    #Find the current seller's saved DuitNow QR.
    payment_qr = PaymentQR.query.filter_by(
        user_id=current_user.id
    ).first()
    
    #Show the page when the seller opens it.
    if request.method == "GET":
        return render_template(
            "payment_qr_settings.html",
            payment_qr=payment_qr
        )

    #Get the QR image submitted through the form.
    qr_file = request.files.get("payment_qr")

    #Do not save if the seller did not choose an image.
    if not qr_file or not qr_file.filename:
        return render_template(
            "payment_qr_settings.html",
            payment_qr=payment_qr,
            error="Please select a payment QR image."
        )

    #Make the uploaded filename safe and unique.
    original_filename = secure_filename(qr_file.filename)
    qr_filename = f"{uuid4().hex}_{original_filename}"

    #Create the folder for seller payment QR images if needed.
    upload_folder = os.path.join(
        marketplace_bp.root_path,
        "static",
        "uploads",
        "payment_qrs"
    )
    os.makedirs(upload_folder, exist_ok=True)

    #Save the QR image file in the marketplace static folder.
    qr_file.save(
        os.path.join(upload_folder, qr_filename)
    )

    #Update an existing QR, or create the seller's first QR record.
    if payment_qr:
        payment_qr.filename = qr_filename
    else:
        payment_qr = PaymentQR(
            user_id=current_user.id,
            filename=qr_filename
        )
        db.session.add(payment_qr)

    #Save the QR filename to the database.
    db.session.commit()

    return redirect(
        url_for("marketplace.my_listings")
    )

#======================================================================
# SELLER DELETE THEIR DUITNOW QR
#======================================================================
@marketplace_bp.route(
    "/payment-qr/delete",
    methods=["POST"]
)
@login_required
def delete_payment_qr():

    #Seller can't delete their QR if they got active listing
    active_listing = Listing.query.filter(
        Listing.user_id == current_user.id,
        Listing.status.in_(
            ["available", "unavailable", "pending"]
        )
    ).first()

    if active_listing:
        payment_qr = PaymentQR.query.filter_by(
            user_id=current_user.id
        ).first()

        return render_template(
            "payment_qr_settings.html",
            payment_qr=payment_qr,
            error=(
                "You cannot delete your DuitNow QR while you have active listings or pending purchases!"
            )
        )

    #Find only the current seller's QR record.
    payment_qr = PaymentQR.query.filter_by(
        user_id=current_user.id
    ).first_or_404()

    #Delete the QR image file from the project folder.
    qr_file_path = os.path.join(
        marketplace_bp.root_path,
        "static",
        "uploads",
        "payment_qrs",
        payment_qr.filename
    )

    if os.path.exists(qr_file_path):
        os.remove(qr_file_path)

    #Delete the QR record from the database.
    db.session.delete(payment_qr)
    db.session.commit()

    return redirect(
        url_for("marketplace.my_listings")
    )

#====================================================================== 
# SELLER MARK ONE OF THE LISTING AS UNAVAILABLE
#======================================================================
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

    #Show the edit form again with a validation error message.
    def show_form_error(message):
        return render_template(
            "edit_listing.html",
            listing=listing,
            item=item,
            error=message
        )
    
    #Change status to unavailable
    listing.status = "unavailable"

    #Save the new status in the database.
    db.session.commit()

    #Return the user to their My Listings page.
    return redirect(
        url_for("marketplace.my_listings")
    )

#======================================================================
# SELLER MAKE A LISTING AVAILABLE AGAIN
#======================================================================
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
    
#======================================================================
# SELLER DELETE ONE OF THEIR LISTING
#======================================================================
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

    #Remember the image filename before deleting the listing.
    image_filename = listing.image
    
    #Remove the listing record from the database.
    db.session.delete(listing)
    db.session.commit()
    
    #Remove the uploaded image file if this listing has one.
    if image_filename:
        image_path = os.path.join(
            marketplace_bp.root_path,
            "static",
            "uploads",
            "listings",
            image_filename
        )

        if os.path.exists(image_path):
            os.remove(image_path)

    #Return the user to My Listings page.
    return redirect(
        url_for("marketplace.my_listings")
    )

#======================================================================
# SELLER EDIT LISTING
#======================================================================
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
            "edit_listing.html",
            listing=listing,
            item=item
        )

    #read the new values submitted by the edit form.
    condition = request.form.get("condition", "").strip()
    listing_type = request.form.get("listing_type", "").strip()
    description = request.form.get("description", "").strip()
    price = request.form.get("price", "").strip()

    #Get the new image file only when the user selected one.
    image_file = request.files.get("image")
    image_filename = None

    if image_file and image_file.filename:
        original_filename = secure_filename(
            image_file.filename
        )

        image_filename = (
            f"{uuid4().hex}_{original_filename}"
        )

    #for sell must enter a price (cannot leave empty)
    if listing_type == "sell":
        try:
            listing.price = float(price)
        except ValueError:
            return show_form_error(
                "Please enter a valid price for a Sell listing."
            )

    #A trade listing must not have a price.
    elif listing_type == "trade":
        if price:
            return show_form_error(
                "Trade listings should not have a price."
            )

        listing.price = None

    #Reject an invalid listing type.
    else:
        return show_form_error(
            "Please choose Sell or Trade."
        )

    #Update the editable listing information.
    listing.condition = condition
    listing.listing_type = listing_type
    listing.description = description

    #Replace the listing image only when a new image was uploaded.
    if image_filename:
        listing.image = image_filename

    #Save the changes to the database.
    db.session.commit()

    #Save the new uploaded image file in the app static folder.
    if image_file and image_filename:
        upload_folder = os.path.join(
            marketplace_bp.root_path,
            "static",
            "uploads",
            "listings"
        )

        os.makedirs(
            upload_folder,
            exist_ok=True
        )

        image_file.save(
            os.path.join(
                upload_folder,
                image_filename
            )
        )

    #Return to My Listings after a successful update.
    return redirect(
        url_for("marketplace.my_listings")
    )

#======================================================================
#NOW IS FOR BUY
#======================================================================

#======================================================================
# VIEW LISTING: show the details of the marketplace listing
#======================================================================
@marketplace_bp.route("/<int:listing_id>")
def view_listing(listing_id):

    #Find the marketplace listing using its ID.
    listing = Listing.query.join(
        User,
        Listing.user_id == User.id
    ).filter(
        Listing.id == listing_id,
        User.is_banned == False
    ).first_or_404()

    #Find the item connected to this listing.
    item = Item.query.filter_by(
        id=listing.item_id
    ).first_or_404()

    #Send the listing and item information to the detail page.
    return render_template(
        "view_details.html",
        listing=listing,
        item=item
    )

#======================================================================
# SEND TRADE REQUEST
#======================================================================
@marketplace_bp.route(
    "/<int:listing_id>/trade-request",
    methods =["GET", "POST"]
)
@login_required
def send_trade_request(listing_id):

    #Only available Trade listings can receive a Trade request.
    listing = Listing.query.filter_by(
        id=listing_id,
        status="available",
        listing_type="trade"
    ).first_or_404()

    #Users cannot request their own Trade listing.
    if listing.user_id == current_user.id:
        return "You cannot send a Trade request for your own listing."

    #Get the item offered by the listing owner.
    requested_item = Item.query.get_or_404(listing.item_id)
    seller = User.query.get_or_404(listing.user_id)

    #Show items owned by the requester that can be offered.
    offered_items = Item.query.join(
        OwnedItem,
        Item.id == OwnedItem.item_id
    ).filter(
        OwnedItem.user_id == current_user.id,
        OwnedItem.quantity > 0,
        Item.id != requested_item.id
    ).order_by(
        Item.name.asc()
    ).all()

    #Group the offerable items by collection.
    items_by_collection = {}

    for offered_item in offered_items:
        items_by_collection.setdefault(
            offered_item.collection_id,
            []
        ).append(offered_item)

    #Get only collections that contain an item the requester can offer.
    collections = Collection.query.filter(
        Collection.id.in_(list(items_by_collection))
    ).order_by(
        Collection.name.asc()
    ).all()

    if request.method == "GET":
        return render_template(
            "send_trade_request.html",
            listing=listing,
            seller=seller,
            requested_item=requested_item,
            offered_items=offered_items,
            collections=collections,
            items_by_collection=items_by_collection
        )
        
    #Get the item selected by the requester.
    offered_item_id = request.form.get("offered_item_id")
    offered_condition = request.form.get("offered_condition")

    if not offered_item_id:
        return "Please select an item to offer."
    
    if not offered_condition:
        return "Please select the condition of your item."
    
    #Get the optionalimage uploaded for the offered item.
    offered_image_file = request.files.get("offered_image")

    offered_image_filename = None

    if offered_image_file and offered_image_file.filename:
        original_filename = secure_filename(
            offered_image_file.filename
        )

        offered_image_filename = (
            f"{uuid4().hex}_{original_filename}"
        )

        upload_folder = os.path.join(
            marketplace_bp.root_path,
            "static",
            "uploads",
            "trades"
        )

        os.makedirs(
            upload_folder,
            exist_ok=True
        )

        offered_image_file.save(
            os.path.join(
                upload_folder,
                offered_image_filename
            )
        )

    #Check that the selected offered item belongs to the requester.
    offered_owned_item = OwnedItem.query.filter_by(
        user_id=current_user.id,
        item_id=offered_item_id
    ).first()

    if not offered_owned_item or offered_owned_item.quantity <= 0:
        return "You can only offer an item that you own."

    #The requester cannot offer the same item they want to receive.
    if offered_owned_item.item_id == requested_item.id:
        return "You cannot offer the same item for this Trade."

    #Create a pending Trade request.
    new_trade = Trade(
        sender_id=current_user.id,
        receiver_id=listing.user_id,
        listing_id=listing.id,
        offered_item_id=offered_owned_item.item_id,
        offered_condition=offered_condition,
        offered_image=offered_image_filename,
        requested_item_id=requested_item.id,
        status="pending"
    )

    #Reserve this Trade listing while the owner reviews the request.
    listing.status = "pending"

    db.session.add(new_trade)
    db.session.commit()

    return redirect(
        url_for("marketplace.marketplace_home")
    )

#======================================================================
# VIEW TRADE REQUESTS
#======================================================================
@marketplace_bp.route("/trade-requests")
@login_required
def view_trade_requests():
    trades = Trade.query.filter_by(
        receiver_id=current_user.id,
        status="pending"
    ).all()

    trade_details = []

    for trade in trades:
        sender = User.query.get_or_404(trade.sender_id)

        offered_item = Item.query.get_or_404(
            trade.offered_item_id
        )

        requested_item = Item.query.get_or_404(
            trade.requested_item_id
        )

        #Get the original Trade listing requested by the sender.
        listing = Listing.query.get_or_404(
            trade.listing_id
        )

        trade_details.append({
            "trade": trade,
            "sender": sender,
            "offered_item": offered_item,
            "requested_item": requested_item,
            "listing": listing
        })

    return render_template(
        "trade_requests.html",
        trade_details=trade_details
    )

#======================================================================
# ACCEPT TRADE REQUESTS
#======================================================================
@marketplace_bp.route(
    "/trade-requests/<int:trade_id>/accept",
    methods=["POST"]
)
@login_required
def accept_trade_request(trade_id):
    trade = Trade.query.filter_by(
        id=trade_id,
        receiver_id=current_user.id,
        status="pending"
    ).first_or_404()

    #Only accept a Trade Request while its listing is still available.
    listing = Listing.query.filter_by(
        id=trade.listing_id,
        user_id=current_user.id,
        status="available"
    ).first()

    if not listing:
        return "This Trade listing is no longer available."

    #Check that the sender still owns the item they offered.
    sender_owned_item = OwnedItem.query.filter_by(
        user_id=trade.sender_id,
        item_id=trade.offered_item_id
    ).first()

    #Check that the listing owner still owns the requested item.
    receiver_owned_item = OwnedItem.query.filter_by(
        user_id=current_user.id,
        item_id=trade.requested_item_id
    ).first()

    if not sender_owned_item or sender_owned_item.quantity <= 0:
        return "The requester no longer has the offered item."

    if not receiver_owned_item or receiver_owned_item.quantity <= 0:
        return "You no longer have the requested item."

    #Both users still own their items, so the Trade is accepted.
    trade.status = "accepted"

    #Hide this listing while the accepted Trade is in progress.
    listing.status = "trading"

    db.session.commit()

    return redirect(
        url_for("marketplace.trade_history")
    )

#======================================================================
# REJECT TRADE REQUEST
#======================================================================
@marketplace_bp.route(
    "/trade-requests/<int:trade_id>/reject",
    methods=["POST"]
)
@login_required
def reject_trade_request(trade_id):
    trade = Trade.query.filter_by(
        id=trade_id,
        receiver_id=current_user.id,
        status="pending"
    ).first_or_404()

    listing = Listing.query.get_or_404(
        trade.listing_id
    )

    #Get the listing owner's reason for rejecting the Trade Request.
    rejection_reason = request.form.get(
        "rejection_reason",
        ""
    ).strip()

    if not rejection_reason:
        return "Please enter a reason for rejecting the Trade Request."

    #Reject the request and make the Trade listing available again.
    trade.rejection_reason = rejection_reason
    trade.status = "rejected"
    listing.status = "available"

    db.session.commit()

    return redirect(
        url_for("marketplace.view_trade_requests")
    )

#======================================================================
# CONFIRM TRADE ITEM RECEIVED
#======================================================================
@marketplace_bp.route(
    "/trades/<int:trade_id>/confirm-item-received",
    methods=["POST"]
)
@login_required
def confirm_trade_item_received(trade_id):

    #Only an accepted Trade can be confirmed as received.
    trade = Trade.query.filter_by(
        id=trade_id,
        status="accepted"
    ).first_or_404()

    #Record confirmation from the Trade requester.
    if trade.sender_id == current_user.id:
        trade.sender_received = True

    #Record confirmation from the owner of the requested listing.
    elif trade.receiver_id == current_user.id:
        trade.receiver_received = True

    #Block users who are not involved in this Trade.
    else:
        abort(403)

    #Exchange the items only after both users confirm receiving them.
    if trade.sender_received and trade.receiver_received:

        sender_owned_item = OwnedItem.query.filter_by(
            user_id=trade.sender_id,
            item_id=trade.offered_item_id
        ).first()

        receiver_owned_item = OwnedItem.query.filter_by(
            user_id=trade.receiver_id,
            item_id=trade.requested_item_id
        ).first()

        #Stop the Trade if either user no longer owns their item.
        if not sender_owned_item or sender_owned_item.quantity <= 0:
            return "The requester no longer has the offered item."

        if not receiver_owned_item or receiver_owned_item.quantity <= 0:
            return "The listing owner no longer has the requested item."

        offered_item = Item.query.get_or_404(
            trade.offered_item_id
        )

        requested_item = Item.query.get_or_404(
            trade.requested_item_id
        )

        #Remove one item from each original owner.
        sender_owned_item.quantity -= 1
        receiver_owned_item.quantity -= 1

        #Give the requested item to the Trade requester.
        sender_received_item = OwnedItem.query.filter_by(
            user_id=trade.sender_id,
            item_id=trade.requested_item_id
        ).first()

        if sender_received_item:
            sender_received_item.quantity += 1
        else:
            db.session.add(
                OwnedItem(
                    user_id=trade.sender_id,
                    item_id=trade.requested_item_id,
                    quantity=1
                )
            )

        #Give the offered item to the listing owner.
        receiver_received_item = OwnedItem.query.filter_by(
            user_id=trade.receiver_id,
            item_id=trade.offered_item_id
        ).first()

        if receiver_received_item:
            receiver_received_item.quantity += 1
        else:
            db.session.add(
                OwnedItem(
                    user_id=trade.receiver_id,
                    item_id=trade.offered_item_id,
                    quantity=1
                )
            )

        #Add the requested item's collection to the sender if needed.
        sender_collection = UserCollection.query.filter_by(
            user_id=trade.sender_id,
            collection_id=requested_item.collection_id
        ).first()

        if not sender_collection:
            db.session.add(
                UserCollection(
                    user_id=trade.sender_id,
                    collection_id=requested_item.collection_id
                )
            )

        #Add the offered item's collection to the receiver if needed.
        receiver_collection = UserCollection.query.filter_by(
            user_id=trade.receiver_id,
            collection_id=offered_item.collection_id
        ).first()

        if not receiver_collection:
            db.session.add(
                UserCollection(
                    user_id=trade.receiver_id,
                    collection_id=offered_item.collection_id
                )
            )

        #Finish the Trade and close its original listing.
        listing = Listing.query.get_or_404(
            trade.listing_id
        )

        trade.status = "completed"
        listing.status = "traded"

    db.session.commit()

    return redirect(
        url_for("marketplace.trade_history")
    )
    
#======================================================================
# VIEW TRADE HISTORY
#======================================================================
@marketplace_bp.route("/trade-history")
@login_required
def trade_history():
    
    #Get all Trades history.
    trades = Trade.query.filter(
        or_(
            Trade.sender_id == current_user.id,
            Trade.receiver_id == current_user.id
        )
    ).order_by(
        Trade.id.desc()
    ).all()

    #Store each Trade together with its related users and items.
    trade_details = []

    for trade in trades:
        
        #Get the user who sent the Trade Request.
        sender = User.query.get_or_404(trade.sender_id)

        #Get the owner of the original Trade Listing.
        receiver = User.query.get_or_404(trade.receiver_id)

        #Get the item offered by the sender.
        offered_item = Item.query.get_or_404(trade.offered_item_id)

        #Get the item requested from the receiver.
        requested_item = Item.query.get_or_404(trade.requested_item_id)

        #Get the original Trade listing requested by the sender.
        listing = Listing.query.get_or_404(trade.listing_id)

        #Group all the information for the HTML page
        trade_details.append({
            "trade": trade,
            "sender": sender,
            "receiver": receiver,
            "offered_item": offered_item,
            "requested_item": requested_item,
            "listing": listing
        })

    return render_template(
        "trade_history.html",
        trade_details=trade_details
    )
    
#======================================================================
# BUYER PURCHASE LISTING (confirm purchase)
#======================================================================
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
            "confirm_purchase.html",
            listing=listing,
            item=item
        )
    
    #POST: create a transaction that is waiting for payment.
    new_transaction = Transaction(
        listing_id=listing.id,
        buyer_id=current_user.id,
        seller_id=listing.user_id,
        item_id=item.id,
        price=listing.price,
        status="awaiting_payment"
    )

    #Listing status will change to pending (when seller view my-listings)
    listing.status = "pending"

    db.session.add(new_transaction)
    db.session.commit()

    #Send the buyer to upload payment proof.
    return redirect(
        url_for(
            "marketplace.upload_payment_proof",
            transaction_id=new_transaction.id
        )
    )

#======================================================================
# BUYER UPLOAD PAYMENT PROOF for a pending transaction
#======================================================================
@marketplace_bp.route(
    "/transactions/<int:transaction_id>/payment-proof",
    methods=["GET", "POST"]
)
@login_required
def upload_payment_proof(transaction_id):

    #Only the buyer of this transaction can upload proof.
    transaction = Transaction.query.filter_by(
        id=transaction_id,
        buyer_id=current_user.id
    ).first_or_404()

    item = Item.query.get_or_404(
        transaction.item_id
    )
    
    #Get the payment QR uploaded by the seller
    payment_qr = PaymentQR.query.filter_by(
        user_id=transaction.seller_id
    ).first_or_404()

    #Buyer may submit the proof that they paid
    if transaction.status not in (
        "awaiting_payment",
        "payment_rejected"
    ):
        return "This payment request cannot accept a new proof."
    
    #Show the payment proof page again with an error.
    def show_proof_error(message):
        return render_template(
            "payment_proof_upload.html",
            transaction=transaction,
            item=item,
            payment_qr=payment_qr,
            error=message
        )

    #GET: show the upload payment proof page.
    if request.method == "GET":
        return render_template(
            "payment_proof_upload.html",
            transaction=transaction,
            item=item,
            payment_qr=payment_qr,
        )
        
    #POST: get the payment proof selected by the buyer.
    proof_file = request.files.get("payment_proof")

    if not proof_file or not proof_file.filename:
        return show_proof_error(
            "Please select a payment proof image."
        )

    #Create a safe and unique filename.
    original_filename = secure_filename(
        proof_file.filename
    )

    proof_filename = (
        f"{uuid4().hex}_{original_filename}"
    )

    #Save the proof image in the Marketplace static folder.
    upload_folder = os.path.join(
        marketplace_bp.root_path,
        "static",
        "uploads",
        "payment_proofs"
    )

    os.makedirs(
        upload_folder,
        exist_ok=True
    )

    proof_file.save(
        os.path.join(
            upload_folder,
            proof_filename
        )
    )

    #Save the proof filename and send it to the seller for review.
    transaction.payment_proof = proof_filename
    
    #Clear the old rejection reason when the buyer submits a new proof.
    transaction.rejection_reason = None
    
    transaction.status = "payment_submitted"

    db.session.commit()
    
    return redirect(
        url_for("marketplace.transaction_history")
    )
    
#======================================================================
# BUYER CANCEL PURCHASE after seller reject
#======================================================================
@marketplace_bp.route(
    "/transactions/<int:transaction_id>/cancel",
    methods=["POST"]
)
@login_required
def cancel_purchase(transaction_id):

    #Only the buyer can cancel a transaction that is awaiting payment.
    transaction = Transaction.query.filter(
        Transaction.id == transaction_id,
        Transaction.buyer_id == current_user.id,
        Transaction.status.in_([
            "awaiting_payment",
            "payment_rejected"
        ])
    ).first_or_404()

    #Make the listing visible in Marketplace again.
    listing = Listing.query.get_or_404(
        transaction.listing_id
    )

    transaction.status = "cancelled"
    listing.status = "available"

    db.session.commit()

    return redirect(
        url_for("marketplace.transaction_history")
    )
    
#======================================================================
# SHOW PAYMENT REQUESTS waiting for seller to review
#======================================================================
@marketplace_bp.route("/payment-requests")
@login_required
def payment_requests():

    Buyer = aliased(User)

    #Get the payment proof submmitted by the buyer
    requests = db.session.query(
        Transaction,
        Item,
        Buyer
    ).join(
        Item,
        Transaction.item_id == Item.id
    ).join(
        Buyer,
        Transaction.buyer_id == Buyer.id
    ).filter(
        Transaction.seller_id == current_user.id,
        Transaction.status == "payment_submitted"
    ).order_by(
        Transaction.created_at.desc()
    ).all()

    return render_template(
        "confirm_payments.html",
        requests=requests
    )

#======================================================================
# SELLER choose to APPROVE PAYMENT
#======================================================================
@marketplace_bp.route(
    "/transactions/<int:transaction_id>/approve",
    methods=["POST"]
)
@login_required
def approve_payment(transaction_id):

    #Only the seller can approve a submitted payment.
    transaction = Transaction.query.filter_by(
        id=transaction_id,
        seller_id=current_user.id,
        status="payment_submitted"
    ).first_or_404()

    #Seller confirmed they received payment
    #Keep the listing reserved until the buyer confirms they receive the item
    transaction.status = "payment_confirmed"

    db.session.commit()

    return redirect(
        url_for("marketplace.payment_requests")
    )

#======================================================================
# BUYER CONFIRM THEY RECEIVED THE ITEM
#======================================================================
@marketplace_bp.route(
    "/transactions/<int:transaction_id>/confirm-item-received",
    methods=["POST"]
)
@login_required
def confirm_item_received(transaction_id):

    #Only the buyer can confirm the item was received after seller comfirmed payment.
    transaction = Transaction.query.filter_by(
        id=transaction_id,
        buyer_id=current_user.id,
        status="payment_confirmed"
    ).first_or_404()

    item = Item.query.get_or_404(
        transaction.item_id
    )

    #Get the seller's item and reduce their quantity by one.
    seller_owned_item = OwnedItem.query.filter_by(
        user_id=transaction.seller_id,
        item_id=item.id
    ).first_or_404()

    if seller_owned_item.quantity <= 0:
        return "The seller no longer has this item available."

    seller_owned_item.quantity -= 1

    if seller_owned_item.quantity == 0:
        db.session.delete(seller_owned_item)

    #Give one copy of the item to the buyer.
    buyer_owned_item = OwnedItem.query.filter_by(
        user_id=transaction.buyer_id,
        item_id=item.id
    ).first()

    if buyer_owned_item:
        buyer_owned_item.quantity += 1
    else:
        buyer_owned_item = OwnedItem(
            user_id=transaction.buyer_id,
            item_id=item.id,
            quantity=1
        )
        db.session.add(buyer_owned_item)

    #Complete the transaction and close the listing.
    transaction.status = "completed"
    listing = Listing.query.get_or_404(
        transaction.listing_id
    )
    listing.status = "sold"

    db.session.commit()

    return redirect(
        url_for("marketplace.transaction_history")
    )

#======================================================================
# SELLER choose to REJECT PAYMENT
#======================================================================
@marketplace_bp.route(
    "/transactions/<int:transaction_id>/reject",
    methods=["POST"]
)
@login_required
def reject_payment(transaction_id):

    #Only the seller can reject a submitted payment.
    transaction = Transaction.query.filter_by(
        id=transaction_id,
        seller_id=current_user.id,
        status="payment_submitted"
    ).first_or_404()

    #Get the seller's reason for rejecting the payment proof.
    rejection_reason = request.form.get(
        "rejection_reason",
        ""
    ).strip()

    if not rejection_reason:
        return "Please enter a reason for rejecting the payment proof."

    #Save the seller's rejection reason.
    transaction.rejection_reason = rejection_reason
    
    #Keep the listing reserved while the buyer uploads a new proof.
    transaction.status = "payment_rejected"

    db.session.commit()

    return redirect(
        url_for("marketplace.payment_requests")
    )
     
#======================================================================
# TRANSACTION HISTORY
#======================================================================
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
        "transaction_history.html",
        transactions=transactions,
        malaysia_offset=timedelta(hours=8)
    )
