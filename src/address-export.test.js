import test from 'node:test';
import assert from 'node:assert/strict';
import { deriveAddresses, exportAddresses, findPhraseForAddress } from './address-export.js';

const mnemonic = 'abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about';

test('derives known BIP84 and EVM addresses from a BIP-39 test vector', () => {
  const result = deriveAddresses(mnemonic);
  assert.equal(result.btc, 'bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu');
  assert.equal(result.evm, '0x9858EfFD232B4033E47d90003D41EC34EcaEda94');
  assert.deepEqual(Object.keys(result), ['btc', 'evm']);
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
  const rows = csv.trim().split('\n');
  assert.equal(rows.length, 3); // header + two valid phrases; invalid line is skipped
  assert.equal(rows[0], 'phrase_line,btc_native_segwit,evm');
  assert.equal(rows[1], '1,bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu,0x9858EfFD232B4033E47d90003D41EC34EcaEda94');
  assert.equal(rows[2], '3,bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu,0x9858EfFD232B4033E47d90003D41EC34EcaEda94');
  assert.ok(rows.every((row) => row.split(',').length === 3));
  assert.ok(!csv.includes(mnemonic));
});

test('empty or wholly invalid TXT does not produce an address file', async () => {
  await assert.rejects(exportAddresses({ text: async () => '\n  \n' }), /empty/);
  await assert.rejects(exportAddresses({ text: async () => 'not a mnemonic\n' }), /No valid/);
});

test('finds the matching phrase from the original TXT for BTC or EVM addresses', async () => {
  const other = 'test test test test test test test test test test test junk';
  const file = { text: async () => `${mnemonic}\ninvalid phrase\n${other}\n` };
  const btc = await findPhraseForAddress(file, 'bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu');
  assert.deepEqual(btc, { phrase: mnemonic, line: 1 });
  const eth = await findPhraseForAddress(file, '0XF39FD6E51AAD88F6F4CE6AB8827279CFFFB92266');
  assert.deepEqual(eth, { phrase: other, line: 3 });
});

test('does not invent a phrase for an address absent from the file', async () => {
  const file = { text: async () => mnemonic + '\n' };
  assert.equal(await findPhraseForAddress(file, '0x0000000000000000000000000000000000000000'), null);
  await assert.rejects(findPhraseForAddress(file, 'bc1qnot-a-valid-address'), /Enter a BTC/);
  await assert.rejects(findPhraseForAddress(file, 'not-an-address'), /Enter a BTC/);
});
