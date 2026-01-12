import { JobFailCountTag } from '@/components/Tags/JobFailCountTag';
import { JobStatusTag } from '@/components/Tags/JobStatusTag';
import { JobTypeTag } from '@/components/Tags/JobTypeTag';
import { type Job } from '@/types';
import { formatDate } from '@/utils/time';
import { ClockCircleOutlined } from '@ant-design/icons';
import { Card, Flex, Grid, Space, Tag, Typography } from 'antd';
import { Link } from 'react-router-dom';
import { JobActionButtons } from '../JobDetails/JobActionButtons';
import { JobProgressCircle, JobProgressLine } from './JobProgessBar';

export const JobListItemCard: React.FC<{
  job: Job;
  onChange?: () => any;
}> = ({ job, onChange }) => {
  const { lg } = Grid.useBreakpoint();
  return (
    <Link to={`/job/${job.id}`}>
      <Card
        style={{ marginBottom: 5 }}
        styles={{
          body: { padding: 15 },
        }}
      >
        <Flex wrap align="center" justify="end" gap="15px">
          {lg && <JobProgressCircle job={job} size={48} />}

          <div style={{ flex: 1, minWidth: lg ? 0 : '100%' }}>
            <Typography.Paragraph
              ellipsis={{ rows: 2 }}
              style={{
                margin: 0,
                fontSize: '1.15rem',
                fontFamily: "'Roboto Slab', serif",
              }}
            >
              {job.job_title || `Request ${job.id}`}
            </Typography.Paragraph>

            <Space wrap style={{ marginTop: 5 }}>
              <JobStatusTag job={job} />
              <JobFailCountTag job={job} short />
              <JobTypeTag value={job.type} />
              <Tag icon={<ClockCircleOutlined />} color="default">
                {formatDate(job.created_at)}
              </Tag>
            </Space>

            {!lg && <JobProgressLine job={job} style={{ marginTop: 10 }} />}
          </div>

          <Flex
            justify="end"
            align="center"
            gap={5}
            onClick={(e) => e.preventDefault()}
          >
            <JobActionButtons job={job} size="small" onChange={onChange} />
          </Flex>
        </Flex>
      </Card>
    </Link>
  );
};
