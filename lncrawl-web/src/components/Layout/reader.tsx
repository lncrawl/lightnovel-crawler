import LncrawlImage from '@/assets/lncrawl.svg';
import { Avatar, Grid, Layout, Typography } from 'antd';
import { useRef, useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { MobileNavbar } from './navbar';
import { MainLayoutSidebar } from './sidebar';

export const ReaderLayout: React.FC<any> = () => {
  const navigate = useNavigate();
  const { md } = Grid.useBreakpoint();
  const previousPosition = useRef<number>(0);
  const [showNavbar, setShowNavbar] = useState(true);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const position = Math.round(e.currentTarget.scrollTop / 10);
    if (position > previousPosition.current) {
      setShowNavbar(false);
    } else if (position < previousPosition.current) {
      setShowNavbar(true);
    }
    previousPosition.current = position;
  };

  return (
    <Layout>
      {md && <MainLayoutSidebar />}

      <Layout.Content
        onScroll={md ? undefined : handleScroll}
        style={{
          height: '100vh',
          overflow: 'auto',
          position: 'relative',
          padding: 0,
        }}
      >
        {!md && (
          <>
            <Typography.Title
              onClick={() => navigate('/')}
              level={4}
              style={{
                textAlign: 'center',
                fontSize: 18,
                margin: 7,
              }}
            >
              <Avatar
                shape="square"
                src={LncrawlImage}
                size={24}
                style={{ paddingBottom: 3 }}
              />
              Lightnovel Crawler
            </Typography.Title>
          </>
        )}

        <div
          style={{
            margin: '0 auto',
            transition: 'all 0.2s ease-in-out',
            minHeight: 'calc(100% - 45px)',
          }}
        >
          <Outlet />
        </div>
      </Layout.Content>

      {!md && showNavbar && <MobileNavbar />}
    </Layout>
  );
};
