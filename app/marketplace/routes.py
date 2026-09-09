from flask import render_template
from flask_login import login_required

from app.marketplace import marketplace_bp


#Temporary route used to test the Marketplace module.
@marketplace_bp.route("/")
def marketplace_home():
    return "Marketplace module is working!"

#Create Listing page.
#Login is required before the user can access this page.
@marketplace_bp.route("/create")
@login_required #(check whether user login or not; if not,system will ask user to login 1st)
def create_listing(): 
    #Display the Create Marketplace Listing form
    return render_template("marketplace_create.html")