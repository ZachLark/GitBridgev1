from flask import Blueprint, render_template

# Create a Blueprint for the UI
webui_bp = Blueprint('webui', __name__, template_folder='templates')

# Define the route for the home page
@webui_bp.route('/')
def index():
    return render_template('index.html')

