const crypto = require("crypto");

function createRunId() {
  return `run_${Date.now()}_${crypto.randomUUID().slice(0, 8)}`;
}

module.exports = {
  createRunId
};
