import { Auth } from '@/store/_auth';
import { JobStatus, type Job } from '@/types';
import { stringifyError } from '@/utils/errors';
import { CloseOutlined, ReloadOutlined } from '@ant-design/icons';
import { Button, message, type ButtonProps } from 'antd';
import axios from 'axios';
import { useState } from 'react';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { JobIssueReportButton } from './JobIssueReportButton';

export const JobActionButtons: React.FC<{
  job: Job;
  onChange?: () => any;
  size?: ButtonProps['size'];
}> = ({ job, size, onChange }) => {
  const navigate = useNavigate();
  const isAdmin = useSelector(Auth.select.isAdmin);
  const currentUser = useSelector(Auth.select.user);
  const [messageApi, contextHolder] = message.useMessage();

  const [busy, setBusy] = useState<boolean>(false);

  const cancelJob = async () => {
    try {
      setBusy(true);
      await axios.post(`/api/job/${job.id}/cancel`);
      if (onChange) onChange();
    } catch (err) {
      messageApi.open({
        type: 'error',
        content: stringifyError(err, 'Something went wrong!'),
      });
    } finally {
      setBusy(false);
    }
  };

  const replayJob = async () => {
    try {
      setBusy(true);
      const result = await axios.post<Job>(`/api/job/${job.id}/replay`, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      navigate({ pathname: `/job/${result.data.id}` });
    } catch (err) {
      messageApi.open({
        type: 'error',
        content: stringifyError(err, 'Something went wrong!'),
      });
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      {contextHolder}
      {job.status === JobStatus.FAILED && (
        <JobIssueReportButton size={size} job={job} />
      )}
      {job.is_done && (
        <Button size={size} onClick={replayJob} loading={busy}>
          <ReloadOutlined /> Replay
        </Button>
      )}
      {(isAdmin || job.user_id === currentUser?.id) && !job.is_done && (
        <Button size={size} danger onClick={cancelJob} loading={busy}>
          <CloseOutlined /> Cancel
        </Button>
      )}
    </>
  );
};
