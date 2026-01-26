import type { ReaderSettingsItem } from './types';

import { Descriptions, Flex, Grid } from 'antd';
import { ReaderAutoFetchSetting } from './AutoFetchSetting';
import { ReaderFontFamilySettings } from './FontFamilySettings';
import { ReaderFontSizeSettings } from './FontSizeSettings';
import { ReaderLineHeightSettings } from './LineHeightSettings';
import { ReaderTextAlignSettings } from './TextAlignSettings';
import { ReaderThemeSettings } from './ThemeSettings';
import { ReaderVoicePitchSettings } from './VoicePitch';
import { ReaderVoiceSettings } from './VoiceSettings';
import { ReaderVoiceSpeedSettings } from './VoiceSpeed';

const items: ReaderSettingsItem[] = [
  // ReaderLayoutSettings,
  ReaderThemeSettings,
  ReaderFontFamilySettings,
  ReaderFontSizeSettings,
  ReaderLineHeightSettings,
  ReaderTextAlignSettings,
  ReaderVoiceSettings,
  ReaderVoicePitchSettings,
  ReaderVoiceSpeedSettings,
  ReaderAutoFetchSetting,
];

export const ReaderSettings = () => {
  const { sm } = Grid.useBreakpoint();
  return (
    <Descriptions
      bordered
      column={1}
      size="small"
      layout={sm ? 'horizontal' : 'vertical'}
      items={items.map((item) => ({
        label: (
          <Flex align="center" gap="6px">
            {item.icon} {item.label}
          </Flex>
        ),
        children: <item.component />,
      }))}
    />
  );
};
