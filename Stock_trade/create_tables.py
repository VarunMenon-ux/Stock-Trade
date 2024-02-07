from app import app, db
from models import User

admin_username = 'admin'
admin_email = 'admin@example.com'
admin_password = 'password'
admin_name = 'Admin User'

with app.app_context():
    db.create_all()
    
    # Check if admin user already exists
    existing_admin = User.query.filter_by(username=admin_username).first()
    
    if not existing_admin:
        # Create the admin user
        admin = User(username=admin_username, email=admin_email, name=admin_name, is_admin=True)
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()

