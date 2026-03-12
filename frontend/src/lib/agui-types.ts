export type AguiEventType =
  | 'RUN_STARTED'
  | 'RUN_FINISHED'
  | 'RUN_ERROR'
  | 'STEP_STARTED'
  | 'STEP_FINISHED'
  | 'TEXT_MESSAGE_START'
  | 'TEXT_MESSAGE_CONTENT'
  | 'TEXT_MESSAGE_END'
  | 'STATE_SNAPSHOT'
  | 'STATE_DELTA'
  | 'CUSTOM';

export interface AguiBaseEvent {
  type: AguiEventType;
  timestamp?: number;
}

export interface RunStartedEvent extends AguiBaseEvent {
  type: 'RUN_STARTED';
  threadId: string;
  runId: string;
}

export interface RunFinishedEvent extends AguiBaseEvent {
  type: 'RUN_FINISHED';
  threadId: string;
  runId: string;
}

export interface RunErrorEvent extends AguiBaseEvent {
  type: 'RUN_ERROR';
  message: string;
  code?: string;
}

export interface StepStartedEvent extends AguiBaseEvent {
  type: 'STEP_STARTED';
  stepName: string;
}

export interface StepFinishedEvent extends AguiBaseEvent {
  type: 'STEP_FINISHED';
  stepName: string;
}

export interface TextMessageStartEvent extends AguiBaseEvent {
  type: 'TEXT_MESSAGE_START';
  messageId: string;
  role: string;
}

export interface TextMessageContentEvent extends AguiBaseEvent {
  type: 'TEXT_MESSAGE_CONTENT';
  messageId: string;
  delta: string;
}

export interface TextMessageEndEvent extends AguiBaseEvent {
  type: 'TEXT_MESSAGE_END';
  messageId: string;
}

export interface CustomEvent extends AguiBaseEvent {
  type: 'CUSTOM';
  name: string;
  value: unknown;
}

export interface StateSnapshotEvent extends AguiBaseEvent {
  type: 'STATE_SNAPSHOT';
  snapshot: unknown;
}

export interface StateDeltaEvent extends AguiBaseEvent {
  type: 'STATE_DELTA';
  delta: unknown[]; // JSON Patch operations (RFC 6902)
}

export type AguiEvent =
  | RunStartedEvent
  | RunFinishedEvent
  | RunErrorEvent
  | StepStartedEvent
  | StepFinishedEvent
  | TextMessageStartEvent
  | TextMessageContentEvent
  | TextMessageEndEvent
  | StateSnapshotEvent
  | StateDeltaEvent
  | CustomEvent;
