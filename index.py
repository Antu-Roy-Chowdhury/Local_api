from flask import Flask, request, jsonify
from pymongo import MongoClient
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime
import logging
from http import HTTPStatus

# Initialize Flask app
app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
import os
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client['web_scraper_db']  # Database name
collection = db['scraped_data']  # Collection name
@app.route('/')
def  msg():
    return "hello world"
@app.route('/api/test-mongo', methods=['GET'])
def test_mongo():
    try:
        collection.insert_one({"test": "data"})
        return jsonify({"success": True, "message": "MongoDB connection successful"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Rate limiting
# limiter = Limiter(get_remote_address, app=app, default_limits=["100 per day", "10 per hour"])

@app.route('/api/store-data', methods=['POST'])
# @limiter.limit("5 per minute") # Limit to 5 requests per minute per IP
def store_data():
    try:
        # Get JSON data from the request
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        # Add metadata to the data
        data_entry = {
            "data": data,  # Store the raw JSON payload
            "timestamp": datetime.utcnow(),  # Add timestamp
            "source_ip": request.remote_addr  # Log the client's IP (optional)
        }

        # Insert into MongoDB
        result = collection.insert_one(data_entry)
        logger.info(f"Data stored with ID: {result.inserted_id}")

        # Return success response
        return jsonify({
            "success": True,
            "message": "Data stored successfully",
            "id": str(result.inserted_id)
        }), 201

    except Exception as e:
        logger.error(f"Error storing data: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# Health check endpoint (optional)
@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        client.server_info()  # Check MongoDB connection
        return jsonify({"success": True, "message": "API is healthy"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": "MongoDB connection failed"}), 503
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

def handler(request):
    return app(request.environ, request.start_response)