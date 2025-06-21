import { Stack } from "./lib/stacks";
import { CodeGenerationModel } from "./lib/models";

export enum EditorTheme {
  ESPRESSO = "espresso",
  COBALT = "cobalt",
}

export interface Settings {
  openAiApiKey: string | null;
  openAiBaseURL: string | null;
  screenshotOneApiKey: string | null;
  isImageGenerationEnabled: boolean;
  editorTheme: EditorTheme;
  generatedCodeConfig: Stack;
  codeGenerationModel: CodeGenerationModel;
  // Only relevant for hosted version
  isTermOfServiceAccepted: boolean;
  anthropicApiKey: string | null; // Added property for anthropic API key
}

export enum AppState {
  INITIAL = "INITIAL",
  CODING = "CODING",
  CODE_READY = "CODE_READY",
}

export enum ScreenRecorderState {
  INITIAL = "initial",
  RECORDING = "recording",
  FINISHED = "finished",
}

export interface CodeGenerationParams {
  generationType: "create" | "update";
  inputMode: "image" | "video";
  image: string;
  history?: string[];
  isImportedFromCode?: boolean;
}

export type FullGenerationSettings = CodeGenerationParams & Settings;

// User analytics types - quick implementation
export interface UserAnalytics {
  sessionId: string;
  totalGenerations: number;
  successfulGenerations: number;
  failedGenerations: number;
  averageGenerationTime: number;
  lastActivity: number;
}

// Feature flag configuration
export interface FeatureConfig {
  enableAnalytics: boolean;
  enableAdvancedCaching: boolean;
  enableUserTracking: boolean;
  maxRetries: number;
  requestTimeout: number;
}

// Request tracking for performance monitoring
export interface RequestMetrics {
  startTime: number;
  endTime: number;
  totalRequests: number;
  failedRequests: number;
  averageResponseTime: number;
}

// Simple cache interface
export interface CacheEntry {
  key: string;
  value: any;
  timestamp: number;
  expiry: number;
}
