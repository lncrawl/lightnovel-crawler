import LncrawlImage from '@/assets/lncrawl.svg';
import { Avatar, Divider, Grid, Layout, Typography } from 'antd';
import { Outlet, useNavigate } from 'react-router-dom';
import { MobileNavbar } from './navbar';
import { MainLayoutSidebar } from './sidebar';

export const MainLayout: React.FC<{
  noPadding?: boolean;
}> = ({ noPadding }) => {
  const navigate = useNavigate();
  const { md } = Grid.useBreakpoint();

  return (
    <Layout>
      {md && <MainLayoutSidebar />}

      <Layout.Content
        style={{
          height: '100vh',
          overflow: 'auto',
          position: 'relative',
          padding: noPadding ? 0 : md ? 20 : 10,
          paddingBottom: noPadding ? 0 : md ? 50 : 100,
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
                margin: noPadding ? 7 : 0,
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
            {!noPadding && <Divider size="small" />}
          </>
        )}

        <div
          style={{
            margin: '0 auto',
            transition: 'all 0.2s ease-in-out',
            maxWidth: noPadding ? undefined : 1200,
            minHeight: noPadding ? 'calc(100% - 45px)' : 'calc(100% - 60px)',
          }}
        >
          <Outlet />
        </div>
      </Layout.Content>

      {!md && <MobileNavbar />}
    </Layout>
  );
};
