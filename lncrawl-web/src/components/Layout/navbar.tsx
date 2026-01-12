import {
  BookOutlined,
  CloseOutlined,
  DeploymentUnitOutlined,
  FileDoneOutlined,
  FolderOpenOutlined,
  MenuFoldOutlined,
} from '@ant-design/icons';
import { Button, Drawer, Flex, theme } from 'antd';
import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { MainLayoutSidebar } from './sidebar';

export const MobileNavbar: React.FC = () => {
  const navigate = useNavigate();
  const { token } = theme.useToken();
  const { pathname: currentPath } = useLocation();
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    if (drawerOpen) {
      setDrawerOpen(false);
    }
  }, [currentPath]);

  const handleNavClick = (path: string) => {
    navigate(path);
  };

  return (
    <>
      <Flex
        gap={4}
        align="center"
        justify="space-between"
        style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          zIndex: 1000,
          padding: '4px 16px',
          background: token.colorBgContainer,
          boxShadow: '0 -2px 8px rgba(0, 0, 0, 0.06)',
          borderTop: `1px solid ${token.colorBorderSecondary}`,
        }}
      >
        <NavbarButton
          label="Requests"
          icon={<DeploymentUnitOutlined />}
          active={currentPath === '/'}
          onClick={() => handleNavClick('/')}
        />
        <NavbarButton
          label="Novels"
          icon={<BookOutlined />}
          active={currentPath === '/novels'}
          onClick={() => handleNavClick('/novels')}
        />
        <NavbarButton
          label="Libraries"
          icon={<FolderOpenOutlined />}
          active={currentPath === '/libraries'}
          onClick={() => handleNavClick('/libraries')}
        />
        <NavbarButton
          label="Crawlers"
          icon={<FileDoneOutlined />}
          active={currentPath === '/meta/sources'}
          onClick={() => handleNavClick('/meta/sources')}
        />
        <NavbarButton
          label="More"
          icon={<MenuFoldOutlined />}
          onClick={() => setDrawerOpen((v) => !v)}
        />
      </Flex>

      <Drawer
        size={250}
        closable={false}
        placement="right"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        styles={{ body: { padding: 0 } }}
      >
        <MainLayoutSidebar fullWidth />
        <Button
          type="text"
          shape="circle"
          icon={<CloseOutlined />}
          onClick={() => setDrawerOpen(false)}
          style={{ position: 'absolute', top: 10, right: 10, zIndex: 5 }}
        />
      </Drawer>
    </>
  );
};

const NavbarButton: React.FC<{
  label: string;
  icon: React.ReactNode;
  active?: boolean;
  onClick: React.MouseEventHandler<HTMLDivElement>;
}> = ({ label, icon, active, onClick }) => {
  const { token } = theme.useToken();
  return (
    <Flex
      gap={0}
      vertical
      align="center"
      onClick={onClick}
      style={{
        fontSize: 11,
        fontWeight: 500,
        cursor: 'pointer',
        padding: '4px 8px',
        opacity: active ? 1 : 0.9,
        color: active ? token.colorSuccess : token.colorText,
      }}
    >
      <span style={{ fontSize: 18 }}>{icon}</span>
      <span>{label}</span>
    </Flex>
  );
};
