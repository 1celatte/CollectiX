from flask import render_template, request, redirect, url_for
from flask_login import login_required, current_user
from app.models import Item, OwnedItem, Listing, Transaction, User, Collection, PaymentQR
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

    #A seller must upload their DuitNow before creating a listing.
    if not payment_qr:
        return redirect(
            url_for(
                "marketplace.payment_qr_settings",
                required="must_upload_qr"
            )
        )
       
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
            "marketplace_create.html",
            owned_items=owned_items,
            collections=collections,
            items_by_collection=items_by_collection,
            error=message
        )
        
    #When the user first time open the create listing page, show the form
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

#======================================================================
#NOW IS FOR BUY
#======================================================================

#======================================================================
# VIEW LISTING: show the details of the marketplace listing
#======================================================================
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
            "marketplace_purchase_confirm.html",
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
        "payment_requests.html",
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
        "marketplace_history.html",
        transactions=transactions,
        malaysia_offset=timedelta(hours=8)
    )