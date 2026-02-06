from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, FloatField, SelectField, BooleanField, FileField, DecimalField, HiddenField, IntegerField
from wtforms.validators import InputRequired, EqualTo, NumberRange, Optional

class SignupForm(FlaskForm):
    user_id = StringField("Username:", validators=[InputRequired()])
    password = PasswordField("Password:", validators=[InputRequired()])
    password2 = PasswordField("Confirm Password:", validators=[InputRequired(), EqualTo("password")])
    submit = SubmitField("Sign-up")

class LoginForm(FlaskForm):
    user_id = StringField("Username:", validators=[InputRequired()])
    password = PasswordField("Password:", validators=[InputRequired()])
    submit = SubmitField("Log-in")

class PhotoSearchForm(FlaskForm):
    theme = SelectField(choices=[], validators=[InputRequired()])
    price_min = DecimalField("Min Price", places=2, validators=[Optional()])
    price_max = DecimalField("Max Price", places=2, validators=[Optional()])
    filter_type = SelectField("Filter By", validators=[Optional()], choices=[
        ("both", "License and Print"),
        ("license", "License Only"),
        ("print", "Print Only")])
    submit = SubmitField("Search")

class UploadPhotoForm(FlaskForm):
    title = StringField("Title", validators=[InputRequired()])
    description = StringField("Description", validators=[InputRequired()])
    theme = SelectField("Theme", choices=[], validators=[InputRequired()])
    price_license = FloatField("License Price €", validators=[Optional()])
    price_print = FloatField("Print Price €", validators=[Optional()])
    inventory = IntegerField("Prints Inventory", validators=[InputRequired()])
    file = FileField("Upload Image", validators=[InputRequired()])
    submit = SubmitField("Submit")

class DeletePhotoForm(FlaskForm):
    delete_title = StringField("Photo Title", validators=[InputRequired()])
    delete_submit = SubmitField("Delete")

class UpdatePhotoForm(FlaskForm):
    photo_id = HiddenField()
    title = StringField("Title", validators=[Optional()])
    description = StringField("Description", validators=[Optional()])
    theme = SelectField("Theme", choices=[], validators=[Optional()])
    price_license = DecimalField("License Price €", validators=[Optional(), NumberRange(min=0)])
    price_print = DecimalField("Print Price €", validators=[Optional(), NumberRange(min=0)])
    inventory = IntegerField("Update Inventory", validators=[Optional()])
    update_submit = SubmitField("Update Photo")

class PurchaseForm(FlaskForm):
    buy_license = BooleanField("Buy License")
    buy_print = BooleanField("Buy Physical Print")
    quantity = IntegerField("Quantity", validators=[NumberRange(min=1, message="Quantity must be at least 1")])
    submit = SubmitField("Add to Cart")

class CheckoutForm(FlaskForm):
    name = StringField("Full Name", validators=[InputRequired()])
    shipping = StringField("Shipping Address", validators=[InputRequired()])
    payment = SelectField("Payment Method", validators=[InputRequired()], choices=[("card", "Debit Card"), ("other", "PayPal")])
    submit = SubmitField("Confirm Purchase")

class UpdateCartForm(FlaskForm):
    photo_id = HiddenField()
    action = HiddenField()
    submit = SubmitField("Update")

class LimitedPhotoForm(FlaskForm):
    title = StringField('Title', validators=[InputRequired()])
    description = StringField('Description', validators=[InputRequired()])
    file = FileField('Upload Image', validators=[InputRequired()])
    base_price = DecimalField('Starting Bid Price (€)', validators=[InputRequired()])
    submit = SubmitField('Upload Limited Edition Photo')

class BidForm(FlaskForm):
    bid_amount = DecimalField("Place Your Bid €:", validators=[InputRequired(), NumberRange(min=10.00)])
    submit = SubmitField("Submit Bid")
