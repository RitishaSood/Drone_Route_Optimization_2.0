const fs = require("fs/promises");
const path = require("path");

const { allowedSensorTypes } = require("../config/allowedValues");

const MAX_CSV_BYTES = 5 * 1024 * 1024;
const SENSOR_HEADER = ["id", "sensor_type", "label", "x", "y", "z", "class"];
const SAFE_TEXT = /^[A-Za-z0-9 _.,;:+()\-\/\[\]{}@#%&'*=?!|]+$/;

function normalizeCsvText(text) {
  if (typeof text !== "string") {
    const error = new Error("CSV content must be text");
    error.statusCode = 400;
    throw error;
  }

  if (Buffer.byteLength(text, "utf8") > MAX_CSV_BYTES) {
    const error = new Error("CSV content exceeds the 5 MB limit");
    error.statusCode = 413;
    throw error;
  }

  if (text.includes("\0")) {
    const error = new Error("CSV content contains invalid null bytes");
    error.statusCode = 400;
    throw error;
  }

  return text.replace(/^\uFEFF/, "").replace(/\r\n/g, "\n").replace(/\r/g, "\n").trim();
}

function splitCsvLine(line) {
  return line.split(",").map((part) => part.trim());
}

function sanitizeTextCell(value) {
  const text = String(value ?? "").trim();
  if (!text) return "";
  if (/^[=+\-@]/.test(text)) {
    return `'${text}`;
  }
  if (!SAFE_TEXT.test(text)) {
    const error = new Error("CSV text contains unsupported characters");
    error.statusCode = 400;
    throw error;
  }
  return text;
}

function sanitizeNumericCell(value, min, max, field) {
  const n = Number.parseInt(String(value ?? "").trim(), 10);
  if (!Number.isInteger(n) || n < min || n > max) {
    const error = new Error(`Invalid ${field}`);
    error.statusCode = 400;
    throw error;
  }
  return String(n);
}

function parseSensorCsv(text) {
  const normalized = normalizeCsvText(text);
  if (!normalized) {
    const error = new Error("Sensor CSV is empty");
    error.statusCode = 400;
    throw error;
  }

  const lines = normalized.split("\n").filter((line) => line.trim().length > 0);
  const header = splitCsvLine(lines[0]).map((part) => part.toLowerCase());
  if (header.length !== SENSOR_HEADER.length || !SENSOR_HEADER.every((h, i) => header[i] === h)) {
    const error = new Error("Sensor CSV must start with id,sensor_type,label,x,y,z,class");
    error.statusCode = 400;
    throw error;
  }

  const rows = lines.slice(1).map((line, index) => {
    const values = splitCsvLine(line);
    if (values.length !== SENSOR_HEADER.length) {
      const error = new Error(`Sensor CSV row ${index + 2} must have 7 columns`);
      error.statusCode = 400;
      throw error;
    }

    const row = {
      id: sanitizeSensorId(values[0], index),
      sensor_type: sanitizeSensorType(values[1], index),
      label: sanitizeTextCell(values[2]),
      x: sanitizeNumericCell(values[3], 0, 99, `sensor x at row ${index + 2}`),
      y: sanitizeNumericCell(values[4], 0, 99, `sensor y at row ${index + 2}`),
      z: sanitizeNumericCell(values[5], 0, 100, `sensor z at row ${index + 2}`),
      class: sanitizeSensorClass(values[6], index)
    };

    return row;
  });

  return toSensorCsv(rows);
}

function toSensorCsv(rows) {
  const output = [SENSOR_HEADER.join(",")];
  for (const row of rows) {
    output.push([
      sanitizeSensorId(row.id, 0),
      sanitizeSensorType(row.sensor_type, 0),
      sanitizeTextCell(row.label),
      sanitizeNumericCell(row.x, 0, 99, "sensor x"),
      sanitizeNumericCell(row.y, 0, 99, "sensor y"),
      sanitizeNumericCell(row.z, 0, 100, "sensor z"),
      sanitizeSensorClass(row.class, 0)
    ].join(","));
  }
  return `${output.join("\n")}\n`;
}

function sanitizeSensorId(value, rowIndex) {
  const text = String(value ?? "").trim();
  if (!/^[A-Za-z0-9_-]{1,64}$/.test(text)) {
    const error = new Error(`Invalid sensor id at row ${rowIndex + 2}`);
    error.statusCode = 400;
    throw error;
  }
  return text;
}

function sanitizeSensorType(value, rowIndex) {
  const text = String(value ?? "").trim().toLowerCase();
  const normalized = text === "infrared" ? "ir" : text;
  if (!allowedSensorTypes.includes(normalized)) {
    const error = new Error(`Invalid sensor type at row ${rowIndex + 2}`);
    error.statusCode = 400;
    throw error;
  }
  return normalized;
}

function sanitizeSensorClass(value, rowIndex) {
  const text = String(value ?? "").trim();
  if (!/^[A-Za-z0-9 _-]{1,64}$/.test(text)) {
    const error = new Error(`Invalid sensor class at row ${rowIndex + 2}`);
    error.statusCode = 400;
    throw error;
  }
  return text;
}

function sanitizeGenericCsvText(text) {
  const normalized = normalizeCsvText(text);
  if (!normalized) {
    const error = new Error("CSV content is empty");
    error.statusCode = 400;
    throw error;
  }

  const lines = normalized.split("\n");
  if (lines.length > 5000) {
    const error = new Error("CSV content has too many rows");
    error.statusCode = 400;
    throw error;
  }

  for (const line of lines) {
    if (line.length > 4096) {
      const error = new Error("CSV row is too long");
      error.statusCode = 400;
      throw error;
    }
  }

  return `${lines.join("\n")}\n`;
}

async function writeInputCsvFiles(dir, inputFiles) {
  await fs.mkdir(dir, { recursive: true });
  const writes = [];

  for (const [filename, content] of Object.entries(inputFiles)) {
    if (!content) continue;

    const normalized = filename === "sensor.csv"
      ? parseSensorCsv(content)
      : sanitizeGenericCsvText(content);

    writes.push(fs.writeFile(path.join(dir, filename), normalized, "utf8"));
  }

  await Promise.all(writes);
}

function isInputModeUsed(config) {
  return config.inputMode && config.inputMode !== "generated";
}

function collectInputCsvPayload(config) {
  const csvInputs = config.csvInputs || {};
  const payload = {};

  if (config.inputMode === "uploaded" || config.inputMode === "pasted" || config.inputMode === "hybrid") {
    for (const key of ["terrain_height", "terrain_type", "sensor", "nfz", "env"]) {
      const value = csvInputs[key];
      if (typeof value === "string" && value.trim()) {
        payload[`${key}.csv`] = value;
      }
    }
  }

  if (config.sensorMode === "manual-table" && Array.isArray(config.manualSensors) && config.manualSensors.length > 0) {
    payload["sensor.csv"] = toSensorCsv(config.manualSensors);
  } else if (typeof csvInputs.sensor === "string" && csvInputs.sensor.trim()) {
    payload["sensor.csv"] = csvInputs.sensor;
  }

  return payload;
}

module.exports = {
  collectInputCsvPayload,
  isInputModeUsed,
  parseSensorCsv,
  sanitizeGenericCsvText,
  writeInputCsvFiles,
  toSensorCsv
};
