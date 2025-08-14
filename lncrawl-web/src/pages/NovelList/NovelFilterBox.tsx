import { Flex, Input } from 'antd';
import { type NovelListHook } from './hooks';

export const NovelFilterBox: React.FC<{
  initialSearch: NovelListHook['search'];
  updateParams: NovelListHook['updateParams'];
}> = ({ initialSearch, updateParams }) => {
  return (
    <Flex align="center">
      <Input.Search
        defaultValue={initialSearch}
        onSearch={(search) => updateParams({ search, page: 0 })}
        placeholder="Search novels"
        allowClear
        size="large"
      />
    </Flex>
  );
};
