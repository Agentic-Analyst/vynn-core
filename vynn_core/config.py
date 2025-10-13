import os

# MongoDB configuration - REPLACE WITH YOUR ACTUAL MONGODB ATLAS URI
# Get the correct URI from: MongoDB Atlas > Your Cluster > Connect > Connect your application
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://zanwenfu_db_user:GsLq3jJZuoal0kbp@stock-dashboard.4nlrof8.mongodb.net/?retryWrites=true&w=majority&appName=stock-dashboard")
MONGO_DB = os.getenv("MONGO_DB", "stock-dashboard")
