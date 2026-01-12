import { ErrorState } from '@/components/Loading/ErrorState';
import { LoadingState } from '@/components/Loading/LoadingState';
import { FeedbackStatusTag } from '@/components/Tags/FeedbackStatusTag';
import { FeedbackTypeTag } from '@/components/Tags/FeedbackTypeTag';
import { Auth } from '@/store/_auth';
import type { Feedback, Job, User } from '@/types';
import { FeedbackStatus } from '@/types';
import { stringifyError } from '@/utils/errors';
import { formatFromNow } from '@/utils/time';
import {
  CalendarOutlined,
  LeftOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { Card, Divider, Flex, Grid, Space, Typography } from 'antd';
import axios from 'axios';
import { useEffect, useMemo, useState } from 'react';
import { useSelector } from 'react-redux';
import { useNavigate, useParams } from 'react-router-dom';
import { UserDetailsCard } from '../JobDetails/UserDetailsCard';
import { FeedbackDeleteButton } from './FeedbackDeleteButton';
import { FeedbackEditButton } from './FeedbackEditButton';
import { FeedbackRespondButton } from './FeedbackRespondButton';
import { JobDetailsCard } from '../JobDetails/JobDetailsCard';

export const FeedbackDetailsPage: React.FC<any> = () => {
  const { id } = useParams<{ id: string }>();
  const { sm } = Grid.useBreakpoint();
  const navigate = useNavigate();
  const user = useSelector(Auth.select.user);
  const isAdmin = useSelector(Auth.select.isAdmin);

  const [feedback, setFeedback] = useState<Feedback>();
  const [owner, setOwner] = useState<User>();
  const [job, setJob] = useState<Job>();
  const [refreshId, setRefreshId] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();

  const isOwner = useMemo(
    () => Boolean(feedback && user && feedback.user_id === user.id),
    [feedback, user]
  );

  useEffect(() => {
    const fetchJob = async (jobId: string) => {
      setError(undefined);
      try {
        const { data } = await axios.get<Job>(`/api/job/${jobId}`);
        setJob(data);
      } catch (err: any) {
        setError(stringifyError(err));
      } finally {
        setLoading(false);
      }
    };

    const fetchFeedback = async (feedbackId: string) => {
      setError(undefined);
      try {
        const { data } = await axios.get<Feedback>(
          `/api/feedback/${feedbackId}`
        );
        setFeedback(data);
        if (data.extra?.job_id) {
          fetchJob(data.extra.job_id);
        }
      } catch (err: any) {
        setError(stringifyError(err));
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchFeedback(id);
    }
  }, [id, refreshId]);

  useEffect(() => {
    const fetchOwner = async (userId: string) => {
      try {
        const { data } = await axios.get<User>(`/api/user/${userId}`);
        setOwner(data);
      } catch (err) {
        console.error('Failed to fetch feedback owner', err);
      }
    };
    if (feedback?.user_id && isAdmin) {
      fetchOwner(feedback.user_id);
    }
  }, [feedback?.user_id, isAdmin]);

  if (loading) {
    return <LoadingState />;
  }

  if (error || !feedback || !id) {
    return (
      <ErrorState
        error={error}
        title="Failed to load feedback details"
        onRetry={() => {
          setLoading(true);
          setRefreshId((v) => v + 1);
        }}
      />
    );
  }

  return (
    <>
      {/* Feedback Details Header */}
      <Flex
        justify={'space-between'}
        align={'center'}
        style={{ marginBottom: 16 }}
        gap={8}
      >
        <Typography.Link
          style={{ flex: 1 }}
          onClick={() => navigate('/feedbacks')}
        >
          <LeftOutlined /> {sm ? 'Back to Feedback' : 'Back'}
        </Typography.Link>
        <Space size="small">
          {isAdmin && (
            <FeedbackRespondButton
              feedback={feedback}
              onSuccess={setFeedback}
            />
          )}
          {isOwner && feedback.status === FeedbackStatus.PENDING && (
            <FeedbackEditButton feedback={feedback} onSuccess={setFeedback} />
          )}
          {(isAdmin || isOwner) && <FeedbackDeleteButton feedback={feedback} />}
        </Space>
      </Flex>

      {/* Owner Details Section */}
      {owner && <UserDetailsCard user={owner} title="From" />}

      {/* Feedback Details Section */}
      <Card style={{ marginTop: 16 }}>
        <Flex
          vertical={!sm}
          align={sm ? 'center' : 'start'}
          justify={sm ? 'space-between' : 'center'}
          gap={sm ? 16 : 4}
        >
          <Typography.Title level={4} style={{ margin: 0, flex: 1 }}>
            {feedback.subject}
          </Typography.Title>
          <Space size="small">
            {!feedback.admin_notes && (
              <FeedbackStatusTag status={feedback.status} />
            )}
            <FeedbackTypeTag value={feedback.type} />
          </Space>
        </Flex>

        <Typography.Paragraph style={{ whiteSpace: 'pre-wrap', marginTop: 16 }}>
          {feedback.message}
        </Typography.Paragraph>

        <Space size="small" separator={<Divider orientation="vertical" />}>
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
            <UserOutlined /> {feedback?.extra?.user_name || 'Unknown'}
          </Typography.Text>

          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
            <CalendarOutlined /> Posted {formatFromNow(feedback.created_at)}
          </Typography.Text>

          {feedback.updated_at !== feedback.created_at && (
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              Updated {formatFromNow(feedback.updated_at)}
            </Typography.Text>
          )}
        </Space>
      </Card>

      {/* Job Details Section */}
      {job && (
        <div style={{ marginTop: 16 }}>
          <JobDetailsCard job={job} hideActions />
        </div>
      )}

      {/* Admin Notes Section */}
      {feedback.admin_notes && (
        <Card style={{ marginTop: 16 }}>
          <Flex align="center" justify="space-between" gap={16}>
            <Typography.Title level={4} style={{ margin: 0, flex: 1 }}>
              Response
            </Typography.Title>
            <FeedbackStatusTag status={feedback.status} />
          </Flex>

          <Typography.Paragraph
            style={{ whiteSpace: 'pre-wrap', marginTop: 16 }}
          >
            {feedback.admin_notes}
          </Typography.Paragraph>
        </Card>
      )}
    </>
  );
};

export default FeedbackDetailsPage;
