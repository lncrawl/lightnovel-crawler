import './fonts.css';
import './index.scss';

import { store } from '@/store';
import { Reader } from '@/store/_reader';
import { type Job, type ReadChapter } from '@/types';
import { stringifyError } from '@/utils/errors';
import { formatFromNow } from '@/utils/time';
import { Button, Flex, Result, Spin } from 'antd';
import axios from 'axios';
import { LRUCache } from 'lru-cache';
import { useEffect, useState } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { useSelector } from 'react-redux';
import { useParams } from 'react-router-dom';
import { ReaderVerticalLayout } from './ReaderVerticalLayout';

const fetchJobs = new LRUCache<string, Promise<Job>>({ max: 1000 });
const cache = new LRUCache<string, Promise<ReadChapter>>({ max: 1000 });

async function fetchChapter(id: string) {
  const { data } = await axios.get<ReadChapter>(`/api/chapter/${id}/read`);
  if (data.content) {
    const header = renderToStaticMarkup(
      <>
        <h1 style={{ marginBottom: 6 }}>{data.chapter.title.trim()}</h1>
        <div style={{ fontSize: 12, opacity: 0.8, marginBottom: 25 }}>
          {data.chapter.serial} of {data.novel.chapter_count}
          <span> | </span>
          Updated {formatFromNow(data.chapter.updated_at)}
        </div>
      </>
    );
    const clean = data.content.replace(
      /<p>(\s+)|(&nbsp;)+<\/p>(\n|\s|<br\/>)+/gim,
      ''
    );
    data.content = header + clean;
  }
  return data;
}

function fetchChapterCached(id: string): Promise<ReadChapter> {
  if (!cache.has(id)) {
    cache.set(id, fetchChapter(id));
  }
  return cache.get(id)!;
}

function createFetchJob(id: string) {
  if (!fetchJobs.has(id)) {
    const promise = axios
      .get<Job>(`/api/chapter/${id}/fetch`)
      .then((res) => res.data);
    fetchJobs.set(id, promise);
  }
  return fetchJobs.get(id)!;
}

export const NovelReaderPage: React.FC<any> = () => {
  const { id } = useParams<{ id: string }>();
  const autoFetch = useSelector(Reader.select.autoFetch);

  const [refreshId, setRefreshId] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();
  const [data, setData] = useState<ReadChapter>();
  const [job, setJob] = useState<Job>();

  // current chapter content data
  useEffect(() => {
    if (id) {
      const fetchChapter = async () => {
        setError(undefined);
        try {
          if (fetchJobs.has(id)) {
            cache.delete(id);
          } else {
            setJob(undefined);
          }
          const data = await fetchChapterCached(id);
          setData(data);
        } catch (err) {
          setError(stringifyError(err));
        } finally {
          setLoading(false);
        }
      };
      fetchChapter();
    } else {
      setData(undefined);
      setJob(undefined);
      setError('No chapter ID in URL');
    }
  }, [id, refreshId]);

  // preload previous chapter
  useEffect(() => {
    if (data?.previous_id) {
      fetchChapterCached(data.previous_id).then((prev) => {
        if (autoFetch && !prev.chapter.is_done) {
          createFetchJob(prev.chapter.id);
        }
      });
    }
  }, [data?.previous_id, autoFetch]);

  // preload next chapter
  useEffect(() => {
    if (data?.next_id) {
      fetchChapterCached(data.next_id).then((next) => {
        if (autoFetch && !next.chapter.is_done) {
          createFetchJob(next.chapter.id);
        }
      });
    }
  }, [data?.next_id, autoFetch]);

  // get job details if auto fetch is enabled
  useEffect(() => {
    if (autoFetch && data?.chapter?.id && !data.chapter.is_done) {
      createFetchJob(data.chapter.id).then(setJob).catch(console.error);
    } else {
      setJob(undefined);
    }
  }, [autoFetch, data?.chapter.id, data?.chapter.is_done]);

  // auto refresh job status
  useEffect(() => {
    if (!job?.id || !data?.chapter.id || data.chapter.is_done) {
      return;
    }
    const id = data.chapter.id;
    if (job.is_done) {
      cache.delete(id);
      setRefreshId((v) => v + 1);
    } else {
      const refreshJob = async () => {
        try {
          const { data } = await axios.get<Job>(`/api/job/${job.id}`);
          fetchJobs.set(id, Promise.resolve(data));
          setJob(data);
        } catch {}
      };
      const iid = setInterval(refreshJob, 1000);
      return () => clearInterval(iid);
    }
  }, [data?.chapter.id, data?.chapter.is_done, job?.is_done, job?.id]);

  useEffect(() => {
    if (!data) return;

    store.dispatch(Reader.action.setSepakPosition(0));
    if (data && !data.content && data.chapter.is_done) {
      store.dispatch(Reader.action.setSpeaking(false));
    }

    const fid = requestAnimationFrame(() => {
      const mainEl = document.querySelector('main');
      if (mainEl) {
        mainEl.scrollTop = 0;
      }
    });
    return () => cancelAnimationFrame(fid);
  }, [data]);

  if (loading) {
    return (
      <Flex
        align="center"
        justify="center"
        style={{ height: 'calc(100vh - 60px)' }}
      >
        <Spin size="large" style={{ margin: '50px 0' }} />
      </Flex>
    );
  }

  if (error || !data || !id) {
    return (
      <Flex
        align="center"
        justify="center"
        style={{ height: 'calc(100vh - 60px)' }}
      >
        <Result
          status="404"
          title="Failed to load chapter content"
          subTitle={error}
          extra={[
            <Button
              onClick={() => {
                setLoading(true);
                setRefreshId((v) => v + 1);
              }}
            >
              Retry
            </Button>,
          ]}
        />
      </Flex>
    );
  }

  return <ReaderVerticalLayout key={id} data={data} job={job} />;
};
