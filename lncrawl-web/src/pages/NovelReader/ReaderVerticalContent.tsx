import cx from 'classnames';
import styles from './ReaderVerticalLayout.module.scss';

import { API_BASE_URL } from '@/config';
import { store } from '@/store';
import { Auth } from '@/store/_auth';
import { Reader } from '@/store/_reader';
import type { ReadChapter } from '@/types';
import { useEffect, useMemo, useState } from 'react';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { getVoices } from '../SettingsPage/ReaderSettings/VoiceSettings';

function useSpeechSynthesis(
  contentEl: HTMLDivElement | null,
  data: ReadChapter
) {
  const navigate = useNavigate();

  const voiceName = useSelector(Reader.select.voice);
  const speaking = useSelector(Reader.select.speaking);
  const position = useSelector(Reader.select.speakPosition);
  const voiceSpeed = useSelector(Reader.select.voiceSpeed);
  const voicePitch = useSelector(Reader.select.voicePitch);

  const [loading, setLoading] = useState<boolean>(true);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);

  const voice = useMemo(
    () => voices.find((x) => x.name === voiceName) || voices[0],
    [voices, voiceName]
  );

  useEffect(() => {
    getVoices()
      .then(setVoices)
      .finally(() => setLoading(false));

    const aborter = new AbortController();
    window.addEventListener(
      'beforeunload',
      () => {
        window.speechSynthesis.cancel();
        store.dispatch(Reader.action.setSpeaking(false));
      },
      { signal: aborter.signal }
    );
    return () => aborter.abort();
  }, []);

  useEffect(() => {
    if (!contentEl || !speaking) {
      return;
    }

    if (position >= contentEl.children.length) {
      store.dispatch(Reader.action.setSepakPosition(0));
      if (data.next_id) {
        navigate(`/read/${data.next_id}`);
      } else {
        store.dispatch(Reader.action.setSpeaking(false));
      }
      return;
    }

    const childEl = contentEl.children[position];

    const text = childEl.textContent;
    if (!text?.length) {
      store.dispatch(Reader.action.setSepakPosition(position + 1));
      return;
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.voice = voice;
    utterance.rate = voiceSpeed;
    utterance.pitch = voicePitch;

    utterance.addEventListener('end', () => {
      store.dispatch(Reader.action.setSepakPosition(position + 1));
    });

    const tid = setTimeout(() => {
      window.speechSynthesis.speak(utterance);
    }, 50);

    return () => {
      clearTimeout(tid);
      requestAnimationFrame(() => {
        window.speechSynthesis.cancel();
      });
    };
  }, [
    data,
    contentEl,
    speaking,
    voice,
    voiceSpeed,
    voicePitch,
    position,
    loading,
    navigate,
  ]);

  useEffect(() => {
    if (loading || !contentEl || !speaking || !voice || !data.content) {
      return;
    }

    if (position >= contentEl.children.length) {
      store.dispatch(Reader.action.setSepakPosition(0));
      if (data.next_id) {
        navigate(`/read/${data.next_id}`);
      } else {
        store.dispatch(Reader.action.setSpeaking(false));
      }
      return;
    }

    const childEl = contentEl.children[position];

    const text = childEl.textContent;
    if (!text?.length) {
      store.dispatch(Reader.action.setSepakPosition(position + 1));
      return;
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.voice = voice;
    utterance.rate = voiceSpeed;
    utterance.pitch = voicePitch;

    utterance.addEventListener('end', () => {
      store.dispatch(Reader.action.setSepakPosition(position + 1));
    });

    const tid = setTimeout(() => {
      window.speechSynthesis.speak(utterance);
    }, 50);

    return () => {
      clearTimeout(tid);
      requestAnimationFrame(() => {
        window.speechSynthesis.cancel();
      });
    };
  }, [
    data,
    contentEl,
    speaking,
    voice,
    voiceSpeed,
    voicePitch,
    position,
    loading,
    navigate,
  ]);
}

export const ReaderVerticalContent: React.FC<{
  data: ReadChapter;
}> = ({ data }) => {
  const token = useSelector(Auth.select.authToken);
  const speaking = useSelector(Reader.select.speaking);
  const position = useSelector(Reader.select.speakPosition);
  const [contentEl, setContentEl] = useState<HTMLDivElement | null>(null);

  useSpeechSynthesis(contentEl, data);

  const contentHTML = useMemo(() => {
    if (!token || !data.content) {
      return '';
    }
    const parser = new DOMParser();
    const doc = parser.parseFromString(data.content, 'text/html');
    for (const img of doc.querySelectorAll('img')) {
      if (!img.src.includes(img.alt)) continue;
      img.src = `${API_BASE_URL}/static/novels/${data.novel.id}/images/${img.alt}.jpg?token=${token}`;
      img.loading = 'lazy';
    }
    return doc.body.innerHTML;
  }, [data.content, data.novel.id, token]);

  useEffect(() => {
    if (!speaking) return;
    const fid = requestAnimationFrame(() => {
      const childEl = contentEl?.children[position];
      childEl?.setAttribute('data-focus', 'true');
    });
    return () => {
      cancelAnimationFrame(fid);
      const childEl = contentEl?.children[position];
      childEl?.removeAttribute('data-focus');
    };
  });

  const handleClick = (e: React.MouseEvent<HTMLElement>) => {
    let target = e.target as HTMLElement | null;
    if (!contentEl || !contentEl.contains(target)) return;
    while (target && target.parentElement !== contentEl) {
      target = target.parentElement!;
    }
    if (target) {
      const index = Array.prototype.indexOf.call(contentEl.children, target);
      store.dispatch(Reader.action.setSepakPosition(index));
    }
  };

  return (
    <div
      id="chapter-content"
      ref={setContentEl}
      dangerouslySetInnerHTML={{
        __html: contentHTML,
      }}
      onPointerUp={handleClick}
      className={cx(styles.content, {
        [styles.speaking]: speaking,
      })}
    />
  );
};
