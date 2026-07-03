import type {
  ApprovalScope,
  Contribution,
  EvidenceManifest,
  JarvisEvent,
  LearningRecord,
  MemoryProposal,
  OutcomeReport,
  ProtocolError as ProtocolErrorRecord,
  ProtocolErrorId,
  Request,
  Review,
  SkillProposal,
  Takeover,
  WorkSession,
} from "./generated/openapi-types.js";

export * from "./generated/openapi-types.js";

export type ProtocolError = ProtocolErrorRecord;

export interface ValidationResult {
  valid: boolean;
  errors: ProtocolError[];
}

export interface ProtocolErrorOptions {
  objectType?: string;
  field?: string;
  reason?: string;
  remediation?: string;
  traceId?: string;
}

export interface HeaderValidationOptions {
  workSessionScoped?: boolean;
  requiredHeaders?: readonly string[];
  now?: Date;
  maxSkewMs?: number;
  maxPastSkewMs?: number;
  maxFutureSkewMs?: number;
}

export interface BaseHeaderOptions {
  actorId: string;
  authorization: string;
  protocolVersion?: string;
  validationOptions?: HeaderValidationOptions;
}

export interface MutationHeaderBaseOptions extends BaseHeaderOptions {
  idempotencyKey: string;
  requestTimestamp: string;
}

export interface NonWorkSessionMutationHeaderOptions extends MutationHeaderBaseOptions {
  workSessionScoped?: false;
}

export interface WorkSessionMutationHeaderOptions extends MutationHeaderBaseOptions {
  workSessionScoped?: true;
  expectedWorkSessionRevision: number;
  previousEventHash: string;
}

export type MutationHeaderOptions =
  | NonWorkSessionMutationHeaderOptions
  | WorkSessionMutationHeaderOptions;

export interface OperationBinding {
  method: string;
  path: string;
  statuses: number[];
}

export interface FixtureOperation {
  operation_id: string;
  method: string;
  path: string;
  headers: Record<string, unknown>;
  actor_id: string;
  expected_status: number;
  expected_error_id?: ProtocolErrorId;
  expected_error_field?: string;
  work_session_id?: string;
  body_ref?: string;
  attempted_takeover_lock_epoch?: number;
}

export interface OperationEnvelopeOptions {
  operationId: string;
  actorId: string;
  authorization?: string;
  protocolVersion?: string;
  headers?: Record<string, unknown>;
  path?: string;
  pathParams?: Record<string, string>;
  workerId?: string;
  targetActorId?: string;
  workSessionId?: string;
  idempotencyKey?: string;
  requestTimestamp?: string;
  expectedWorkSessionRevision?: number;
  previousEventHash?: string;
  expectedStatus?: number;
  expectedErrorId?: ProtocolErrorId;
  expectedErrorField?: string;
  bodyRef?: string;
  attemptedTakeoverLockEpoch?: number;
  validationOptions?: HeaderValidationOptions;
}

export interface JarvisEventOptions {
  id: string;
  sequence: number;
  type: string;
  workSessionId: string;
  actorId: string;
  timestamp: string;
  payload: JarvisEvent["payload"];
  previousHash?: string;
  eventHash?: string;
  canonicalization?: JarvisEvent["canonicalization"];
  traceContext?: JarvisEvent["trace_context"];
  actorSignature?: string;
  signingKeyRef?: string;
}

export interface NextJarvisEventOptions extends Omit<JarvisEventOptions, "sequence"> {
  events?: JarvisEvent[];
  sequence?: number;
}

export interface EvidenceManifestOptions {
  id: string;
  workSession: WorkSession;
  generatedByActorId: string;
  generatedAt: string;
  objective?: string;
  workSessionId?: string;
  events?: JarvisEvent[];
  eventChainRoot?: string;
  evidenceItemRefs?: EvidenceManifest["evidence_item_refs"];
  policyDecisionRefs?: string[];
  requestRefs?: string[];
  reviewRefs?: string[];
  takeoverRefs?: string[];
  contributionRefs?: string[];
  artifactRefs?: string[];
  limitationRefs?: string[];
  redactionRefs?: string[];
  exportProfile?: EvidenceManifest["export_profile"];
}

export interface ConformanceFixture {
  fixture_id: string;
  protocol_version: string;
  kind: "valid" | "invalid";
  title: string;
  description: string;
  records: Record<string, unknown>;
  operations: FixtureOperation[];
  assertions: unknown[];
  expected_result: "accepted" | "rejected";
  expected_error_id?: ProtocolErrorId;
  expected_error_field?: string;
}

export declare class JarvisProtocolValidationError extends Error {
  readonly error: ProtocolError;
  constructor(error: ProtocolError);
}

export declare const PROTOCOL_VERSION: string;
export declare const OPENAPI_SCHEMA_NAMES: string[];
export declare const SCHEMA_REQUIRED_FIELDS: Record<string, string[]>;
export declare const SCHEMA_ENUMS: Record<string, string[]>;
export declare const SCHEMA_FORBIDDEN_FIELDS: Record<string, string[]>;
export declare const SCHEMA_ALLOWED_FIELDS: Record<string, string[]>;
export declare const SCHEMA_CLOSED_SCHEMAS: string[];
export declare const WORKSESSION_MUTATION_HEADERS: readonly string[];
export declare const NON_WORKSESSION_MUTATION_HEADERS: readonly string[];
export declare const READ_HEADERS: readonly string[];
export declare const TERMINAL_WORK_SESSION_STATES: readonly string[];
export declare const REVIEW_RESOLVED_REQUEST_STATUSES: readonly string[];
export declare const FORBIDDEN_EXPORT_KEY_TOKENS: readonly string[];

export declare function protocolError(
  errorId: ProtocolErrorId,
  options?: ProtocolErrorOptions,
): ProtocolError;

export declare function validationResult(errors: ProtocolError[]): ValidationResult;

export declare function createReadHeaders(
  options: BaseHeaderOptions,
): Record<string, unknown>;

export declare function createNonWorkSessionMutationHeaders(
  options: NonWorkSessionMutationHeaderOptions,
): Record<string, unknown>;

export declare function createWorkSessionMutationHeaders(
  options: WorkSessionMutationHeaderOptions,
): Record<string, unknown>;

export declare function createMutationHeaders(
  options: MutationHeaderOptions | NonWorkSessionMutationHeaderOptions,
): Record<string, unknown>;

export declare function getOperationBinding(operationId: string): OperationBinding;
export declare function createOperationPath(
  operationId: string,
  pathParams?: Record<string, string>,
): string;
export declare function createOperationEnvelope(
  options: OperationEnvelopeOptions,
): FixtureOperation;
export declare function createJarvisEvent(options: JarvisEventOptions): JarvisEvent;
export declare function createNextJarvisEvent(options: NextJarvisEventOptions): JarvisEvent;
export declare function createEvidenceManifest(options: EvidenceManifestOptions): EvidenceManifest;

export declare function findForbiddenHostPrivateField(
  value: unknown,
  basePath?: string,
): string | null;

export declare function validateSchemaRecord(
  objectType: string,
  record: unknown,
): ValidationResult;

export declare function validateHeaders(
  headers: unknown,
  options?: HeaderValidationOptions,
): ValidationResult;

export declare function validateMutationHeaders(
  headers: unknown,
  options?: HeaderValidationOptions,
): ValidationResult;

export declare function validateReadHeaders(
  headers: unknown,
  options?: HeaderValidationOptions,
): ValidationResult;

export declare function validateOperationHeaders(
  operation: FixtureOperation,
  options?: HeaderValidationOptions,
): ValidationResult;
export declare function validateRequest(request: Request): ValidationResult;
export declare function validateApprovalScope(
  approvalScope: ApprovalScope,
  options?: { request?: Request; review?: Review },
): ValidationResult;
export declare function validateReview(
  review: Review,
  options?: { request?: Request },
): ValidationResult;
export declare function validateTakeover(takeover: Takeover): ValidationResult;
export declare function validateContribution(contribution: Contribution): ValidationResult;
export declare function validateEvidenceManifest(
  evidenceManifest: EvidenceManifest,
  options?: { workSession?: WorkSession },
): ValidationResult;
export declare function validateLearningRecord(learningRecord: LearningRecord): ValidationResult;
export declare function validateMemoryProposal(memoryProposal: MemoryProposal): ValidationResult;
export declare function validateSkillProposal(skillProposal: SkillProposal): ValidationResult;
export declare function validateOutcomeReport(
  outcomeReport: OutcomeReport,
  options?: { workSession?: WorkSession },
): ValidationResult;
export declare function validateProtocolRecord(
  objectType: string,
  record: unknown,
  options?: Record<string, unknown>,
): ValidationResult;
export declare function canonicalizeProtocolValue(value: unknown): string;
export declare function hashProtocolValue(value: unknown): string;
export declare function validateEventHashChain(
  events: JarvisEvent[],
  options?: { genesisHash?: string },
): ValidationResult;
export declare function validateFixture(fixture: ConformanceFixture): ValidationResult;
