import { ErrorState } from '@/components/Loading/ErrorState';
import { LoadingState } from '@/components/Loading/LoadingState';
import { Auth } from '@/store/_auth';
import type { Library, User } from '@/types';
import { stringifyError } from '@/utils/errors';
import { Space, message } from 'antd';
import axios from 'axios';
import { useEffect, useMemo, useState } from 'react';
import { useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import { UserDetailsCard } from '../JobDetails/UserDetailsCard';
import { LibraryInfoCard } from './LibraryInfoCard';
import { LibraryNovelList } from './LibraryNovelList';

export const LibraryDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const user = useSelector(Auth.select.user);
  const isAdmin = useSelector(Auth.select.isAdmin);
  const [messageApi, contextHolder] = message.useMessage();

  const [loading, setLoading] = useState<boolean>(true);
  const [refresh, setRefresh] = useState<number>(0);
  const [error, setError] = useState<string>();
  const [owner, setOwner] = useState<User>();
  const [library, setLibrary] = useState<Library>();

  const isOwner = useMemo(
    () => Boolean(library && user?.id === library.user_id),
    [user?.id, library]
  );

  useEffect(() => {
    const loadDetails = async () => {
      setLoading(true);
      setError(undefined);
      try {
        const { data } = await axios.get<Library>(`/api/library/${id}`);
        setLibrary(data);
      } catch (err) {
        setError(stringifyError(err));
      } finally {
        setLoading(false);
      }
    };
    if (id) {
      loadDetails();
    }
  }, [id, refresh]);

  useEffect(() => {
    if (!isAdmin || !library?.user_id) {
      return;
    }
    const loadOwner = async () => {
      try {
        const { data } = await axios.get<User>(`/api/user/${library.user_id}`);
        setOwner(data);
      } catch (err) {
        messageApi.error(stringifyError(err));
      }
    };
    loadOwner();
  }, [library?.user_id, isAdmin, messageApi]);

  const handleTogglePublic = async (checked: boolean) => {
    if (!id) return;
    try {
      await axios.patch(`/api/library/${id}`, { is_public: checked });
      setLibrary((library) => library && { ...library, is_public: checked });
      messageApi.success(`Library is now ${checked ? 'public' : 'private'}`);
    } catch (err) {
      messageApi.error(stringifyError(err));
    }
  };

  const handleLibraryUpdated = (updatedLibrary: Library) => {
    setLibrary(updatedLibrary);
  };

  if (loading) {
    return <LoadingState message="Loading library details..." />;
  }

  if (error || !library) {
    return (
      <ErrorState
        error={error}
        title="Failed to load library"
        onRetry={() => setRefresh((v) => v + 1)}
      />
    );
  }

  return (
    <Space vertical style={{ width: '100%' }}>
      {contextHolder}

      <LibraryInfoCard
        library={library}
        isOwner={isOwner}
        loading={loading}
        onTogglePublic={handleTogglePublic}
        onLibraryUpdated={handleLibraryUpdated}
      />

      {isAdmin && owner && <UserDetailsCard user={owner} title="Owner" />}

      <LibraryNovelList library={library} isOwner={isOwner} />
    </Space>
  );
};
