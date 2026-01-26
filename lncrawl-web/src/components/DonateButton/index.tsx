import { getGradientForId } from '@/utils/gradients';
import { HeartFilled } from '@ant-design/icons';
import { Avatar, Button, Collapse, Modal, Space, Typography } from 'antd';
import { useState } from 'react';
import { CryptoDonationTab } from './CryptoDonationTab';
import { CRYPTO_WALLETS } from './data';

export const DonateButton = () => {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Button
        block
        type="primary"
        icon={<HeartFilled />}
        onClick={() => setOpen(true)}
      >
        Donate
      </Button>

      <Modal
        title={
          <Typography.Title level={4} style={{ margin: 0 }}>
            Donate with Cryptocurrency
          </Typography.Title>
        }
        open={open}
        onCancel={() => setOpen(false)}
        footer={null}
        width={650}
        destroyOnHidden
      >
        <Typography.Text
          type="secondary"
          style={{ fontSize: '14px', textAlign: 'center' }}
        >
          Your donations are greatly appreciated and help keep the project
          running.
        </Typography.Text>

        <Collapse
          accordion
          style={{ marginTop: '16px' }}
          defaultActiveKey={[CRYPTO_WALLETS[0].symbol]}
          items={CRYPTO_WALLETS.map((crypto) => ({
            key: crypto.symbol,
            label: (
              <Space>
                <Avatar
                  size={24}
                  icon={crypto.icon}
                  style={{
                    color: '#d9f134',
                    background: getGradientForId(crypto.name),
                  }}
                />
                <Typography.Text style={{ fontSize: '16px', fontWeight: 600 }}>
                  {crypto.name} ({crypto.symbol})
                </Typography.Text>
              </Space>
            ),
            children: <CryptoDonationTab crypto={crypto} />,
          }))}
        />

        <Space vertical style={{ marginTop: '16px', textAlign: 'center' }}>
          <Typography.Text type="success">
            Thank you for your support! 🙏
          </Typography.Text>
        </Space>
      </Modal>
    </>
  );
};
