import test from 'node:test';
import assert from 'node:assert/strict';
import { deriveAddresses, exportAddresses } from './address-export.js';

const mnemonic = 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about';

test('derives known BIP84 and EVM addresses from a BIP-39 test vector', () => {
  const result = deriveAddresses(mnemonic);
  assert.equal(result.btc, 'bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu');
  assert.equal(result.eth, '0x9858EfFD232B4033E47d90003D41EC34EcaEda94');
  assert.equal(result.bnbSmartChain, result.eth);
  assert.equal(result.base, result.eth);
});

test('rejects a bad mnemonic and checksum', () => {
  assert.throws(() => deriveAddresses('not a valid phrase'), /Invalid/);
  assert.throws(() => deriveAddresses('abandon '.repeat(12).trim()), /Invalid/);
});

test('CSV contains public addresses, line numbers and no secret phrases', async () => {
  const file = { text: async () => `${mnemonic}\nnot a valid phrase\n${mnemonic}\n` };
  const { csv, valid, invalid } = await exportAddresses(file);
  assert.equal(valid, 2);
  assert.equal(invalid, 1);
  assert.equal(csv.trim().split('\r\n').length, 4);
  assert.match(csv, /^phrase_line,.*\r\n1,bc1qcr8te4kr/);
  assert.match(csv, /2,,,,,invalid BIP-39 phrase/);
  assert.match(csv, /3,bc1qcr8te4kr/);
  assert.ok(!csv.includes(mnemonic));
});

test('empty TXT does not produce a download', async () => {
  await assert.rejects(exportAddresses({ text: async () => '\n  \n' }), /empty/);
});
