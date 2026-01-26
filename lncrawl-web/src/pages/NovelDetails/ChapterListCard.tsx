import { Reader } from '@/store/_reader';
import type { Chapter, Job, ReadHistory } from '@/types';
import { stringifyError } from '@/utils/errors';
import { DownloadOutlined, RightCircleOutlined } from '@ant-design/icons';
import { Button, Collapse, message, theme } from 'antd';
import axios from 'axios';
import { useSelector } from 'react-redux';
import { Link, useNavigate } from 'react-router-dom';
import { ChapterDetailsCard } from './ChapterDetailsCard';

export const ChapterListCard: React.FC<{
  chapters: Chapter[];
  history?: ReadHistory;
}> = ({ chapters, history = {} }) => {
  const navigate = useNavigate();
  const { token } = theme.useToken();
  const [messageApi, contextHolder] = message.useMessage();
  const autoFetch = useSelector(Reader.select.autoFetch);

  const createFetchJob = async (id: string) => {
    try {
      const { data } = await axios.get<Job>(`/api/chapter/${id}/fetch`);
      navigate(`/job/${data.id}`);
    } catch (err) {
      messageApi.error(stringifyError(err));
    }
  };

  return (
    <>
      {contextHolder}
      <Collapse
        ghost
        accordion
        size="small"
        style={{
          marginTop: 10,
          borderRadius: 0,
        }}
        items={chapters.map((chapter) => ({
          key: chapter.id,
          label:
            autoFetch || chapter.is_available ? (
              <Link to={`/read/${chapter.id}`}>{chapter.title}</Link>
            ) : (
              chapter.title
            ),
          children: <ChapterDetailsCard inner chapter={chapter} />,
          styles: {
            body: { padding: 0 },
            header: {
              borderRadius: 0,
              textTransform: 'capitalize',
              opacity: history[chapter.id] ? 0.5 : 1,
              borderTop: `1px solid ${token.colorSplit}`,
            },
          },
          extra: chapter.is_available ? (
            <Button
              size="small"
              shape="round"
              icon={<RightCircleOutlined />}
              onClick={(e) => {
                e.stopPropagation();
                e.preventDefault();
                navigate(`/read/${chapter.id}`);
              }}
              style={{ width: '75px', borderColor: token.colorLink }}
            >
              Read
            </Button>
          ) : (
            <Button
              size="small"
              shape="round"
              style={{ width: '75px' }}
              icon={<DownloadOutlined />}
              onClick={(e) => {
                e.stopPropagation();
                e.preventDefault();
                createFetchJob(chapter.id);
              }}
            >
              Fetch
            </Button>
          ),
        }))}
      />
    </>
  );
};
