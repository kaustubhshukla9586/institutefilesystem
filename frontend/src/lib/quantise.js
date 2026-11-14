// Anti-leak rule (from the Lacuna frontend): a cut-out's width comes from a hash of the token id,
// never from the hidden text, so bar length can't reveal how long a name is.
export const INLINE_CH = [4, 7, 11];

/** FNV-1a 32-bit */
export function hashId(id) {
  let h = 0x811c9dc5;
  for (let i = 0; i < id.length; i++) {
    h ^= id.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}

export const quantiseInlineCh = (tokenId) => INLINE_CH[hashId(tokenId) % 3];
