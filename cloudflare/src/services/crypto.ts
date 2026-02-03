/**
 * Crypto Service
 * Web Crypto API wrapper for encryption (Fernet replacement)
 */

// AES-256-GCM parameters
const ALGORITHM = 'AES-GCM';
const KEY_LENGTH = 256;
const IV_LENGTH = 12; // 96 bits for GCM
const TAG_LENGTH = 128; // Authentication tag

/**
 * Derive a CryptoKey from a master key string
 */
async function deriveKey(masterKey: string): Promise<CryptoKey> {
  const encoder = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey(
    'raw',
    encoder.encode(masterKey),
    'PBKDF2',
    false,
    ['deriveKey']
  );

  return crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt: encoder.encode('blacklist-salt'), // Use a proper salt in production
      iterations: 100000,
      hash: 'SHA-256',
    },
    keyMaterial,
    { name: ALGORITHM, length: KEY_LENGTH },
    false,
    ['encrypt', 'decrypt']
  );
}

/**
 * Encrypt plaintext using AES-256-GCM
 * Returns base64-encoded ciphertext with IV prepended
 */
export async function encrypt(plaintext: string, masterKey: string): Promise<string> {
  const key = await deriveKey(masterKey);
  const encoder = new TextEncoder();
  const data = encoder.encode(plaintext);

  // Generate random IV
  const iv = crypto.getRandomValues(new Uint8Array(IV_LENGTH));

  // Encrypt
  const ciphertext = await crypto.subtle.encrypt(
    { name: ALGORITHM, iv, tagLength: TAG_LENGTH },
    key,
    data
  );

  // Combine IV + ciphertext and encode as base64
  const combined = new Uint8Array(iv.length + ciphertext.byteLength);
  combined.set(iv, 0);
  combined.set(new Uint8Array(ciphertext), iv.length);

  return btoa(String.fromCharCode(...combined));
}

/**
 * Decrypt ciphertext using AES-256-GCM
 * Expects base64-encoded data with IV prepended
 */
export async function decrypt(ciphertext: string, masterKey: string): Promise<string> {
  const key = await deriveKey(masterKey);

  // Decode from base64
  const combined = new Uint8Array(
    atob(ciphertext)
      .split('')
      .map((c) => c.charCodeAt(0))
  );

  // Extract IV and ciphertext
  const iv = combined.slice(0, IV_LENGTH);
  const data = combined.slice(IV_LENGTH);

  // Decrypt
  const plaintext = await crypto.subtle.decrypt(
    { name: ALGORITHM, iv, tagLength: TAG_LENGTH },
    key,
    data
  );

  const decoder = new TextDecoder();
  return decoder.decode(plaintext);
}

/**
 * Generate a secure random token
 */
export function generateToken(length: number = 32): string {
  const bytes = crypto.getRandomValues(new Uint8Array(length));
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

/**
 * Hash a value using SHA-256
 */
export async function hash(value: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(value);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
}

/**
 * Constant-time string comparison (timing attack safe)
 */
export function secureCompare(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let result = 0;
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return result === 0;
}
