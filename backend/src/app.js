const expressMongoSanitize = require("express-mongo-sanitize");
const cors = require("cors");
const express = require("express");
const helmet = require("helmet");
const hpp = require("hpp");
const morgan = require("morgan");

const runRoutes = require("./routes/run.routes");

const app = express();

app.disable("x-powered-by");

if (String(process.env.TRUST_PROXY).toLowerCase() === "true") {
  app.set("trust proxy", 1);
}

const allowedOrigins = String(process.env.CORS_ORIGIN || "http://localhost:5173,https://localhost:5173")
  .split(",")
  .map((origin) => origin.trim())
  .filter(Boolean);

const corsOptions = {
  origin(origin, callback) {
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
      return;
    }

    const error = new Error("CORS origin not allowed");
    error.statusCode = 403;
    callback(error);
  },
  credentials: false
};

function isUnsafeMethod(method) {
  return ["POST", "PUT", "PATCH", "DELETE"].includes(String(method || "").toUpperCase());
}

function normalizeBrowserOrigin(value) {
  if (typeof value !== "string" || !value.trim()) {
    return "";
  }

  try {
    return new URL(value).origin;
  } catch {
    return value.trim();
  }
}

function isAllowedBrowserOrigin(value) {
  const normalized = normalizeBrowserOrigin(value);
  return Boolean(normalized) && allowedOrigins.includes(normalized);
}

app.use(
  helmet.contentSecurityPolicy({
    useDefaults: false,
    directives: {
      defaultSrc: ["'none'"],
      baseUri: ["'none'"],
      frameAncestors: ["'none'"],
      formAction: ["'none'"]
    }
  })
);
app.use(helmet.frameguard({ action: "deny" }));
app.use(helmet.noSniff());
app.use(helmet.referrerPolicy({ policy: "no-referrer" }));
app.use(
  helmet.hsts({
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true,
  })
);
app.use(helmet.hidePoweredBy());
app.use((req, res, next) => {
  if (String(process.env.REQUIRE_HTTPS).toLowerCase() === "true" && !req.secure) {
    res.status(400).json({ error: "HTTPS is required" });
    return;
  }
  next();
});
app.use((req, res, next) => {
  res.setHeader(
    "Permissions-Policy",
    "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
  );
  next();
});
app.use(cors(corsOptions));
app.use(express.json({ limit: "100kb" }));
app.use(express.urlencoded({ extended: false, limit: "100kb" }));
app.use(expressMongoSanitize());
app.use(hpp());
app.use((req, res, next) => {
  if (!isUnsafeMethod(req.method)) {
    next();
    return;
  }

  const origin = String(req.headers.origin || req.headers.referer || "");
  const requestedWith = String(req.headers["x-requested-with"] || "").toLowerCase();
  if (isAllowedBrowserOrigin(origin) || requestedWith === "xmlhttprequest") {
    next();
    return;
  }

  res.status(403).json({
    error: "Cross-site requests are not allowed",
  });
});
app.use(morgan("dev"));

app.get("/health", (_req, res) => {
  res.json({ ok: true });
});

app.use("/api/runs", runRoutes);

app.use((req, res) => {
  res.status(404).json({
    error: "Not found",
    path: req.originalUrl
  });
});

app.use((error, _req, res, _next) => {
  const status =
    error.statusCode ||
    error.status ||
    (error.type === "entity.too.large" ? 413 : 500);
  const payload = {
    error: error.message || "Internal server error"
  };

  if (error.details && Array.isArray(error.details)) {
    payload.details = error.details;
  }

  res.status(status).json(payload);
});

module.exports = app;
