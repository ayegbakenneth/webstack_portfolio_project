from flask import Flask, jsonify, render_template, request, url_for
import os
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from extensions import db
from models import Product

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

db.init_app(app)
with app.app_context():
    db.create_all()

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({"error": "Unauthorized"}), 401

@app.route('/', methods=['GET'], strict_slashes=False)
def index():
    return render_template('index.html')

@app.route('/get_products', methods=['GET'], strict_slashes=False)
def get_products():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 3, type=int)
    
    products = Product.query.paginate(page=page, per_page=per_page)

    product_list = []
    for product in products.items:
        product_dict = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'image_url': product.image_url,
            'price': product.price
        }
        product_list.append(product_dict)

    next_page = url_for('get_products', page=products.next_num) if products.has_next else None
    prev_page = url_for('get_products', page=products.prev_num) if products.has_prev else None

    return render_template('views.html', products=product_list, next_page=next_page, prev_page=prev_page)

@app.route('/add_product', methods=['POST'])
def add_product():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input"}), 400

    try:
        new_product = Product(
            name=data['name'],
            description=data['description'],
            price=data['price'],
            image_url=data['image_url']
        )
        db.session.add(new_product)
        db.session.commit()
        return jsonify({"message": "Product added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/update_product/<int:id>', methods=['PUT'])
def update_product(id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input"}), 400

    product = Product.query.get(id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    try:
        product.name = data.get('name', product.name)
        product.description = data.get('description', product.description)
        product.price = data.get('price', product.price)
        product.image_url = data.get('image_url', product.image_url)
        db.session.commit()
        return jsonify({"message": "Product updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/delete_product/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get(id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    try:
        db.session.delete(product)
        db.session.commit()
        return jsonify({"message": "Product deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.errorhandler(403)
def forbidden(error):
    return jsonify({"error": "Forbidden"}), 403

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not Found"}), 404

if __name__ == "__main__":
    initialize_database()
    app.run()
