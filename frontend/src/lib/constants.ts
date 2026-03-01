/**
 * Core Application Constants
 * This file contains environment variables and endpoint configurations used across the app.
 */

// Application Wide Settings
export const APP_CONFIG = {
  APP_NAME: 'Clinical AI Platform',
  APP_VERSION: '0.1.0',
  DEFAULT_AGENT_ID: 'general',
  SUPPORTED_LOCALES: ['en-US'],
  DEFAULT_LOCALE: 'en-US',
};

// API Endpoints
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/v1';

export const API_ENDPOINTS = {
  CHAT: {
    BASE: `${API_BASE_URL}/chat`,
    SESSIONS: `${API_BASE_URL}/chat/sessions`,
  },
  INDEXING: {
    TRIGGER_WHO: `${API_BASE_URL}/indexing/trigger/who`,
    TRIGGER_CDC: `${API_BASE_URL}/indexing/trigger/cdc`,
    UPLOAD: `${API_BASE_URL}/indexing/upload`,
    STATUS: `${API_BASE_URL}/indexing/status`,
  },
  CATALOG: {
    BASE: `${API_BASE_URL}/catalog`,
  },
  SETTINGS: {
    LLM: `${API_BASE_URL}/settings/llm`,
    EMBEDDING: `${API_BASE_URL}/settings/embedding`,
    CONFIG: `${API_BASE_URL}/settings/config`,
  },
  AUTH: {
    LOGIN: `${API_BASE_URL}/auth/login`,
    SIGNUP: `${API_BASE_URL}/auth/signup`,
  },
  VECTOR_DB: {
    SEARCH: `${API_BASE_URL}/vector_db/search`,
    CLEAR: `${API_BASE_URL}/vector_db/collection`,
  },
  USER_PROFILE: `${API_BASE_URL}/users/me`,
};

// Feature Flags
export const FEATURES = {
  ENABLE_VOICE_INPUT: process.env.NEXT_PUBLIC_ENABLE_VOICE_INPUT === 'true',
  ENABLE_FILE_UPLOAD: process.env.NEXT_PUBLIC_ENABLE_FILE_UPLOAD === 'true',
};
