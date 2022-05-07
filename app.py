import json
from flask import Flask, request
from db import db, User, Post, Location, Asset, Allergen
import datetime

# DB = db.DatabaseDriver()

app = Flask(__name__)
db_filename = "free.db"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % db_filename
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True

db.init_app(app)
with app.app_context():
    db.drop_all() 
    db.create_all()


# generalized response formats
def resp_succ(body, code=200):
    """
    Returns a JSON representation of `body`, with a default success `code` of 200.
    """
    return json.dumps(body), code


def resp_err(message, code=404):
    """
    Returns a JSON representation of an error with `message`, with a default error `code` of 404.
    """
    return json.dumps({"error": message}), code

#actual routes
@app.route("/api/posts/")
def get_posts():
    """
    Get all posts
    """
    posts = []
    for post in Post.query.all():
         posts.append(post.serialize())
    return resp_succ({"posts": posts})


@app.route("/api/posts/<int:post_id>/")
def get_post(post_id):
    """
    Get the post with an id of `post_id`
    """
    post = Post.query.filter_by(id=post_id).first()
    if post is None:
        return resp_err("Invalid ID", 404)
    return resp_succ(post.serialize()) 


@app.route("/api/users/<int:user_id>/")
def get_user(user_id):
    """
    Get a user with an ID of `user_id`
    """
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return resp_err("User not found", 404)

    return resp_succ(user.serialize()) 


@app.route("/api/users/")
def get_users():
    """
    Get all users
    """
    users = []
    for user in User.query.all():
         users.append(user.serialize())
    return resp_succ({"posts": users})


@app.route("/api/posts/", methods=["POST"])
def make_post():
    """
    Make a post with specifications in the request body.
    """
    body = json.loads(request.data)

    user_id = body.get("user_id")
    building = body.get("building")
    room = body.get("room")
    description = body.get("description")
    # image_URL = body.get("image_URL")
    vegan = body.get("vegan")
    vegetarian = body.get("vegetarian")
    gluten_free = body.get("gluten_free")
    dairy_free = body.get("dairy_free")
    nut_free = body.get("nut_free")
    fish_free = body.get("fish_free")
    shell_free = body.get("shell_free")
    wheat_free = body.get("wheat_free")
    soy_free = body.get("soy_free")

    if None in [user_id, building, room, description, vegan, 
    vegetarian, gluten_free, dairy_free, nut_free, fish_free, 
    shell_free, wheat_free, soy_free]:
        return resp_err("Bad request", 400)

    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return resp_err("User does not exist", 404)
    
    new_post = Post(user_id=user_id, building=building, room=room, description=description) 
    db.session.add(new_post)

    allergens_dict = {
        "vegan": vegan, 
        "vegetarian": vegetarian, 
        "gluten_free": gluten_free, 
        "dairy_free": dairy_free, 
        "nut_free": nut_free, 
        "fish_free": fish_free, 
        "shell_free": shell_free, 
        "wheat_free": wheat_free,
        "soy_free": soy_free
    }
    new_allergens = Allergen(**allergens_dict)
    db.session.add(new_allergens)
    new_post.allergens.append(new_allergens) 
    
    user.posts.append(new_post)

    db.session.commit()

    return resp_succ(new_post.serialize(), 201)

@app.route("/api/posts/filter/")
def filter_posts():
    """
    Endpoint for filtering posts based on query parameters.

    Returns a JSON of all locations that pass the specified filter.

    Query parameter is specified by the 'filter' key and a comma 
    separated string of values. 
    For example, .../filter?filter='dairy_free'
    """
    args = request.args.to_dict()["filter"].split(",")

    temp = {}
    valid_args = [
        "vegan",
        "vegetarian",
        "gluten_free",
        "dairy_free",
        "nut_free",
        "fish_free",
        "shell_free", 
        "wheat_free",
        "soy_free",
    ]

    for arg in args:
        arg = arg.strip()
        if arg in valid_args and arg is not "location":
            temp[arg] = True
    
    allergens = Allergen.query.filter_by(**temp)

    posts = []
    for allergen in allergens:
        posts.append([p.serialize_simp() for p in allergen.posts])

    return resp_succ({"posts": posts})


@app.route("/api/users/", methods=["POST"])
def make_user():
    """
    Make a new user with a name specified in the request body
    """
    body = json.loads(request.data)

    name = body.get("name") 

    if name is None:
        return resp_err("Bad request", 400)

    new_user = User(name=name)
    db.session.add(new_user)
    db.session.commit()

    return resp_succ(new_user.serialize(), 201)

@app.route("/api/posts/<int:post_id>/", methods=["POST"])
def update_post(post_id):
    """
    Update a specific posts allergens.
    """
    body = json.loads(request.data)

    user_id = body.get("user_id")
    building = body.get("building")
    room = body.get("room")
    description = body.get("description")
    # image_URL = body.get("image_URL")
    vegan = body.get("vegan")
    vegetarian = body.get("vegetarian")
    gluten_free = body.get("gluten_free")
    dairy_free = body.get("dairy_free")
    nut_free = body.get("nut_free")
    fish_free = body.get("fish_free")
    shell_free = body.get("shell_free")
    wheat_free = body.get("wheat_free")
    soy_free = body.get("soy_free")

    if None in [user_id, building, room, description, vegan, 
    vegetarian, gluten_free, dairy_free, nut_free, fish_free, 
    shell_free, wheat_free, soy_free]:
        return resp_err("Bad request", 400)

    post = Post.query.filter_by(id=post_id).first()
    if post is None:
        return resp_err("Invalid Post ID", 404)
    post.building = building 
    post.room = description
    post.description = description

    db.session.delete(post.allergens[0]) #delete old allergens
    
    #construct new Allergen(), commit it, and append it to post 
    allergens_dict = {
        "vegan": vegan, 
        "vegetarian": vegetarian, 
        "gluten_free": gluten_free, 
        "dairy_free": dairy_free, 
        "nut_free": nut_free, 
        "fish_free": fish_free, 
        "shell_free": shell_free, 
        "wheat_free": wheat_free,
        "soy_free": soy_free
    }
    new_allergens = Allergen(**allergens_dict)
    db.session.add(new_allergens)
    post.allergens.append(new_allergens)
    
    db.session.commit() 

    return resp_succ(post.serialize(), 200)

@app.route("/api/users/<int:user_id>/", methods=["POST"])
def update_user(user_id):
    """
    Updates the fields for the user with an id if `user_id`
    """
    body = json.loads(request.data)
    
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return resp_err("User not found", 404)

    name = body.get("name")
    if name is None:
        return resp_err("Bad request", 400)

    user.name = name 

    db.session.commit()
    return resp_succ(user.serialize()) 
     
@app.route("/api/posts/<int:post_id>/", methods=["DELETE"])
def del_post(post_id):
    """
    Delete the post whose ID is `post_id`
    """
    post = Post.query.filter_by(id=post_id).first()
    if post is None:
        return resp_err("Post not found", 404)

    temp = post.serialize()
    db.session.delete(post)
    db.session.commit()
    return resp_succ(temp)  

@app.route("/api/closed/", methods=["DELETE"])
def close_location():
    """
    Endpoint for whenever a building closes. All food at the specified location is deleted. 

    NOTE: LOCATIONS NOT TESTED/IMPLEMENTED
    """
    body = json.loads(request.data)

    location_name = body.get("location")
    if location_name is None:
        return resp_err("Bad request", 400)

    location = Location.query.filter_by(name=location_name)
    temp = location.posts.serialize()
    db.session.delete(location.posts)
    db.session.commit()
    return resp_succ(temp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

###################################################################################
# OLD FUNCTIONS
###################################################################################

# @app.route("/api/posts/filter/")
def filter_posts_old():
    body = json.loads(request.data)

    # filters_body = body.get("allergens")

    vegan = body.get("vegan")
    vegetarian = body.get("vegetarian")
    gluten_free = body.get("gluten_free")
    dairy_free = body.get("dairy_free")
    nut_free = body.get("nut_free")
    fish_free = body.get("fish_free")
    shell_free = body.get("shell_free")
    wheat_free = body.get("wheat_free")
    soy_free = body.get("soy_free")

    if None in [vegan, vegetarian, gluten_free, dairy_free, nut_free, 
    fish_free, shell_free, wheat_free, soy_free]:
        return resp_err("Bad request")
    
    all_fields = {
        "vegan": vegan, 
        "vegetarian": vegetarian, 
        "gluten_free": gluten_free, 
        "dairy_free": dairy_free, 
        "nut_free": nut_free, 
        "fish_free": fish_free, 
        "shell_free": shell_free, 
        "wheat_free": wheat_free,
        "soy_free": soy_free
    }
    filter = all_fields.copy()
    for allergen, val in all_fields.items(): #remove allergen if user doesn't care for it
        if val == "n/a":
            del filter[allergen]
    # print(filter)
    #TODO: dict first // key = body.get("soy_free") // check if key is None, act resp // shove the whole dict into each constructor

    allergens = Allergen.query.filter_by(**filter)
    
    #TODO: filter by location as well  -- posts += filter_by_loc
    #prevent overlap for multiple filters? e.g.: a post that is both vegan and vegetarian?

    posts = []
    for allergen in allergens:
        posts.append([p.serialize_simp() for p in allergen.posts])
    return resp_succ({"posts": posts})