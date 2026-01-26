import { MainLayout } from '@/components/Layout';
import { ReaderLayout } from '@/components/Layout/reader';
import { Navigate, type RouteObject } from 'react-router-dom';

import { AuthLayout } from '@/components/Layout/auth';
import { FeedbackDetailsPage } from './FeedbackDetails';
import { FeedbackListPage } from './FeedbackList';
import { ForgotPasswordPage } from './ForgotPassword';
import { JobDetailsPage } from './JobDetails';
import { LibraryDetailsPage } from './LibraryDetails';
import { LibraryListPage } from './LibraryList';
import { LoginPage } from './Login';
import { MainPage } from './MainPage';
import { NovelDetailsPage } from './NovelDetails';
import { NovelListPage } from './NovelList';
import { NovelReaderPage } from './NovelReader';
import { ResetPasswordPage } from './ResetPassword';
import { SettingsPage } from './SettingsPage';
import { SignupPage } from './Signup';
import { SupportedSourcesPage } from './SupportedSources';
import { TutorialPage } from './Tutorial';
import { UserDetailsPage } from './UserDetails';
import { UserListPage } from './UserList';
import { UserProfilePage } from './UserProfile';

export const AUTH_ROUTES: RouteObject[] = [
  {
    path: '/',
    element: <AuthLayout />,
    children: [
      {
        path: '',
        element: <Navigate to="/login" replace />,
      },
      {
        path: '/login',
        element: <LoginPage />,
      },
      {
        path: '/signup',
        element: <SignupPage />,
      },
      {
        path: '/forgot-password',
        element: <ForgotPasswordPage />,
      },
      {
        path: '/reset-password',
        element: <ResetPasswordPage />,
      },
    ],
  },
];

export const USER_ROUTES: RouteObject[] = [
  {
    path: '/',
    element: <MainLayout />,
    children: [
      {
        path: '',
        element: <MainPage />,
      },
      {
        path: 'profile',
        element: <UserProfilePage />,
      },
      {
        path: 'job/:id',
        element: <JobDetailsPage />,
      },
      {
        path: 'novels',
        element: <NovelListPage />,
      },
      {
        path: 'libraries',
        element: <LibraryListPage />,
      },
      {
        path: 'library/:id',
        element: <LibraryDetailsPage />,
      },
      {
        path: 'novel/:id',
        element: <NovelDetailsPage />,
      },
      {
        path: 'feedbacks',
        element: <FeedbackListPage />,
      },
      {
        path: 'feedback/:id',
        element: <FeedbackDetailsPage />,
      },
      {
        path: 'meta',
        children: [
          {
            path: 'sources',
            element: <SupportedSourcesPage />,
          },
        ],
      },
      {
        path: 'settings',
        element: <SettingsPage />,
      },
      {
        path: 'tutorial',
        element: <TutorialPage />,
      },
    ],
  },
  {
    path: 'read',
    element: <ReaderLayout />,
    children: [
      {
        path: ':id',
        element: <NovelReaderPage />,
      },
    ],
  },
];

export const ADMIN_ROUTES: RouteObject[] = [
  ...USER_ROUTES,
  {
    path: '/admin',
    element: <MainLayout />,
    children: [
      {
        path: 'users',
        element: <UserListPage />,
      },
      {
        path: 'user/:id',
        element: <UserDetailsPage />,
      },
    ],
  },
];
