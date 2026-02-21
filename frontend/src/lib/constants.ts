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
export const API_ENDPOINTS = {
  // Base endpoints
  BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1',
  
  // Chat endpoints
  CHAT_SESSIONS: '/chats',
  CHAT_MESSAGES: (chatId: string) => `/chats/${chatId}/messages`,
  
  // Agent endpoints
  AGENTS: '/agents',
  AGENT_DETAIL: (agentId: string) => `/agents/${agentId}`,

  // User endpoints
  USER_PROFILE: '/users/me',
};

// Feature Flags
export const FEATURES = {
  ENABLE_VOICE_INPUT: process.env.NEXT_PUBLIC_ENABLE_VOICE_INPUT === 'true',
  ENABLE_FILE_UPLOAD: process.env.NEXT_PUBLIC_ENABLE_FILE_UPLOAD === 'true',
};
