export const UserRole = {
  USER: 'user',
  ADMIN: 'admin',
};
export type UserRole = (typeof UserRole)[keyof typeof UserRole];

export const UserTier = {
  BASIC: 0,
  PREMIUM: 1,
  VIP: 2,
};
export type UserTier = (typeof UserTier)[keyof typeof UserTier];

export const JobPriority = {
  LOW: 0,
  NORMAL: 1,
  HIGH: 2,
};
export type JobPriority = (typeof JobPriority)[keyof typeof JobPriority];

export const JobStatus = {
  PENDING: 0,
  RUNNING: 1,
  SUCCESS: 2,
  FAILED: 3,
  CANCELED: 4,
};
export type JobStatus = (typeof JobStatus)[keyof typeof JobStatus];

export const JobType = {
  NOVEL: 0,
  NOVEL_BATCH: 1,
  FULL_NOVEL: 5,
  FULL_NOVEL_BATCH: 6,
  CHAPTER: 10,
  CHAPTER_BATCH: 11,
  VOLUME: 20,
  VOLUME_BATCH: 21,
  IMAGE: 30,
  IMAGE_BATCH: 31,
  ARTIFACT: 40,
  ARTIFACT_BATCH: 41,
};
export type JobType = (typeof JobType)[keyof typeof JobType];

export const OutputFormat = {
  json: 'json',
  epub: 'epub',
  text: 'txt',
  pdf: 'pdf',
  mobi: 'mobi',
  fb2: 'fb2',
  rtf: 'rtf',
  docx: 'docx',
  azw3: 'azw3',
  lit: 'lit',
  lrf: 'lrf',
  pdb: 'pdb',
  rb: 'rb',
  tcr: 'tcr',
};
export type OutputFormat = (typeof OutputFormat)[keyof typeof OutputFormat];

export const FontFamily = {
  Literata: 'Literata, serif',
  Merriweather: 'Merriweather, serif',
  NotoSerif: 'Noto Serif, serif',
  SourceSerif4: 'Source Serif 4, serif',
  CrimsonText: 'Crimson Text, serif',
  PTSerif: 'PT Serif, serif',
  IBMPlexSerif: 'IBM Plex Serif, serif',
  Taviraj: 'Taviraj, serif',
  Cormorant: 'Cormorant, serif',
  PlayfairDisplay: 'Playfair Display, serif',
  ArbutusSlab: 'Arbutus Slab, serif',
  RobotoSlab: 'Roboto Slab, serif',
};
export type FontFamily = (typeof FontFamily)[keyof typeof FontFamily];

export const ReaderTheme = {
  Dark: { background: '#121212', color: '#E0E0E0' },
  Black: { background: '#000000', color: '#FFFFFF' },
  White: { background: '#FFFFFF', color: '#000000' },
  Paper: { background: '#F5F2E7', color: '#2B2B2B' },
  Sepia: { background: '#FDF6E3', color: '#333333' },
  Coffee: { background: '#EAE7DC', color: '#2C2C2C' },
  Parchment: { background: '#FBEEC1', color: '#3C3C3C' },
};
export type ReaderTheme = (typeof ReaderTheme)[keyof typeof ReaderTheme];

export const NotificationItem = {
  JOB_RUNNING: 10,
  JOB_SUCCESS: 20,
  JOB_FAILURE: 30,
  JOB_CANCELED: 40,
  NOVEL_SUCCESS: 50,
  ARTIFACT_SUCCESS: 60,
};
export type NotificationItem =
  (typeof NotificationItem)[keyof typeof NotificationItem];

export const ReaderLayout = {
  horizontal: 'horizontal',
  vertical: 'vertical',
};
export type ReaderLayout = (typeof ReaderLayout)[keyof typeof ReaderLayout];

export const FeedbackType = {
  GENERAL: 0,
  ISSUE: 1,
  FEATURE: 2,
};
export type FeedbackType = (typeof FeedbackType)[keyof typeof FeedbackType];

export const FeedbackStatus = {
  PENDING: 0,
  ACCEPTED: 1,
  RESOLVED: 2,
};
export type FeedbackStatus =
  (typeof FeedbackStatus)[keyof typeof FeedbackStatus];

export const TextAlign = {
  left: 'left',
  center: 'center',
  right: 'right',
  justify: 'justify',
};
export type TextAlign = (typeof TextAlign)[keyof typeof TextAlign];
