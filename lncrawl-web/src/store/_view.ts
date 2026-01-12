import type { PayloadAction } from '@reduxjs/toolkit';
import { createSelector, createSlice } from '@reduxjs/toolkit';
import type { PersistConfig } from 'redux-persist';
import storage from 'redux-persist/lib/storage';
import type { RootState } from '.';

//
// Initial State
//

export interface ViewState {
  sidebarCollapsed: boolean;
}

const buildInitialState = (): ViewState => ({
  sidebarCollapsed: false,
});

//
// Slice
//
export const ViewSlice = createSlice({
  name: 'auth',
  initialState: buildInitialState(),
  reducers: {
    setSidebarCollapsed(state, action: PayloadAction<boolean>) {
      state.sidebarCollapsed = action.payload;
    },
  },
});

//
// Actions & Selectors
//
const selectViewState = (state: RootState) => state.view;
const sidebarCollapsed = createSelector(
  selectViewState,
  (state) => state.sidebarCollapsed
);

export const View = {
  action: ViewSlice.actions,
  select: {
    sidebarCollapsed,
  },
};

//
// Persist Config
//
const blacklist: Array<keyof ViewState> = [
  // items to exclude from local storage
  'sidebarCollapsed',
];

export const viewPersistConfig: PersistConfig<ViewState> = {
  key: 'view',
  version: 1,
  storage,
  blacklist,
};
