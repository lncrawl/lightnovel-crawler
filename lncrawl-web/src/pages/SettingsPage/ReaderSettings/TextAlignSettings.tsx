import { store } from '@/store';
import { Reader } from '@/store/_reader';
import { TextAlign } from '@/types';
import { AlignLeftOutlined } from '@ant-design/icons';
import { Flex, Select, Tag } from 'antd';
import { startCase } from 'lodash';
import { useSelector } from 'react-redux';
import type { ReaderSettingsItem } from './types';

export const ReaderTextAlignSettings: ReaderSettingsItem = {
  label: 'Text Align',
  icon: <AlignLeftOutlined />,
  component: () => {
    const textAlign = useSelector(Reader.select.textAlign);

    const updateTextAlign = (value: TextAlign) => {
      store.dispatch(Reader.action.setTextAlign(value));
    };

    return (
      <Flex align="center">
        <Tag style={{ fontSize: 12, userSelect: 'none' }}>Text Align</Tag>
        <Select
          value={textAlign}
          onChange={updateTextAlign}
          style={{ flex: 1 }}
          options={Object.entries(TextAlign).map(([name, value]) => ({
            label: startCase(name),
            value,
          }))}
        />
      </Flex>
    );
  },
};
