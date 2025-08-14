import { Auth } from '@/store/_auth';
import { type User } from '@/types';
import { stringifyError } from '@/utils/errors';
import { CheckCircleOutlined, StopOutlined } from '@ant-design/icons';
import { Button, message } from 'antd';
import axios from 'axios';
import { useSelector } from 'react-redux';

export const UserActionButtons: React.FC<{
  user: User;
  onChange?: () => any;
}> = ({ user, onChange }) => {
  const currentUser = useSelector(Auth.select.user);
  const [messageApi, contextHolder] = message.useMessage();

  const toggleUserActiveStatus = async () => {
    try {
      await axios.put(`/api/user/${user.id}`, {
        is_active: !user.is_active,
      });
      if (onChange) onChange();
    } catch (err) {
      messageApi.open({
        type: 'error',
        content: stringifyError(err, 'Something went wrong!'),
      });
    }
  };

  if (user.id === currentUser?.id) {
    return null;
  }

  return (
    <>
      {contextHolder}
      {user.is_active ? (
        <Button
          size="small"
          title="Disable"
          type="primary"
          danger
          icon={<StopOutlined />}
          onClick={toggleUserActiveStatus}
        >
          Disable
        </Button>
      ) : (
        <Button
          size="small"
          title="Enable"
          type="primary"
          icon={<CheckCircleOutlined />}
          onClick={toggleUserActiveStatus}
        >
          Enable
        </Button>
      )}
    </>
  );
};
