import { Auth } from '@/store/_auth';
import type { Library } from '@/types';
import { getGradientForId } from '@/utils/gradients';
import { BookOutlined, UserOutlined } from '@ant-design/icons';
import {
  Card,
  Divider,
  Flex,
  Grid,
  Space,
  Switch,
  Tag,
  Typography,
} from 'antd';
import { useSelector } from 'react-redux';
import { DeleteLibraryButton } from './DeleteLibraryButton';
import { EditLibraryButton } from './EditLibraryButton';

interface LibraryInfoCardProps {
  library: Library;
  isOwner: boolean;
  loading: boolean;
  onTogglePublic: (checked: boolean) => void;
  onLibraryUpdated?: (updatedLibrary: Library) => void;
}

export const LibraryInfoCard: React.FC<LibraryInfoCardProps> = ({
  library,
  isOwner,
  loading,
  onTogglePublic,
  onLibraryUpdated,
}) => {
  const { lg } = Grid.useBreakpoint();
  const isAdmin = useSelector(Auth.select.isAdmin);

  return (
    <Card
      style={{
        position: 'relative',
        overflow: 'hidden',
        background: getGradientForId(library.id),
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        textShadow: '0 2px 4px rgba(0,0,0,0.5)',
      }}
      styles={{
        body: {
          display: 'flex',
          position: 'relative',
          alignItems: 'flex-start',
          gap: lg ? 16 : 8,
          padding: lg ? 16 : 8,
          flexWrap: lg ? 'nowrap' : 'wrap',
          justifyContent: lg ? 'space-between' : 'center',
        },
      }}
    >
      {/* Cover Image */}
      <BookOutlined
        style={{
          fontSize: 48,
          marginTop: 6,
          color: library.is_public ? '#39f' : '#0f0',
        }}
      />

      {/* Content */}
      <Flex vertical justify="center" style={{ width: '100%' }}>
        <Typography.Title
          level={3}
          style={{ margin: 0, textAlign: lg ? 'left' : 'center' }}
        >
          {library.name || 'Library'}
        </Typography.Title>

        {library.extra?.owner_name && (
          <Typography.Text
            type="secondary"
            style={{ marginBottom: lg ? 8 : 0 }}
          >
            <Flex gap={4} align="center" justify={lg ? 'flex-start' : 'center'}>
              <UserOutlined />
              {library.extra.owner_name}
            </Flex>
          </Typography.Text>
        )}

        {library.description ? (
          <>
            {!lg && <Divider size="small" />}
            {library.description.split('\n\n').map((line, index) => (
              <Typography.Text
                key={index}
                style={{
                  margin: '4px 0',
                  display: 'block',
                }}
              >
                {line}
              </Typography.Text>
            ))}
          </>
        ) : null}
      </Flex>

      {!lg && <Divider size="small" />}

      {/* Owner Controls */}
      {(isOwner || isAdmin) && (
        <Flex
          vertical
          gap={7}
          style={{ width: 300 }}
          align={lg ? 'flex-end' : 'center'}
        >
          {isOwner ? (
            <Space>
              <Typography.Text>Public</Typography.Text>
              <Switch
                checked={library.is_public}
                onChange={onTogglePublic}
                disabled={loading}
              />
            </Space>
          ) : (
            <Tag
              style={{
                color: '#000',
                background: library.is_public ? '#0f0' : '#3cf',
              }}
            >
              {library.is_public ? 'Public' : 'Private'}
            </Tag>
          )}

          <Flex gap={4} align="center" wrap justify={lg ? 'end' : 'center'}>
            <EditLibraryButton library={library} onSuccess={onLibraryUpdated} />
            <DeleteLibraryButton library={library} />
          </Flex>
        </Flex>
      )}
    </Card>
  );
};
