import type { Env, BlacklistItem } from '../types/index.js';
import { DatabaseService } from './database.js';
import { decrypt } from './crypto.js';
import puppeteer from '@cloudflare/puppeteer';
import * as XLSX from 'xlsx';

interface RegtechCredentials {
  username: string;
  password: string;
  baseUrl: string;
}

interface CollectionResult {
  success: boolean;
  itemsCollected: number;
  error?: string;
  duration: number;
}

const REGTECH_BASE_URL = 'https://regtech.fsec.or.kr';

export class RegtechCollector {
  private db: DatabaseService;
  private masterKey: string;
  private env: Env;

  constructor(env: Env) {
    this.db = new DatabaseService(env.DB);
    this.masterKey = env.CREDENTIAL_MASTER_KEY;
    this.env = env;
  }

  async collect(): Promise<CollectionResult> {
    const startTime = Date.now();

    try {
      const credentials = await this.getCredentials();
      if (!credentials) {
        return {
          success: false,
          itemsCollected: 0,
          error: 'REGTECH credentials not configured',
          duration: Date.now() - startTime,
        };
      }

      // Launch browser using CF Browser Rendering
      const browser = await puppeteer.launch(this.env.BROWSER);
      
      try {
        const page = await browser.newPage();
        
        // Set viewport and user agent
        await page.setViewport({ width: 1920, height: 1080 });
        await page.setUserAgent(
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        );

        // Navigate to login page
        console.log('Navigating to REGTECH portal...');
        await page.goto(`${credentials.baseUrl}/login`, {
          waitUntil: 'networkidle0',
          timeout: 30000,
        });

        // Debug: Capture page info
        const pageUrl = page.url();
        const pageTitle = await page.title();
        const bodyText = await page.evaluate(`document.body?.innerText?.substring(0, 500) || 'No body'`);
        console.log(`DEBUG - URL: ${pageUrl}, Title: ${pageTitle}`);
        console.log(`DEBUG - Body preview: ${bodyText}`);

        // Try multiple selectors for login form
        const loginSelectors = [
          'input[name="userId"]',
          '#userId', 
          'input[type="text"][name*="id"]',
          'input[type="text"][placeholder*="아이디"]',
          'input.form-control',
          'input[type="text"]'
        ];
        
        let foundSelector = null;
        for (const selector of loginSelectors) {
          try {
            await page.waitForSelector(selector, { timeout: 3000 });
            foundSelector = selector;
            console.log(`Found login input with selector: ${selector}`);
            break;
          } catch {
            console.log(`Selector not found: ${selector}`);
          }
        }
        
        if (!foundSelector) {
          // Capture available inputs for debugging
          const inputs = await page.evaluate(`
            Array.from(document.querySelectorAll('input')).map(i => ({
              type: i.type,
              name: i.name,
              id: i.id,
              placeholder: i.placeholder,
              className: i.className
            })).slice(0, 10)
          `);
          const bodyPreview = await page.evaluate(`document.body?.innerText?.substring(0, 300) || 'Empty'`);
          throw new Error(`No login input. URL: ${pageUrl}, Title: ${pageTitle}, Body: ${bodyPreview}, Inputs: ${JSON.stringify(inputs)}`);
        }

        // Fill login form using found selector
        console.log('Filling login form...');
        await page.type(foundSelector, credentials.username);
        
        // Find password field
        const pwSelectors = ['input[name="userPw"]', '#userPw', 'input[type="password"]'];
        for (const pwSel of pwSelectors) {
          try {
            await page.type(pwSel, credentials.password);
            console.log(`Password entered with selector: ${pwSel}`);
            break;
          } catch {
            continue;
          }
        }

        // Click login button
        await Promise.all([
          page.waitForNavigation({ waitUntil: 'networkidle0', timeout: 30000 }),
          page.click('button[type="submit"], input[type="submit"], .login-btn, #loginBtn'),
        ]);

        // Check if login succeeded (verify we're not still on login page)
        const currentUrl = page.url();
        if (currentUrl.includes('/login')) {
          const errorText = await page.evaluate(`
            (() => {
              const errorEl = document.querySelector('.error, .alert-danger, .login-error');
              return errorEl?.textContent?.trim() || 'Unknown login error';
            })()
          `);
          throw new Error(`Login failed: ${errorText}`);
        }

        console.log('Login successful, navigating to blacklist page...');

        // Navigate to security advisory / blacklist page
        await page.goto(`${credentials.baseUrl}/fcti/securityAdvisory/advisoryList`, {
          waitUntil: 'networkidle0',
          timeout: 30000,
        });

        // Set date range for last 3 months
        const endDate = new Date();
        const startDate = new Date();
        startDate.setMonth(startDate.getMonth() - 3);

        const startDateStr = this.formatDate(startDate);
        const endDateStr = this.formatDate(endDate);

        // Fill date range if fields exist
        try {
          await page.evaluate(`
            (() => {
              const startInput = document.querySelector('input[name="startDate"], #startDate');
              const endInput = document.querySelector('input[name="endDate"], #endDate');
              if (startInput) startInput.value = '${startDateStr}';
              if (endInput) endInput.value = '${endDateStr}';
            })()
          `);
        } catch {
          console.log('Date fields not found, proceeding with default range');
        }

        // Select blacklist tab if exists
        try {
          await page.click('[data-tab="blacklist"], .blacklist-tab, #blacklistTab');
          await new Promise(resolve => setTimeout(resolve, 1000));
        } catch {
          console.log('Blacklist tab not found, proceeding');
        }

        // Download Excel - intercept the download
        console.log('Initiating Excel download...');
        
        // Enable request interception for download
        const downloadPromise = new Promise<ArrayBuffer>((resolve, reject) => {
          const timeout = setTimeout(() => reject(new Error('Download timeout')), 60000);
          
          page.on('response', async (response) => {
            const headers = response.headers();
            const contentType = headers['content-type'] || '';
            
            if (
              contentType.includes('spreadsheet') ||
              contentType.includes('excel') ||
              contentType.includes('octet-stream')
            ) {
              clearTimeout(timeout);
              try {
                const buffer = await response.buffer();
                resolve(buffer.buffer as ArrayBuffer);
              } catch (e) {
                reject(e);
              }
            }
          });
        });

        // Click download button
        await page.click(
          'button.excel-download, .download-excel, [data-action="excelDownload"], #excelDownBtn, a[href*="xlsx"], button:has-text("엑셀")'
        ).catch(() => {
          // Try form submission approach
          return page.evaluate(`
            (() => {
              const form = document.querySelector('form[action*="Download"]');
              if (form) form.submit();
            })()
          `);
        });

        // Wait for download
        const excelBuffer = await downloadPromise;
        console.log(`Downloaded ${excelBuffer.byteLength} bytes`);

        // Parse Excel
        const items = this.parseExcel(excelBuffer);

        if (items.length === 0) {
          return {
            success: true,
            itemsCollected: 0,
            error: 'No data in Excel file',
            duration: Date.now() - startTime,
          };
        }

        // Save to database
        const savedCount = await this.saveToDatabase(items);

        return {
          success: true,
          itemsCollected: savedCount,
          duration: Date.now() - startTime,
        };
      } finally {
        await browser.close();
      }
    } catch (error) {
      console.error('Collection error:', error);
      return {
        success: false,
        itemsCollected: 0,
        error: error instanceof Error ? error.message : 'Unknown error',
        duration: Date.now() - startTime,
      };
    }
  }

  private async getCredentials(): Promise<RegtechCredentials | null> {
    try {
      const result = await this.db.queryOne<{
        username: string;
        password: string;
        encrypted: number;
        config: string;
      }>(
        `SELECT username, password, encrypted, config 
         FROM collection_credentials 
         WHERE service_name = 'REGTECH' AND is_active = 1`
      );

      if (!result || !result.username || !result.password) return null;

      const config = JSON.parse(result.config || '{}');
      const password = result.encrypted 
        ? await decrypt(result.password, this.masterKey)
        : result.password;

      return {
        username: result.username,
        password,
        baseUrl: config.baseUrl || REGTECH_BASE_URL,
      };
    } catch (error) {
      console.error('Failed to get credentials:', error);
      return null;
    }
  }

  private parseExcel(buffer: ArrayBuffer): BlacklistItem[] {
    const data = new Uint8Array(buffer);
    const workbook = XLSX.read(data, { type: 'array' });
    const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
    const rows = XLSX.utils.sheet_to_json<Record<string, unknown>>(firstSheet);

    const items: BlacklistItem[] = [];

    for (const row of rows) {
      const ipColumn = this.findColumn(row, ['ip', 'addr', 'IP주소', 'IP']);
      const ipValue = String(row[ipColumn] || '').trim();

      if (!this.isValidIP(ipValue)) continue;

      const countryCol = this.findColumn(row, ['국가', 'country', 'Country']);
      const reasonCol = this.findColumn(row, ['사유', 'reason', 'Reason', '이유']);
      const detectCol = this.findColumn(row, ['탐지', '등록', 'detect', 'Detection']);
      const removeCol = this.findColumn(row, ['해제', '삭제', 'remove', 'Removal']);

      const removalDate = this.parseDate(String(row[removeCol] || ''));
      let isActive = 1;
      if (removalDate) {
        const today = new Date().toISOString().split('T')[0];
        if (removalDate < today) {
          isActive = 0;
        }
      }

      items.push({
        ip_address: ipValue,
        source: 'REGTECH',
        category: 'threat_intel',
        country: this.normalizeCountry(String(row[countryCol] || '')),
        reason: String(row[reasonCol] || 'REGTECH Excel Import'),
        confidence_level: 85,
        detection_count: 1,
        is_active: isActive,
        detection_date: this.parseDate(String(row[detectCol] || '')),
        removal_date: removalDate,
        raw_data: JSON.stringify({ excel_import: true, source_row: row }),
      });
    }

    console.log(`Parsed ${items.length} IPs from Excel`);
    return items;
  }

  private findColumn(row: Record<string, unknown>, patterns: string[]): string {
    const keys = Object.keys(row);
    for (const pattern of patterns) {
      const lowerPattern = pattern.toLowerCase();
      const match = keys.find((k) => k.toLowerCase().includes(lowerPattern));
      if (match) return match;
    }
    return keys[0] || '';
  }

  private isValidIP(ip: string): boolean {
    const ipv4Regex = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (!ipv4Regex.test(ip)) return false;

    const parts = ip.split('.').map(Number);
    if (parts.some((p) => p > 255)) return false;

    if (parts[0] === 10) return false;
    if (parts[0] === 172 && parts[1] >= 16 && parts[1] <= 31) return false;
    if (parts[0] === 192 && parts[1] === 168) return false;
    if (parts[0] === 127) return false;
    if (parts[0] === 0) return false;

    return true;
  }

  private normalizeCountry(value: string): string {
    const v = value.toUpperCase().trim();
    const mapping: Record<string, string> = {
      KOREA: 'KR', '한국': 'KR', 'SOUTH KOREA': 'KR',
      USA: 'US', 'UNITED STATES': 'US', '미국': 'US',
      CHINA: 'CN', '중국': 'CN', CHN: 'CN',
      JAPAN: 'JP', '일본': 'JP', JPN: 'JP',
      RUSSIA: 'RU', '러시아': 'RU',
    };
    return mapping[v] || (v.length === 2 ? v : v.substring(0, 2));
  }

  private parseDate(dateStr: string): string | null {
    if (!dateStr) return null;

    const formats = [
      /^(\d{4})-(\d{2})-(\d{2})/,
      /^(\d{4})\/(\d{2})\/(\d{2})/,
      /^(\d{4})\.(\d{2})\.(\d{2})/,
    ];

    for (const regex of formats) {
      const match = dateStr.match(regex);
      if (match) {
        return `${match[1]}-${match[2]}-${match[3]}`;
      }
    }

    return null;
  }

  private formatDate(date: Date): string {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  }

  private async saveToDatabase(items: BlacklistItem[]): Promise<number> {
    const BATCH_SIZE = 100;
    let totalSaved = 0;

    for (let i = 0; i < items.length; i += BATCH_SIZE) {
      const batch = items.slice(i, i + BATCH_SIZE);

      for (const item of batch) {
        try {
          await this.db.execute(
            `INSERT INTO blacklist_ips (
               ip_address, source, category, country, reason,
               confidence_level, detection_count, is_active,
               detection_date, removal_date, last_seen, raw_data
             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
             ON CONFLICT(ip_address) DO UPDATE SET
               detection_count = detection_count + 1,
               last_seen = datetime('now'),
               updated_at = datetime('now'),
               removal_date = COALESCE(excluded.removal_date, blacklist_ips.removal_date),
               is_active = CASE 
                 WHEN COALESCE(excluded.removal_date, blacklist_ips.removal_date) < date('now') THEN 0 
                 ELSE excluded.is_active 
               END`,
            [
              item.ip_address,
              item.source,
              item.category,
              item.country,
              item.reason,
              item.confidence_level,
              item.detection_count,
              item.is_active,
              item.detection_date,
              item.removal_date,
              item.raw_data,
            ]
          );
          totalSaved++;
        } catch (error) {
          console.error(`Failed to save ${item.ip_address}:`, error);
        }
      }
    }

    console.log(`Saved ${totalSaved} IPs to database`);
    return totalSaved;
  }
}
