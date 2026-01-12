export interface CryptoInfo {
  name: string;
  icon: string;
  symbol: string;
  address: string;
}

// Cryptocurrency wallet addresses
export const CRYPTO_WALLETS: CryptoInfo[] = [
  {
    name: 'Bitcoin',
    symbol: 'BTC',
    address: '1CVjbgQpXdtzsXMA6Rtrk5WvNiWuAQnLE',
    icon: '₿',
  },
  {
    name: 'Ethereum',
    symbol: 'ETH',
    address: '0xe925b6db4ee0bbc294a6a7d5b64a7c37e66199fa',
    icon: 'Ξ',
  },
  {
    name: 'Solana',
    symbol: 'SOL',
    address: '6TRj4JD6ZWTnR5awC4x1o4RvU9fweFZd9QgL28Nk5oGC',
    icon: '◎',
  },
  {
    name: 'Litecoin',
    symbol: 'LTC',
    address: 'LYCWMBUyUYjhQFNibfAaJoBs2HqmgviWkb',
    icon: 'Ł',
  },
];
