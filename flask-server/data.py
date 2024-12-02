from server import app, db, Menu, Location

with app.app_context():
    
    menu1 = Menu(menu_name="Italian Delight", description="Pasta and more", price=25.00)
    menu2 = Menu(menu_name="BBQ Feast", description="Grilled meats and sides", price=30.00)
    menu3 = Menu(menu_name="Vegan Paradise", description="Plant-based dishes", price=20.00)

    location1 = Location(venue="Grand Ballroom", address="123 Main St", capacity=200)
    location2 = Location(venue="Garden Terrace", address="456 Oak Ave", capacity=100)
    location3 = Location(venue="Beachside Pavilion", address="789 Pine Rd", capacity=150)

    db.session.add_all([menu1, menu2, menu3, location1, location2, location3])
    db.session.commit()

print("Sample data added successfully")
