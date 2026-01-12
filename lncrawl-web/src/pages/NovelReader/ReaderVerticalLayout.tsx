import cx from 'classnames';
import styles from './ReaderVerticalLayout.module.scss';

import { store } from '@/store';
import { Reader } from '@/store/_reader';
import type { Job, ReadChapter } from '@/types';
import { Button, Divider, Empty, Flex, Grid, Typography } from 'antd';
import { useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import { JobDetailsCard } from '../JobDetails/JobDetailsCard';
import { ReaderVerticalContent } from './ReaderVerticalContent';
import { ReaderNavBar } from './ReaderNavBar';

export const ReaderVerticalLayout: React.FC<{
  data: ReadChapter;
  job?: Job;
}> = ({ data, job }) => {
  const { md } = Grid.useBreakpoint();
  const theme = useSelector(Reader.select.theme);
  const fontSize = useSelector(Reader.select.fontSize);
  const lineHeight = useSelector(Reader.select.lineHeight);
  const fontFamily = useSelector(Reader.select.fontFamily);
  const autoFetch = useSelector(Reader.select.autoFetch);

  return (
    <Flex
      vertical
      style={{ fontSize, lineHeight, fontFamily, ...theme }}
      className={cx('novel-reader', styles.layout, { [styles.mobile]: !md })}
    >
      <div style={{ textAlign: 'center' }}>
        <Typography.Title level={4} style={{ margin: 0, color: '#F16C6F' }}>
          {data.novel.authors}
        </Typography.Title>
        <Typography.Title level={1} style={{ margin: 0 }}>
          <Link to={`/novel/${data.novel.id}`} style={{ color: '#8484F4' }}>
            {data.novel.title}
          </Link>
        </Typography.Title>
      </div>

      <Divider size="middle" style={{ background: theme.color + '44' }} />
      <ReaderNavBar data={data} />

      {data.content ? (
        <ReaderVerticalContent data={data} />
      ) : (
        <Flex
          gap={15}
          vertical
          align="center"
          justify="center"
          style={{ flex: 1, margin: 10, height: '100%' }}
        >
          {job && !job.is_done ? (
            <>
              <JobDetailsCard job={job} />
              <Button href={`/job/${job.id}`}>View Request</Button>
            </>
          ) : (
            <>
              <Empty
                description="No contents available"
                styles={{ description: { color: theme.color } }}
              />
              {!autoFetch && (
                <Button
                  onClick={() =>
                    store.dispatch(Reader.action.setAutoFetch(true))
                  }
                >
                  Enable Auto Fetch
                </Button>
              )}
            </>
          )}
        </Flex>
      )}
    </Flex>
  );
};
