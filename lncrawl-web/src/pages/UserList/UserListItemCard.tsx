import { UserAvatar } from '@/components/Tags/gravatar';
import {
  UserRoleTag,
  UserStatusTag,
  UserTierTag,
} from '@/components/Tags/users';
import { type User } from '@/types';
import { formatDate } from '@/utils/time';
import { CalendarOutlined } from '@ant-design/icons';
import { Card, Col, Flex, Grid, Row, Space, Typography } from 'antd';
import { Link } from 'react-router-dom';
import { UserActionButtons } from './UserActionButtons';

export const UserListItemCard: React.FC<{
  user: User;
  onChange?: () => any;
}> = ({ user, onChange }) => {
  const { lg } = Grid.useBreakpoint();
  return (
    <Link to={`/admin/user/${user.id}`}>
      <Card
        hoverable
        style={{ marginBottom: 5 }}
        styles={{
          body: { padding: lg ? undefined : 15 },
        }}
      >
        <Row align="middle" gutter={[25, 16]}>
          <Col flex="auto" style={{ width: '300px' }}>
            <Space size="middle" style={{ position: 'relative' }}>
              <UserAvatar
                size={48}
                user={user}
                style={{ backgroundColor: '#1890ff' }}
              />
              <Flex vertical>
                <Typography.Text strong>{user.name}</Typography.Text>
                <Typography.Text
                  type={user.name ? 'secondary' : undefined}
                  style={{ whiteSpace: 'pre-wrap' }}
                >
                  {user.email}
                </Typography.Text>
              </Flex>
            </Space>
          </Col>

          <Col flex="auto">
            <Flex wrap gap="10px" justify="space-between">
              <Flex wrap vertical gap="10px">
                <Flex gap="10px">
                  <Typography.Text
                    strong
                    style={{ width: 70, textAlign: 'right' }}
                  >
                    Role:
                  </Typography.Text>
                  <UserRoleTag value={user.role} />
                </Flex>
                <Flex gap="10px">
                  <Typography.Text
                    strong
                    style={{ width: 70, textAlign: 'right' }}
                  >
                    Status:
                  </Typography.Text>
                  <UserStatusTag value={user.is_active} />
                </Flex>
              </Flex>
              <Flex wrap vertical gap="10px">
                <Flex gap="10px">
                  <Typography.Text
                    strong
                    style={{ width: 70, textAlign: 'right' }}
                  >
                    Tier:
                  </Typography.Text>
                  <UserTierTag value={user.tier} />
                </Flex>
                <Flex gap="10px">
                  <Typography.Text
                    strong
                    style={{ width: 70, textAlign: 'right' }}
                  >
                    Joined:
                  </Typography.Text>
                  <Typography.Text>
                    <CalendarOutlined /> {formatDate(user.created_at)}
                  </Typography.Text>
                </Flex>
              </Flex>
            </Flex>
          </Col>

          <Col
            flex="auto"
            style={{ width: '120px' }}
            onClick={(e) => e.preventDefault()}
          >
            <Flex
              wrap
              gap="10px"
              align="center"
              justify="end"
              style={{ minWidth: 100 }}
            >
              <UserActionButtons user={user} onChange={onChange} />
            </Flex>
          </Col>
        </Row>
      </Card>
    </Link>
  );
};
