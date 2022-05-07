import code
from http.client import NETWORK_AUTHENTICATION_REQUIRED
from turtle import title
from unicodedata import name
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
import base64
import boto3
import datetime
import io
from io import BytesIO
from mimetypes import guess_extension, guess_type
import os
from PIL import Image
import random
import re
import string

db = SQLAlchemy()

EXTENSIONS = ["png", "gif", "jpg", "jpeg"]
BASE_DIR = os.getcwd()
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
S3_BASE_URL = f"https://{S3_BUCKET_NAME}.s3.us-east-1.amazonaws.com"

assoc_table = db.Table(
    "association",
    db.Column("post_id", db.Integer, db.ForeignKey("posts.id")),
    db.Column("allergen_id", db.Integer, db.ForeignKey("allergens.id"))
)

class User(db.Model):
    """
    User Model

    One to Many relationship with Posts
    """
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.String, nullable=False)

    posts = db.relationship("Post", back_populates="user", cascade="delete")

    def __init__(self, **kwargs):
        """
        initialize user object
        """
        self.name = kwargs.get("name", "anonymous")

    def serialize(self):
        """
        Serialize user object along with any posts user has made
        """ 
        return {
            "id" : self.id,
            "name" : self.name,
            "posts": [p.serialize_simp() for p in self.posts]
        }
    
    def serialize_simp(self):
        """
        Serialize user w/o posts 
        """
        return {
            "id" : self.id,
            "name" : self.name
        }

class Post(db.Model):
    """
    Post Model

    Many to One relationship with Users
    Many to One relationship with Location
    """
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = db.relationship("User", back_populates="posts")

    allergens = db.relationship("Allergen", secondary=assoc_table, back_populates="posts")

    building = db.Column(db.String, nullable=False)
    # latitude = db.Column(db.Integer, db.ForeignKey("locations.latitude"), nullable = False)
    # longitude = db.Column(db.Integer, db.ForeignKey("locations.longitude"), nullable = False)
    # location_id = db.Column(db.Integer, db.ForeignKey("locations.id"))
    # location = db.relationship("Location", back_populates="posts")

    # img_url = db.Column(db.String, db.ForeignKey("assets.id"), nullable = False)
    room = db.Column(db.String)
    description = db.Column(db.String)
    image_URL = db.Column(db.String)

    def __init__(self, **kwargs):
        """
        initializes a post object
        """
        self.user_id = kwargs.get("user_id")
        self.building = kwargs.get("building", "")
        # self.latitude = kwargs.get("latitude")
        # self.longitude = kwargs.get("longitude")
        self.room = kwargs.get("room", "")
        self.description = kwargs.get("description", "")
        # self.image_URL = kwargs.get("url")
        # self.image_URL = kwargs.get("image_URL", "")
        # self.vegan = kwargs.get("vegan", "")
        # self.vegetarian = kwargs.get("vegetarian", "")
        # self.gluten_free = kwargs.get("gluten_free", "")
        # self.allergens = kwargs.get("allergens", "")

    def serialize(self):
        """
        Serialize Post object
        """
        return {
            "id" :self.id,
            "user_id" : self.user_id,
            "user": self.user.serialize_simp(),
            "building" : self.building,
            "room" : self.room,
            "descrption": self.description,
            "allergens": [a.serialize_simp() for a in self.allergens]
            # "latitude" : self.latitude,
            # "longitude" : self.longitude,
            # "description" : self.description,
            # "image_URL" : self.image_URL,
            # "vegan" : self.vegan,
            # "vegetarian" : self.vegetarian,
            # "gluten_free" : self.gluten_free,
            # "dairy_free" : self.dairy_free,
            # "nut_free" : self.nut_free,
            # "allergens" : self.allergens
        }
    
    def serialize_simp(self):
        """
        Serialize Post object
        """
        return {
            "id" :self.id,
            "user_id" : self.user_id,
            "building" : self.building,
            "room" : self.room,
            "allergens": [a.serialize_simp() for a in self.allergens]
            # "latitude" : self.latitude,
            # "longitude" : self.longitude,
            # "description" : self.description,
            # "image_URL" : self.image_URL,
            # "vegan" : self.vegan,
            # "vegetarian" : self.vegetarian,
            # "gluten_free" : self.gluten_free,
            # "dairy_free" : self.dairy_free,
            # "nut_free" : self.nut_free,
            # "allergens" : self.allergens
        }

class Location(db.Model):
    """
    Location Model

    One to Many relationship with Posts
    """
    __tablename__ = "locations"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.String, nullable = False)
    latitude = db.Column(db.Integer, nullable = False)
    longitude = db.Column(db.Integer, nullable = False)

    # posts = db.relationship("Post", back_populates="location", cascade="delete")

    def __init__(self, **kwargs):
        """
        initialize location object
        """
        self.name = kwargs.get("name", "")
        self.latitude = kwargs.get("latitude")
        self.longitude = kwargs.get("longitude")

    def serialize(self):
        """
        serialize location object
        """
        return {
            "id" : self.id,
            "name" : self.name,
            "latitude" : self.latitude,
            "longitude" : self.longitude
        }

class Asset(db.Model):
    """
    Asset model
    """
    __tablename__ = "assets"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    base_url = db.Column(db.String, nullable=True)
    salt = db.Column(db.String, nullable=False)
    extension = db.Column(db.String, nullable=False)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)

    def __init__(self, **kwargs):
        """
        Initializes an Asset object
        """
        self.create(kwargs.get("image_data"))

    def serialize(self):
        """
        Serializes an Asset object
        """
        return {
            "url" : self.url,
            "created_at" : str(self.created_at)
        }

    def create(self, image_data):
        """
        Given an image in base64 form, does the following:
        1. Rejects the image if it is not a support filetype
        2. Generates a random string for the image filename
        3. Decodes the image and attempts to upload it to AWS
        """
        try:
            ext = guess_extension(guess_type(image_data)[0])[1:]

            # only accept supported file extensions
            if ext not in EXTENSIONS:
                raise Exception(f"Unsupported file type: {ext}")

            # secure way of generating a random string for image filename
            salt = "".join(
                random.SystemRandom().choice(
                    string.ascii_uppercase + string.digits
                ) 
                for _ in range(16)
            )

            # remove header of base64 string
            img_str = re.sub("^data:image/.+;base64,", "", image_data)
            img_data = base64.b64decode(img_str)
            img = Image.open(BytesIO(img_data))

            self.base_url = S3_BASE_URL
            self.salt = salt
            self.extension = ext
            self.width = img.width
            self.height = img.height
            self.created_at = datetime.datetime.now()

            img_filename = f"{self.salt}.{self.extension}"
            self.upload(img, img_filename)

            self.url = f"{self.base_url}/{self.salt}.{self.extension}"

        except Exception as e:
            print(f"Error when creating image: {e}")

    def upload(self, img, img_filename):
        """
        Attempts to upload the image to the specified S3 bucket
        """
        try:
            # save image temporarily on server
            img_temploc = f"{BASE_DIR}/{img_filename}"
            img.save(img_temploc)

            # upload the image to S3
            s3_client = boto3.client("s3")
            s3_client.upload_file(img_temploc, S3_BUCKET_NAME, img_filename)

            # make S3 image url is public
            s3_resource = boto3.resource("s3")
            object_acl = s3_resource.ObjectAcl(S3_BUCKET_NAME, img_filename)
            object_acl.put(ACL="public-read")

            # remove image from server
            os.remove(img_temploc)

        except Exception as e:
            print(f"Error when uploading image: {e}")

class Allergen(db.Model):
    """
    Allergen Model

    Many-to-many with posts
    """
    __tablename__ = "allergens"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    vegan = db.Column(db.Boolean)
    vegetarian = db.Column(db.Boolean)
    gluten_free = db.Column(db.Boolean)
    dairy_free = db.Column(db.Boolean)
    nut_free = db.Column(db.Boolean)
    fish_free = db.Column(db.Boolean)  
    shell_free = db.Column(db.Boolean)
    wheat_free = db.Column(db.Boolean)
    soy_free = db.Column(db.Boolean)
    
    posts = db.relationship("Post", secondary=assoc_table, back_populates="allergens")

    def __init__(self, **kwargs):
        self.vegan = kwargs.get("vegan", False)
        self.vegetarian = kwargs.get("vegetarian", False)
        self.gluten_free = kwargs.get("gluten_free", False)
        self.dairy_free = kwargs.get("dairy_free", False)
        self.nut_free = kwargs.get("nut_free", False)
        self.fish_free = kwargs.get("fish_free", False)
        self.shell_free = kwargs.get("shell_free", False)
        self.wheat_free = kwargs.get("wheat_free", False)
        self.soy_free = kwargs.get("soy_free", False)

    def serialize(self):
        return {
            "id": self.id,
            "vegan": self.vegan, 
            "vegetarian": self.vegetarian, 
            "gluten_free": self.gluten_free, 
            "dairy_free": self.dairy_free, 
            "nut_free": self.nut_free, 
            "fish_free": self.fish_free, 
            "shell_free": self.shell_free, 
            "wheat_free": self.wheat_free,
            "soy_free": self.soy_free
            # "posts": 
        }

    def serialize_simp(self):
        """
        Simple serialize -- doesn't serialize posts
        """
        return {
            # "id": self.id,
            "vegan": self.vegan, 
            "vegetarian": self.vegetarian, 
            "gluten_free": self.gluten_free, 
            "dairy_free": self.dairy_free, 
            "nut_free": self.nut_free, 
            "fish_free": self.fish_free, 
            "shell_free": self.shell_free, 
            "wheat_free": self.wheat_free,
            "soy_free": self.soy_free
        }