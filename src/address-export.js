import { validateMnemonic, mnemonicToSeedSync } from '@scure/bip39';
import { wordlist } from '@scure/bip39/wordlists/english';
import { HDKey } from '@scure/bip32';
import { bech32 } from '@scure/base';
import { sha256 } from '@noble/hashes/sha256';
import { ripemd160 } from '@noble/hashes/ripemd160';
import { keccak_256 } from '@noble/hashes/sha3';
import { secp256k1 } from '@noble/curves/secp256k1';

const BTC_PATH = "m/84'/0'/0'/0/0";
const EVM_PATH = "m/44'/60'/0'/0/0";

function toHex(bytes) {
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('');
}

function checksumAddress(addressBytes) {
  const lower = toHex(addressBytes);
  const hash = toHex(keccak_256(new TextEncoder().encode(lower)));
  let checked = '0x';
  for (let i = 0; i < lower.length; i++) {
    checked += parseInt(hash[i], 16) >= 8 ? lower[i].toUpperCase() : lower[i];
  }
  return checked;
}

export function deriveAddresses(phrase) {
  const mnemonic = phrase.trim().toLowerCase().replace(/\s+/g, ' ');
  if (mnemonic.split(' ').length !== 12 || !validateMnemonic(mnemonic, wordlist)) {
    throw new Error('Invalid 12-word BIP-39 phrase');
  }

  // Everything below runs in the browser. No phrase, seed, or private key is uploaded.
  const root = HDKey.fromMasterSeed(mnemonicToSeedSync(mnemonic));
  const btcPublicKey = root.derive(BTC_PATH).publicKey;
  const btcHash160 = ripemd160(sha256(btcPublicKey));
  const btc = bech32.encode('bc', [0, ...bech32.toWords(btcHash160)]);

  const evmPublicKey = root.derive(EVM_PATH).publicKey;
  const uncompressed = secp256k1.ProjectivePoint.fromHex(evmPublicKey).toRawBytes(false);
  const evm = checksumAddress(keccak_256(uncompressed.slice(1)).slice(-20));

  // ETH, BNB Smart Chain (BEP-20), and Base use the same EVM key/address here.
  return { btc, eth: evm, bnbSmartChain: evm, base: evm };
}

export async function exportAddresses(file, onProgress = () => {}) {
  // Never include mnemonic words in the export, only line numbers and public addresses.
  const lines = (await file.text()).split(/\r?\n/);
  const rows = ['phrase_line,btc_native_segwit,ethereum,bnb_smart_chain,base,status'];
  let valid = 0;
  let invalid = 0;

  for (let index = 0; index < lines.length; index++) {
    if (!lines[index].trim()) continue;
    try {
      const { btc, eth, bnbSmartChain, base } = deriveAddresses(lines[index]);
      rows.push(`${index + 1},${btc},${eth},${bnbSmartChain},${base},ok`);
      valid++;
    } catch (error) {
      if (error.message !== 'Invalid 12-word BIP-39 phrase') throw error;
      rows.push(`${index + 1},,,,,invalid BIP-39 phrase`);
      invalid++;
    }
    if ((valid + invalid) % 10 === 0) {
      onProgress(`Processed ${valid + invalid} phrases…`);
      // Let the UI update and keep the browser responsive during large files.
      await new Promise((resolve) => setTimeout(resolve, 0));
    }
  }

  if (valid + invalid === 0) throw new Error('The selected TXT file is empty.');
  return { csv: rows.join('\r\n') + '\r\n', valid, invalid };
}

function setupExportUI() {
  const form = document.getElementById('address-export-form');
  const input = document.getElementById('phrase-file');
  const button = document.getElementById('address-export-button');
  const status = document.getElementById('export-status');
  if (!form || !input || !button || !status) return;

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const file = input.files[0];
    if (!file || !file.name.toLowerCase().endsWith('.txt')) {
      status.textContent = 'Choose a phrase TXT file first (one 12-word phrase per line).';
      return;
    }
    button.disabled = true;
    status.textContent = 'Reading the file locally…';
    try {
      const { csv, valid, invalid } = await exportAddresses(file, (message) => {
        status.textContent = message;
      });
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `addresses_${file.name.replace(/\.txt$/i, '')}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 60000);
      status.textContent = `Download ready: ${valid} valid, ${invalid} invalid phrase(s). Invalid rows have no addresses. No phrases were uploaded or included in the CSV.`;
    } catch (error) {
      status.textContent = error.message || 'Could not process the TXT file.';
    } finally {
      button.disabled = false;
    }
  });
}

if (typeof document !== 'undefined') setupExportUI();
