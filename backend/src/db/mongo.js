const mongoose = require("mongoose");

async function connectMongo() {
  const mongoUri = process.env.MONGO_URI;

  if (!mongoUri) {
    throw new Error("MONGO_URI is required");
  }

  mongoose.set("strictQuery", true);

  await mongoose.connect(mongoUri);

  console.log("[backend] MongoDB connected");
}

module.exports = {
  connectMongo
};
