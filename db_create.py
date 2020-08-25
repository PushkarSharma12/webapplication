from app import app 
# And this one with the name of your database file and object
from app import db 

db.create_all()
db.session.commit()
print("Database Created!")