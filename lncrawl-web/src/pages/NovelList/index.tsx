import {
  Button,
  Col,
  Divider,
  Empty,
  Flex,
  Pagination,
  Result,
  Row,
  Spin,
  Typography,
} from 'antd';
import { useNovelList } from './hooks';
import { NovelFilterBox } from './NovelFilterBox';
import { NovelListItemCard } from './NovelListItemCard';

export const NovelListPage: React.FC<any> = () => {
  const {
    search: initialSearch,
    currentPage,
    perPage,
    error,
    loading,
    total,
    novels,
    refresh,
    updateParams,
  } = useNovelList();

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
      <Typography.Title level={2}>📚 Available Novels</Typography.Title>

      <Divider size="small" />

      <NovelFilterBox
        initialSearch={initialSearch}
        updateParams={updateParams}
      />

      <Divider size="small" />

      <Row gutter={[16, 16]}>
        {novels.map((novel) => (
          <Col key={novel.id} xs={8} lg={6} xl={4}>
            <NovelListItemCard novel={novel} />
          </Col>
        ))}
      </Row>

      {!novels.length && (
        <Flex align="center" justify="center" style={{ height: '100%' }}>
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No novels" />
        </Flex>
      )}

      {(novels.length > 0 || currentPage > 1) && total / perPage > 1 && (
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
