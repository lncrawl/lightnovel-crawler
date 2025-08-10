import {
  Button,
  Divider,
  Flex,
  Input,
  List,
  Pagination,
  Result,
  Spin,
  Typography,
} from 'antd';
import { useUserList } from './hooks';
import { UserListItemCard } from './UserListItemCard';

export const UserListPage: React.FC<any> = () => {
  const {
    search: initialSearch,
    perPage,
    currentPage,
    error,
    loading,
    total,
    users,
    refresh,
    updateParams,
  } = useUserList();

  if (loading) {
    return (
      <Flex align="center" justify="center" style={{ height: '100%' }}>
        <Spin size="large" style={{ marginTop: 100 }} />
      </Flex>
    );
  }

  if (error) {
    return (
      <Flex align="center" justify="center" style={{ height: '100%' }}>
        <Result
          status="error"
          title="Failed to load novel list"
          subTitle={error}
          extra={[<Button onClick={refresh}>Retry</Button>]}
        />
      </Flex>
    );
  }

  return (
    <>
      <Typography.Title level={2}>👥 Users</Typography.Title>

      <Divider size="small" />

      <Flex align="center">
        <Input.Search
          defaultValue={initialSearch}
          onSearch={(search) => updateParams({ search, page: 0 })}
          placeholder="Find users"
          allowClear
          size="large"
        />
      </Flex>

      <Divider size="small" />

      <List
        itemLayout="horizontal"
        dataSource={users}
        renderItem={(user) => (
          <UserListItemCard user={user} onChange={refresh} />
        )}
      />

      {(users.length > 0 || currentPage > 1) && total / perPage > 1 && (
        <Pagination
          current={currentPage}
          total={total}
          pageSize={perPage}
          showSizeChanger={false}
          onChange={(page) => updateParams({ page })}
          style={{ textAlign: 'center', marginTop: 32 }}
        />
      )}
    </>
  );
};

export default UserListPage;
