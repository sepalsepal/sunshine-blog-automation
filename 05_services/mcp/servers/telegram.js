#!/usr/bin/env node
/**
 * Telegram MCP Server - 알림 전송용
 *
 * 환경변수:
 * - TELEGRAM_BOT_TOKEN: 텔레그램 봇 토큰
 * - TELEGRAM_CHAT_ID: 알림 받을 채팅 ID
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import https from 'https';
import fs from 'fs';

const BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const CHAT_ID = process.env.TELEGRAM_CHAT_ID;

class TelegramServer {
  constructor() {
    this.server = new Server(
      {
        name: 'telegram-mcp',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupHandlers();
  }

  setupHandlers() {
    // 도구 목록
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'send_message',
          description: '텔레그램 메시지 전송',
          inputSchema: {
            type: 'object',
            properties: {
              text: {
                type: 'string',
                description: '전송할 메시지 내용',
              },
              parse_mode: {
                type: 'string',
                enum: ['HTML', 'Markdown', 'MarkdownV2'],
                description: '메시지 포맷 (기본: HTML)',
              },
            },
            required: ['text'],
          },
        },
        {
          name: 'send_photo',
          description: '텔레그램 사진 전송',
          inputSchema: {
            type: 'object',
            properties: {
              photo_path: {
                type: 'string',
                description: '전송할 이미지 파일 경로',
              },
              caption: {
                type: 'string',
                description: '이미지 캡션',
              },
            },
            required: ['photo_path'],
          },
        },
        {
          name: 'send_content_complete',
          description: '콘텐츠 생성 완료 알림 전송',
          inputSchema: {
            type: 'object',
            properties: {
              topic_kr: { type: 'string', description: '한글 주제명' },
              topic_en: { type: 'string', description: '영문 주제명' },
              safety: { type: 'string', description: '안전도 (safe/caution/danger)' },
              color: { type: 'string', description: '텍스트 색상 HEX' },
              visual_guard_result: { type: 'string', description: 'PASS/BLOCK/CAUTION' },
              sample_image_path: { type: 'string', description: '샘플 이미지 경로' },
            },
            required: ['topic_kr', 'topic_en', 'safety', 'visual_guard_result'],
          },
        },
      ],
    }));

    // 도구 실행
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      switch (name) {
        case 'send_message':
          return await this.sendMessage(args.text, args.parse_mode || 'HTML');

        case 'send_photo':
          return await this.sendPhoto(args.photo_path, args.caption);

        case 'send_content_complete':
          return await this.sendContentComplete(args);

        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    });
  }

  async sendMessage(text, parseMode = 'HTML') {
    return new Promise((resolve, reject) => {
      const data = JSON.stringify({
        chat_id: CHAT_ID,
        text: text,
        parse_mode: parseMode,
      });

      const options = {
        hostname: 'api.telegram.org',
        port: 443,
        path: `/bot${BOT_TOKEN}/sendMessage`,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(data),
        },
      };

      const req = https.request(options, (res) => {
        let body = '';
        res.on('data', (chunk) => (body += chunk));
        res.on('end', () => {
          const result = JSON.parse(body);
          if (result.ok) {
            resolve({
              content: [{ type: 'text', text: `메시지 전송 성공: message_id=${result.result.message_id}` }],
            });
          } else {
            reject(new Error(`Telegram API 오류: ${result.description}`));
          }
        });
      });

      req.on('error', reject);
      req.write(data);
      req.end();
    });
  }

  async sendPhoto(photoPath, caption) {
    // 간단한 구현 - 실제로는 multipart/form-data 필요
    const message = caption ? `[이미지] ${caption}\n경로: ${photoPath}` : `[이미지] ${photoPath}`;
    return this.sendMessage(message);
  }

  async sendContentComplete(args) {
    const safetyEmoji = {
      safe: '🟢',
      caution: '🟡',
      danger: '🔴',
    };

    const resultEmoji = {
      PASS: '✅',
      BLOCK: '❌',
      CAUTION: '⚠️',
    };

    const message = `
${resultEmoji[args.visual_guard_result] || '❓'} <b>콘텐츠 생성 완료</b>

📦 <b>${args.topic_kr}</b> (${args.topic_en})
🏷️ 안전도: ${safetyEmoji[args.safety] || '❓'} ${args.safety?.toUpperCase()}
🎨 텍스트 색상: ${args.color || 'N/A'}
🛡️ visual_guard: ${args.visual_guard_result}

📊 시트 업데이트: 대기 중
${args.sample_image_path ? `\n🔗 샘플: ${args.sample_image_path}` : ''}
    `.trim();

    return this.sendMessage(message, 'HTML');
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Telegram MCP Server running');
  }
}

const server = new TelegramServer();
server.run().catch(console.error);
