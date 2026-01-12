import { Auth } from '@/store/_auth';
import type { Job } from '@/types';
import { useMemo } from 'react';
import { useSelector } from 'react-redux';

export const JobErrorDetailsCard: React.FC<{ job: Job }> = ({ job }) => {
  const isAdmin = useSelector(Auth.select.isAdmin);

  if (!job.error) {
    return null;
  }

  const html = useMemo(() => {
    const lines = (job.error || '')
      .split('\n')
      .filter(Boolean)
      .map((line) => line.replace(/^\s+/, '&nbsp;'));
    if (isAdmin) {
      return lines.join('<br/>');
    } else if (lines.length > 0) {
      return lines[lines.length - 1];
    }
    return 'Unknown error';
  }, [job.error, isAdmin]);

  return (
    <div style={{ margin: '15px 0' }}>
      <pre
        style={{
          fontSize: '0.775rem',
          maxHeight: 300,
          margin: 0,
          marginBottom: 10,
          padding: '10px 20px',
          whiteSpace: 'nowrap',
          overflow: 'auto',
          color: '#f8f749',
          border: '1px solid #f8f749',
          background: '#f8f74910',
          borderRadius: 7,
        }}
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </div>
  );
};
