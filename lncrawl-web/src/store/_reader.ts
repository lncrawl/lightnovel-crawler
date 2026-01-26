import { FontFamily, ReaderLayout, ReaderTheme, TextAlign } from '@/types';
import type { PayloadAction } from '@reduxjs/toolkit';
import { createSelector, createSlice } from '@reduxjs/toolkit';
import type { PersistConfig } from 'redux-persist';
import storage from 'redux-persist/lib/storage';
import type { RootState } from '.';

//
// Initial State
//

export interface ReaderState {
  voice: string | undefined;
  voiceSpeed: number;
  voicePitch: number;
  speaking: boolean;
  speakPosition: number;
  fontSize: number;
  lineHeight: number;
  theme: ReaderTheme;
  layout: ReaderLayout;
  fontFamily: FontFamily;
  textAlign: TextAlign;
  autoFetch: boolean;
}

const buildInitialState = (): ReaderState => ({
  layout: ReaderLayout.vertical,
  speaking: false,
  speakPosition: 0,
  voice: undefined,
  voiceSpeed: 1,
  voicePitch: 1,
  fontSize: 16,
  lineHeight: 1.4,
  theme: ReaderTheme.Dark,
  fontFamily: FontFamily.Literata,
  autoFetch: false,
  textAlign: TextAlign.left,
});

//
// Slice
//
export const ReaderSlice = createSlice({
  name: 'reader',
  initialState: buildInitialState(),
  reducers: {
    setLayout(state, action: PayloadAction<ReaderState['layout']>) {
      state.layout = action.payload;
    },
    setVoice(state, action: PayloadAction<ReaderState['voice']>) {
      state.voice = action.payload;
    },
    setTheme(state, action: PayloadAction<ReaderState['theme']>) {
      state.theme = action.payload;
    },
    setLineHeight(state, action: PayloadAction<ReaderState['lineHeight']>) {
      state.lineHeight = action.payload;
    },
    setTextAlign(state, action: PayloadAction<ReaderState['textAlign']>) {
      state.textAlign = action.payload;
    },
    setFontSize(state, action: PayloadAction<ReaderState['fontSize']>) {
      state.fontSize = action.payload;
    },
    setFontFamily(state, action: PayloadAction<ReaderState['fontFamily']>) {
      state.fontFamily = action.payload;
    },
    setSpeaking(state, action: PayloadAction<ReaderState['speaking']>) {
      state.speaking = action.payload;
    },
    setSepakPosition(state, action: PayloadAction<number>) {
      state.speakPosition = action.payload;
    },
    setVoicePitch(state, action: PayloadAction<number>) {
      state.voicePitch = action.payload;
    },
    setVoiceSpeed(state, action: PayloadAction<number>) {
      state.voiceSpeed = action.payload;
    },
    setAutoFetch(state, action: PayloadAction<boolean>) {
      state.autoFetch = action.payload;
    },
  },
});

//
// Actions & Selectors
//
const selectReader = (state: RootState) => state.reader;

export const Reader = {
  action: ReaderSlice.actions,
  select: {
    textAlign: createSelector(selectReader, (reader) => reader.textAlign),
    theme: createSelector(selectReader, (reader) => reader.theme),
    layout: createSelector(selectReader, (reader) => reader.layout),
    fontSize: createSelector(selectReader, (reader) => reader.fontSize),
    fontFamily: createSelector(selectReader, (reader) => reader.fontFamily),
    lineHeight: createSelector(selectReader, (reader) => reader.lineHeight),
    voice: createSelector(selectReader, (reader) => reader.voice),
    voiceSpeed: createSelector(selectReader, (reader) => reader.voiceSpeed),
    voicePitch: createSelector(selectReader, (reader) => reader.voicePitch),
    speaking: createSelector(selectReader, (reader) => reader.speaking),
    autoFetch: createSelector(selectReader, (reader) => reader.autoFetch),
    speakPosition: createSelector(
      selectReader,
      (reader) => reader.speakPosition
    ),
  },
};

//
// Persist Config
//
const blacklist: Array<keyof ReaderState> = [
  // items to exclude from local storage
  'speaking',
  'speakPosition',
];

export const readerPersistConfig: PersistConfig<ReaderState> = {
  key: 'reader',
  version: 1,
  storage,
  blacklist,
};
