const vscode = require("vscode");
const https = require("https");
const path = require("path");

const BACKEND_URL = "http://localhost:8000";

function httpsGet(url) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port || 80,
      path: urlObj.pathname + urlObj.search,
      method: "GET",
      timeout: 30000,
    };

    const protocol = url.startsWith("https") ? require("https") : require("http");

    const req = protocol.request(options, (res) => {
      let data = "";
      res.on("data", (chunk) => {
        data += chunk;
      });
      res.on("end", () => {
        try {
          const json = JSON.parse(data);
          resolve(json);
        } catch (e) {
          resolve(data);
        }
      });
    });

    req.on("error", (err) => {
      reject(new Error(`Backend error: ${err.message}`));
    });

    req.on("timeout", () => {
      req.destroy();
      reject(new Error("Backend request timeout"));
    });

    req.end();
  });
}

function httpsDelete(url) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port || 80,
      path: urlObj.pathname + urlObj.search,
      method: "DELETE",
      timeout: 30000,
    };

    const protocol = url.startsWith("https") ? require("https") : require("http");

    const req = protocol.request(options, (res) => {
      let data = "";
      res.on("data", (chunk) => {
        data += chunk;
      });
      res.on("end", () => {
        try {
          const json = JSON.parse(data);
          resolve(json);
        } catch (e) {
          resolve(data);
        }
      });
    });

    req.on("error", (err) => {
      reject(new Error(`Backend error: ${err.message}`));
    });

    req.on("timeout", () => {
      req.destroy();
      reject(new Error("Backend request timeout"));
    });

    req.end();
  });
}

let panel = null;

async function openPanel(context) {
  const column = vscode.ViewColumn.Beside;

  if (panel) {
    panel.reveal(column);
    return;
  }

  panel = vscode.window.createWebviewPanel(
    "contextEngine",
    "Context Engine",
    column,
    {
      enableScripts: true,
      localResourceRoots: [
        vscode.Uri.joinPath(context.extensionUri, "media"),
      ],
    }
  );

  const mediaPath = vscode.Uri.joinPath(context.extensionUri, "media");
  const panelHtmlPath = vscode.Uri.joinPath(mediaPath, "panel.html");

  let html = "";
  try {
    const fileData = require("fs").readFileSync(panelHtmlPath.fsPath, "utf-8");
    html = fileData;
  } catch (err) {
    html = `<h1>Error loading panel</h1><p>${err.message}</p>`;
  }

  panel.webview.html = html;

  panel.onDidReceiveMessage(async (message) => {
    const { type, text } = message;

    try {
      let result;

      if (type === "ask") {
        const encodedTask = encodeURIComponent(text);
        result = await httpsGet(`${BACKEND_URL}/ask?task=${encodedTask}`);
      } else if (type === "search") {
        const encodedQuery = encodeURIComponent(text);
        result = await httpsGet(`${BACKEND_URL}/search?query=${encodedQuery}&top_k=5`);
      } else if (type === "health") {
        result = await httpsGet(`${BACKEND_URL}/health/full`);
      } else if (type === "index") {
        result = await httpsGet(`${BACKEND_URL}/index?directory=test-codebase`);
      } else if (type === "deps") {
        const encodedFile = encodeURIComponent(text);
        result = await httpsGet(`${BACKEND_URL}/graph/dependencies?file=${encodedFile}`);
      } else if (type === "report") {
        const encodedTask = encodeURIComponent(text);
        result = await httpsGet(`${BACKEND_URL}/report?task=${encodedTask}`);
      } else if (type === "cacheClear") {
        result = await httpsDelete(`${BACKEND_URL}/cache`);
      } else if (type === "cacheStats") {
        result = await httpsGet(`${BACKEND_URL}/cache/stats`);
      }

      panel.webview.postMessage({
        type: type,
        data: result,
        error: null,
      });
    } catch (err) {
      panel.webview.postMessage({
        type: type,
        data: null,
        error: err.message,
      });
    }
  });

  panel.onDidDispose(() => {
    panel = null;
  });
}

function activate(context) {
  const disposable = vscode.commands.registerCommand(
    "contextEngine.openPanel",
    () => openPanel(context)
  );
  context.subscriptions.push(disposable);
}

function deactivate() {}

module.exports = { activate, deactivate };

