import { Flex, Typography } from 'antd';
import { QRCodeSVG } from 'qrcode.react';
import type { CryptoInfo } from './data';

export const CryptoDonationTab: React.FC<{
  crypto: CryptoInfo;
}> = ({ crypto }) => {
  return (
    <Flex vertical align="center" justify="center">
      <div
        style={{
          padding: '20px',
          borderRadius: '8px',
          display: 'inline-block',
          backgroundColor: '#fff',
          marginBottom: '8px',
        }}
      >
        <QRCodeSVG
          value={crypto.address}
          size={256}
          level="M"
          style={{ width: '100%', height: '100%' }}
        />
      </div>

      <Typography.Text
        copyable
        style={{
          fontFamily: 'monospace',
          fontSize: '16px',
          fontWeight: 600,
          letterSpacing: '0.07em',
          wordBreak: 'break-all',
          color: '#d9f134',
          textAlign: 'center',
          padding: '5px 10px',
          borderRadius: '8px',
          border: '1px solid #a9d134',
        }}
      >
        {crypto.address}
      </Typography.Text>

      <Typography.Text type="secondary" style={{ fontSize: '12px' }}>
        Scan the QR code or copy the address above
      </Typography.Text>
    </Flex>
  );
};
