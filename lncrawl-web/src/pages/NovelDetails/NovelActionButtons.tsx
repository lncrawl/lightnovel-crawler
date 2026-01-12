import { AddToLibraryButton } from '@/components/Library/AddToLibraryButton';
import { Auth } from '@/store/_auth';
import type { Job, Novel } from '@/types';
import { stringifyError } from '@/utils/errors';
import { DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import { Button, Flex, message } from 'antd';
import axios from 'axios';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';

export const NovelActionButtons: React.FC<{ novel: Novel }> = ({ novel }) => {
  const navigate = useNavigate();
  const isAdmin = useSelector(Auth.select.isAdmin);
  const [messageApi, contextHolder] = message.useMessage();

  const handleRefresh = async () => {
    try {
      const result = await axios.post<Job>(`/api/job/create/fetch-novel`, {
        url: novel.url,
      });
      navigate(`/job/${result.data.id}`);
    } catch (err) {
      messageApi.error(stringifyError(err));
    }
  };

  const handleDelete = async () => {
    try {
      await axios.delete(`/api/novel/${novel.id}`);
      navigate(`/novels`);
    } catch (err) {
      messageApi.error(stringifyError(err));
    }
  };

  return (
    <Flex wrap align="center" justify="end" gap={10}>
      {contextHolder}
      {isAdmin && (
        <Button danger icon={<DeleteOutlined />} onClick={handleDelete}>
          Delete
        </Button>
      )}
      <div style={{ flex: 1 }} />
      <AddToLibraryButton novelId={novel.id} />
      <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
        Refresh
      </Button>
    </Flex>
  );
};
