// Registration Categories
export const REGISTRATION_CATEGORIES = {
  MODULAR: 'modular',
  FORMAL: 'formal',
  WORKERS_PAS: 'workers_pas',
};

export const REGISTRATION_CATEGORY_LABELS = {
  [REGISTRATION_CATEGORIES.MODULAR]: 'Modular',
  [REGISTRATION_CATEGORIES.FORMAL]: 'Formal',
  [REGISTRATION_CATEGORIES.WORKERS_PAS]: "Worker's PAS",
};

// Intake Options
export const INTAKE_OPTIONS = {
  MARCH: 'M',
  AUGUST: 'A',
};

export const INTAKE_LABELS = {
  [INTAKE_OPTIONS.MARCH]: 'March',
  [INTAKE_OPTIONS.AUGUST]: 'August',
};

// Gender Options
export const GENDER_OPTIONS = {
  MALE: 'male',
  FEMALE: 'female',
  OTHER: 'other',
};

export const GENDER_LABELS = {
  [GENDER_OPTIONS.MALE]: 'Male',
  [GENDER_OPTIONS.FEMALE]: 'Female',
  [GENDER_OPTIONS.OTHER]: 'Other',
};

// Verification Status
export const VERIFICATION_STATUS = {
  PENDING: 'pending_verification',
  VERIFIED: 'verified',
  DECLINED: 'declined',
};

export const VERIFICATION_STATUS_LABELS = {
  [VERIFICATION_STATUS.PENDING]: 'Pending Verification',
  [VERIFICATION_STATUS.VERIFIED]: 'Verified',
  [VERIFICATION_STATUS.DECLINED]: 'Declined',
};

// Account Status
export const ACCOUNT_STATUS = {
  ACTIVE: 'active',
  INACTIVE: 'inactive',
  SUSPENDED: 'suspended',
  COMPLETED: 'completed',
};

export const ACCOUNT_STATUS_LABELS = {
  [ACCOUNT_STATUS.ACTIVE]: 'Active',
  [ACCOUNT_STATUS.INACTIVE]: 'Inactive',
  [ACCOUNT_STATUS.SUSPENDED]: 'Suspended',
  [ACCOUNT_STATUS.COMPLETED]: 'Completed',
};

// Assessment Center Categories
export const CENTER_CATEGORIES = {
  VTI: 'VTI',
  TTI: 'TTI',
  WORKPLACE: 'workplace',
};

export const CENTER_CATEGORY_LABELS = {
  [CENTER_CATEGORIES.VTI]: 'Vocational Training Institute',
  [CENTER_CATEGORIES.TTI]: 'Technical Training Institute',
  [CENTER_CATEGORIES.WORKPLACE]: 'Workplace',
};

// Paper Types
export const PAPER_TYPES = {
  THEORY: 'theory',
  PRACTICAL: 'practical',
};

export const PAPER_TYPE_LABELS = {
  [PAPER_TYPES.THEORY]: 'Theory',
  [PAPER_TYPES.PRACTICAL]: 'Practical',
};

// Pagination
export const DEFAULT_PAGE_SIZE = 20;
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

// Date Formats
export const DATE_FORMAT = 'yyyy-MM-dd';
export const DISPLAY_DATE_FORMAT = 'MMM dd, yyyy';
export const DISPLAY_DATETIME_FORMAT = 'MMM dd, yyyy HH:mm';

// API Status
export const API_STATUS = {
  IDLE: 'idle',
  LOADING: 'loading',
  SUCCESS: 'success',
  ERROR: 'error',
};
