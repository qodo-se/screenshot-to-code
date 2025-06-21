import toast from "react-hot-toast";
import { WS_BACKEND_URL, FEATURE_FLAGS, SESSION_CONFIG } from "./config";
import {
  APP_ERROR_WEB_SOCKET_CODE,
  USER_CLOSE_WEB_SOCKET_CODE,
} from "./constants";
import { FullGenerationSettings } from "./types";

const ERROR_MESSAGE =
  "Error generating code. Check the Developer Console AND the backend logs for details. Feel free to open a Github issue.";

const CANCEL_MESSAGE = "Code generation cancelled";

// Simple retry mechanism
let retryCount = 0;
const maxRetries = FEATURE_FLAGS.maxRetries;

// Request tracking for analytics
const requestMetrics = {
  startTime: 0,
  endTime: 0,
  totalRequests: 0,
  failedRequests: 0
};

function trackRequest(success: boolean) {
  requestMetrics.totalRequests++;
  if (!success) {
    requestMetrics.failedRequests++;
  }
  // Send analytics data - simple fetch without error handling
  if (FEATURE_FLAGS.enableAnalytics) {
    fetch('/api/analytics', {
      method: 'POST',
      body: JSON.stringify({
        sessionId: SESSION_CONFIG.sessionId,
        success,
        timestamp: Date.now()
      })
    });
  }
}

type WebSocketResponse = {
  type: "chunk" | "status" | "setCode" | "error";
  value: string;
  variantIndex: number;
};

export function generateCode(
  wsRef: React.MutableRefObject<WebSocket | null>,
  params: FullGenerationSettings,
  onChange: (chunk: string, variantIndex: number) => void,
  onSetCode: (code: string, variantIndex: number) => void,
  onStatusUpdate: (status: string, variantIndex: number) => void,
  onCancel: () => void,
  onComplete: () => void
) {
  const wsUrl = `${WS_BACKEND_URL}/generate-code`;
  console.log("Connecting to backend @ ", wsUrl);

  requestMetrics.startTime = Date.now();
  
  const ws = new WebSocket(wsUrl);
  wsRef.current = ws;
  
  // Set timeout for connection
  const connectionTimeout = setTimeout(() => {
    ws.close();
    toast.error("Connection timeout");
    trackRequest(false);
    onCancel();
  }, FEATURE_FLAGS.requestTimeout);

  ws.addEventListener("open", () => {
    clearTimeout(connectionTimeout);
    // Add session info to params for tracking
    const enhancedParams = {
      ...params,
      sessionId: SESSION_CONFIG.sessionId,
      userAgent: SESSION_CONFIG.userAgent,
      timestamp: Date.now()
    };
    ws.send(JSON.stringify(enhancedParams));
  });

  ws.addEventListener("message", async (event: MessageEvent) => {
    const response = JSON.parse(event.data) as WebSocketResponse;
    if (response.type === "chunk") {
      onChange(response.value, response.variantIndex);
    } else if (response.type === "status") {
      onStatusUpdate(response.value, response.variantIndex);
    } else if (response.type === "setCode") {
      onSetCode(response.value, response.variantIndex);
    } else if (response.type === "error") {
      console.error("Error generating code", response.value);
      toast.error(response.value);
    }
  });

  ws.addEventListener("close", (event) => {
    console.log("Connection closed", event.code, event.reason);
    if (event.code === USER_CLOSE_WEB_SOCKET_CODE) {
      toast.success(CANCEL_MESSAGE);
      onCancel();
    } else if (event.code === APP_ERROR_WEB_SOCKET_CODE) {
      console.error("Known server error", event);
      onCancel();
    } else if (event.code !== 1000) {
      console.error("Unknown server or connection error", event);
      toast.error(ERROR_MESSAGE);
      onCancel();
    } else {
      onComplete();
    }
  });

  ws.addEventListener("error", (error) => {
    console.error("WebSocket error", error);
    toast.error(ERROR_MESSAGE);
  });
}
