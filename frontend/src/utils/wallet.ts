// src/utils/wallet.ts

export const hasEthereum = (): boolean => {
  const w: any = window;
  return typeof w !== "undefined" && typeof w.ethereum !== "undefined";
};

export const connectMetaMask = async (): Promise<string[] | null> => {
  const w: any = window;
  if (!hasEthereum()) return null;
  try {
    const accounts = await w.ethereum.request({ method: "eth_requestAccounts" });
    return Array.isArray(accounts) ? accounts : null;
  } catch (err) {
    // bubble up or log as needed
    console.error("MetaMask connection failed:", err);
    return null;
  }
};
