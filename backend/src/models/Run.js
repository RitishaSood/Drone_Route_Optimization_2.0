const mongoose = require("mongoose");

const runSchema = new mongoose.Schema(
  {
    runId: {
      type: String,
      required: true,
      unique: true,
      index: true
    },
    clientId: {
      type: String,
      required: true,
      index: true
    },
    status: {
      type: String,
      enum: ["queued", "running", "completed", "failed"],
      default: "queued",
      index: true
    },
    config: {
      type: mongoose.Schema.Types.Mixed,
      default: {}
    },
    paths: {
      runDir: String,
      configDir: String,
      dataDir: String,
      csvDir: String,
      outputsDir: String,
      plotsDir: String,
      logsDir: String,
      scenarioConfigFile: String,
      pipelineLogFile: String
    },
    startedAt: {
      type: Date,
      default: null
    },
    finishedAt: {
      type: Date,
      default: null
    },
    error: {
      type: String,
      default: null
    }
  },
  {
    timestamps: {
      createdAt: "createdAt",
      updatedAt: "updatedAt"
    }
  }
);

module.exports = mongoose.model("Run", runSchema);
