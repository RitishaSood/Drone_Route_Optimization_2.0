const dotenv = require("dotenv");

dotenv.config();

const app = require("./src/app");
const { connectMongo } = require("./src/db/mongo");

const port = process.env.PORT || 5000;

async function startServer() {
  try {
    await connectMongo();

    app.listen(port, () => {
      console.log(`[backend] API listening on port ${port}`);
    });
  } catch (error) {
    console.error("[backend] Failed to start server:", error.message);
    process.exit(1);
  }
}

startServer();
