const { WebSocketServer } = require("ws");
const runManager = require("./runManager.service");
const csvInputService = require("./csvInput.service");

function attachRunSocketServer(httpServer) {
  const wss = new WebSocketServer({
    server: httpServer,
    path: "/ws/runs"
  });

  wss.on("connection", (socket) => {
    socket.on("message", async (raw) => {
      let message;
      try {
        message = JSON.parse(raw.toString("utf8"));
      } catch {
        sendError(socket, "Invalid JSON message");
        return;
      }

      if (message?.type === "create-run") {
        try {
          const payload = {
            clientId: message.clientId,
            config: message.config
          };
          const result = await runManager.createQueuedRun(payload);
          sendJson(socket, {
            type: "run-created",
            ...result
          });
        } catch (error) {
          sendError(socket, error.message || "Run creation failed");
        }
        return;
      }

      if (message?.type === "stage-csv") {
        try {
          const runId = String(message.runId || "");
          if (!runId) throw new Error("runId is required");
          const payload = message.csvInputs || {};
          const normalized = {};
          for (const key of Object.keys(payload)) {
            const filename = `${key}.csv`;
            normalized[filename] = key === "sensor"
              ? csvInputService.parseSensorCsv(payload[key])
              : csvInputService.sanitizeGenericCsvText(payload[key]);
          }
          const { getRunPaths } = require("../utils/paths");
          const fileService = require("./fileService");
          const paths = getRunPaths(runId);
          await fileService.createRunDirectories(paths);
          await csvInputService.writeInputCsvFiles(paths.inputCsvDir, normalized);
          sendJson(socket, { type: "csv-staged", runId });
        } catch (error) {
          sendError(socket, error.message || "CSV staging failed");
        }
        return;
      }

      sendError(socket, "Unsupported websocket message type");
    });
  });

  return wss;
}

function sendJson(socket, payload) {
  if (socket.readyState === socket.OPEN) {
    socket.send(JSON.stringify(payload));
  }
}

function sendError(socket, message) {
  sendJson(socket, { type: "error", error: message });
}

module.exports = {
  attachRunSocketServer
};
