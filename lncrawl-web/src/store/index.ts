import { combineReducers, configureStore } from '@reduxjs/toolkit';
import {
  FLUSH,
  PAUSE,
  PERSIST,
  PURGE,
  REGISTER,
  REHYDRATE,
  persistReducer,
  persistStore,
} from 'redux-persist';
import { AuthSlice, authPersistConfig } from './_auth';
import { ConfigSlice, configPersistConfig } from './_config';
import { ReaderSlice, readerPersistConfig } from './_reader';
import { viewPersistConfig, ViewSlice } from './_view';

const reducer = combineReducers({
  view: persistReducer(viewPersistConfig, ViewSlice.reducer),
  auth: persistReducer(authPersistConfig, AuthSlice.reducer),
  reader: persistReducer(readerPersistConfig, ReaderSlice.reducer),
  config: persistReducer(configPersistConfig, ConfigSlice.reducer),
});

export type RootState = ReturnType<typeof reducer>;

export const store = configureStore({
  reducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
      },
    }),
});

export const persistor = persistStore(store);
