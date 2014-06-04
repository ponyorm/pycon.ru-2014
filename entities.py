from datetime import datetime
from pony.orm import *

db = Database("sqlite", "data.sqlite", create_db=True)

class User(db.Entity):
    username = Required(unicode, unique=True)
    password = Required(unicode)
    dt = Required(datetime, default=datetime.now)
    following = Set("Following", reverse="follower")
    followers = Set("Following", reverse="followee")
    photos = Set("Photo")
    likes = Set("Like")
    comments = Set("Comment", reverse="user")
    mentioned = Set("Comment", reverse="mentioned")

class Photo(db.Entity):
    filename = Required(unicode)
    photo_url = Required(unicode)
    dt = Required(datetime, default=datetime.now)
    tags = Set("Tag")
    user = Required(User)
    liked = Set("Like")
    comments = Set("Comment")

class Tag(db.Entity):
    name = PrimaryKey(unicode)
    photos = Set(Photo)

class Comment(db.Entity):
    photo = Required(Photo)
    user = Required(User, reverse="comments")
    dt = Required(datetime, default=datetime.now)
    text = Required(unicode)
    mentioned = Set(User, reverse="mentioned")

class Like(db.Entity):
    user = Required(User)
    photo = Required(Photo)
    dt = Required(datetime, default=datetime.now)
    PrimaryKey(user, photo)

class Following(db.Entity):
    follower = Required(User, reverse="following")
    followee = Required(User, reverse="followers")
    dt = Required(datetime, default=datetime.now)
    PrimaryKey(follower, followee)

sql_debug(True)
db.generate_mapping(create_tables=True)