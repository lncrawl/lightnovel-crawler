import { PrivacyPolicy } from '@/pages/Signup/PrivacyPolicy';
import { TermsOfService } from '@/pages/Signup/TermsOfService';
import { Auth } from '@/store/_auth';
import {
  BookOutlined,
  CommentOutlined,
  ControlOutlined,
  DeploymentUnitOutlined,
  FileDoneOutlined,
  FolderOpenOutlined,
  QuestionCircleOutlined,
  SettingOutlined,
  TeamOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { Divider, Flex, Layout, Menu, theme } from 'antd';
import { useSelector } from 'react-redux';
import { Link, useLocation } from 'react-router-dom';
import { DonateButton } from '../DonateButton';
import { UserInfoCard } from '../UserInfoCard';

function getClassName(currentPath: string, path: string): string | undefined {
  if (currentPath === path) {
    return 'ant-menu-item-selected';
  }
  return undefined;
}

export const MainLayoutSidebar: React.FC<{
  fullWidth?: boolean;
}> = ({ fullWidth }) => {
  const { token } = theme.useToken();
  const { pathname: currentPath } = useLocation();
  const isAdmin = useSelector(Auth.select.isAdmin);

  return (
    <Layout.Sider
      theme="light"
      collapsible={false}
      width={fullWidth ? '100%' : 250}
      style={{
        height: fullWidth ? '100%' : '100vh',
      }}
    >
      <Flex
        vertical
        style={{
          height: '100%',
          borderRight: `1px solid ${token.colorBorderSecondary}`,
        }}
      >
        <Menu
          key={currentPath}
          mode="inline"
          inlineIndent={15}
          subMenuOpenDelay={0}
          openKeys={['admin']}
          style={{
            flex: 1,
            overflow: 'auto',
            borderRight: 'none',
          }}
        >
          <Menu.ItemGroup
            title={<UserInfoCard />}
            style={{
              background: 'none',
              height: 'fit-content',
            }}
          />
          <Menu.Divider />
          <Menu.Item
            icon={<DeploymentUnitOutlined />}
            className={getClassName(currentPath, '/')}
          >
            <Link to="/">Requests</Link>
          </Menu.Item>
          <Menu.Item
            icon={<BookOutlined />}
            className={getClassName(currentPath, '/novels')}
          >
            <Link to="/novels">Novels</Link>
          </Menu.Item>
          <Menu.Item
            icon={<FolderOpenOutlined />}
            className={getClassName(currentPath, '/libraries')}
          >
            <Link to="/libraries">Libraries</Link>
          </Menu.Item>
          <Menu.Item
            icon={<FileDoneOutlined />}
            className={getClassName(currentPath, '/meta/sources')}
          >
            <Link to="/meta/sources">Crawlers</Link>
          </Menu.Item>
          <Menu.Item
            icon={<CommentOutlined />}
            className={getClassName(currentPath, '/feedbacks')}
          >
            <Link to="/feedbacks">Feedbacks</Link>
          </Menu.Item>
          <Menu.Divider />
          <Menu.Item
            icon={<UserOutlined />}
            className={getClassName(currentPath, '/profile')}
          >
            <Link to="/profile">Profile</Link>
          </Menu.Item>
          <Menu.Item
            icon={<SettingOutlined />}
            className={getClassName(currentPath, '/settings')}
          >
            <Link to="/settings">Settings</Link>
          </Menu.Item>
          <Menu.Divider />
          <Menu.Item
            icon={<QuestionCircleOutlined />}
            className={getClassName(currentPath, '/tutorial')}
          >
            <Link to="/tutorial">Tutorial</Link>
          </Menu.Item>
          {isAdmin && <Menu.Divider />}
          {isAdmin && (
            <Menu.SubMenu
              key="admin"
              title="Administration"
              icon={<ControlOutlined />}
            >
              <Menu.Item
                icon={<TeamOutlined />}
                className={getClassName(currentPath, '/admin/users')}
              >
                <Link to="/admin/users">Users</Link>
              </Menu.Item>
            </Menu.SubMenu>
          )}
        </Menu>

        <Divider style={{ margin: 0 }} />
        <Flex
          gap={5}
          align="center"
          justify="center"
          style={{ fontSize: 11, padding: '8px 16px' }}
        >
          <DonateButton />
        </Flex>

        <Divider style={{ margin: 0 }} />
        <Flex
          gap={5}
          align="center"
          justify="center"
          style={{ fontSize: 11, padding: '4px 16px' }}
        >
          <PrivacyPolicy />
          <Divider orientation="vertical" />
          <TermsOfService />
        </Flex>
      </Flex>
    </Layout.Sider>
  );
};
