#!/usr/bin/env node
/**
 * 단일 표지 이미지에 텍스트 오버레이 적용
 *
 * 사용법: node apply_single_cover_overlay.js <input_image> <title> <output_path>
 * 예시: node apply_single_cover_overlay.js raw.png "STRAWBERRY" final.png
 *
 * Author: 최기술 대리
 */

import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';

// ============================================
// 스타일 설정 (v8.3 기준)
// ============================================

const TITLE_STYLE = {
  fontFamily: "'Arial Black', 'Noto Sans KR', sans-serif",  // text_guide.pptx 기준
  fontWeight: 900,
  color: '#FFFFFF',
  textShadow: '0 4px 12px rgba(0, 0, 0, 0.7)',
  letterSpacing: '0.02em',
  topPercent: 13, // text_guide.pptx 기준: 68/512 = 13%
};

// 언더라인 제거 (2026-01-28 PD 지시)
const UNDERLINE_STYLE = {
  enabled: false,  // 언더라인 비활성화
  height: 4,
  color: '#FFFFFF',
  borderRadius: 2,
  marginTop: 10,
  widthRatio: 1.0,
};

// ============================================
// 폰트 크기 계산
// ============================================

function calculateFontSize(text) {
  const charCount = text.length;
  const sizeMap = {
    4: 160,
    5: 150,
    6: 140,
    7: 130,
    8: 120,
    9: 110,
    10: 100,
  };

  if (charCount <= 4) return sizeMap[4];
  if (charCount >= 10) return sizeMap[10];
  return sizeMap[charCount] || 140;
}

function calculateUnderlineWidth(text, fontSize) {
  const estimatedTextWidth = fontSize * 0.6 * text.length;
  return estimatedTextWidth * UNDERLINE_STYLE.widthRatio;
}

// ============================================
// HTML 생성
// ============================================

function generateHTML(imageSrc, title) {
  const fontSize = calculateFontSize(title);
  const underlineWidth = calculateUnderlineWidth(title, fontSize);

  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css" rel="stylesheet">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      width: 1080px;
      height: 1080px;
      font-family: ${TITLE_STYLE.fontFamily};
      position: relative;
      overflow: hidden;
    }
    .full-image {
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
    }
    .full-image img {
      width: 100%; height: 100%;
      object-fit: cover;
    }
    .title-container {
      position: absolute;
      top: ${TITLE_STYLE.topPercent}%;
      left: 50%;
      transform: translateX(-50%);
      display: flex;
      flex-direction: column;
      align-items: center;
      z-index: 10;
    }
    .title {
      font-size: ${fontSize}px;
      font-weight: ${TITLE_STYLE.fontWeight};
      color: ${TITLE_STYLE.color};
      text-shadow: ${TITLE_STYLE.textShadow};
      letter-spacing: ${TITLE_STYLE.letterSpacing};
      white-space: nowrap;
    }
    .underline {
      width: ${underlineWidth}px;
      height: ${UNDERLINE_STYLE.height}px;
      background: ${UNDERLINE_STYLE.color};
      margin-top: ${UNDERLINE_STYLE.marginTop}px;
      border-radius: ${UNDERLINE_STYLE.borderRadius}px;
    }
  </style>
</head>
<body>
  <div class="full-image"><img src="${imageSrc}" alt=""></div>
  <div class="title-container">
    <div class="title">${title}</div>
    ${UNDERLINE_STYLE.enabled ? '<div class="underline"></div>' : ''}
  </div>
</body>
</html>`;
}

// ============================================
// 메인 함수
// ============================================

async function main() {
  const args = process.argv.slice(2);

  if (args.length < 3) {
    console.error('Usage: node apply_single_cover_overlay.js <input_image> <title> <output_path>');
    process.exit(1);
  }

  const [inputPath, title, outputPath] = args;

  if (!fs.existsSync(inputPath)) {
    console.error(`Error: Input file not found: ${inputPath}`);
    process.exit(1);
  }

  console.log(`Applying overlay: ${title} -> ${path.basename(outputPath)}`);

  // 이미지를 Base64로 변환
  const imageBuffer = fs.readFileSync(inputPath);
  const imageBase64 = imageBuffer.toString('base64');
  const ext = path.extname(inputPath).toLowerCase();
  const mimeType = ext === '.jpg' || ext === '.jpeg' ? 'image/jpeg' : 'image/png';
  const imageSrc = `data:${mimeType};base64,${imageBase64}`;

  // HTML 생성
  const html = generateHTML(imageSrc, title);

  // Puppeteer로 렌더링
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1080 });
  await page.setContent(html, { waitUntil: 'networkidle0' });
  await page.evaluateHandle('document.fonts.ready');

  // 스크린샷 저장
  await page.screenshot({ path: outputPath, type: 'png' });

  await page.close();
  await browser.close();

  console.log(`Done: ${outputPath}`);
}

main().catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});
