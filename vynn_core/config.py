import os

# MongoDB configuration - REPLACE WITH YOUR ACTUAL MONGODB ATLAS URI
# Get the correct URI from: MongoDB Atlas > Your Cluster > Connect > Connect your application
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
