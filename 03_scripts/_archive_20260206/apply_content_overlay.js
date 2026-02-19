#!/usr/bin/env node
/**
 * 본문 슬라이드 텍스트 오버레이 (템플릿 기반)
 *
 * text_guide.pptx 템플릿 기준:
 * - 캔버스: 512x512pt → 1080x1080px
 * - 하단 그라데이션 오버레이
 * - 제목: 하단 영역 상단
 * - 부제목: 제목 아래
 *
 * Author: 박편집
 */

import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';

// ============================================
// 템플릿 스타일 설정 (text_guide.pptx 기준)
// ============================================

const CONTENT_STYLE = {
  // 하단 그라데이션 오버레이 영역
  overlay: {
    startY: 72,  // 상단에서 72% 위치부터 시작
    height: 28,  // 28% 높이
    gradient: 'linear-gradient(to bottom, transparent 0%, rgba(0,0,0,0.3) 30%, rgba(0,0,0,0.85) 100%)'
  },
  // 제목 스타일
  title: {
    fontFamily: "'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif",
    fontWeight: 800,
    fontSize: 52,
    color: '#FFFFFF',
    textShadow: '0 2px 8px rgba(0, 0, 0, 0.8)',
    topPercent: 77,  // 상단에서 77%
  },
  // 부제목 스타일
  subtitle: {
    fontFamily: "'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif",
    fontWeight: 500,
    fontSize: 24,
    color: '#FFFFFF',
    textShadow: '0 1px 4px rgba(0, 0, 0, 0.6)',
    topPercent: 87,  // 상단에서 87%
  }
};

// ============================================
// HTML 생성
// ============================================

function generateHTML(imageSrc, title, subtitle) {
  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css" rel="stylesheet">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@500;800&display=swap');

    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      width: 1080px;
      height: 1080px;
      font-family: 'Noto Sans KR', 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif;
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
    .gradient-overlay {
      position: absolute;
      left: 0;
      top: ${CONTENT_STYLE.overlay.startY}%;
      width: 100%;
      height: ${CONTENT_STYLE.overlay.height}%;
      background: ${CONTENT_STYLE.overlay.gradient};
      z-index: 5;
    }
    .text-container {
      position: absolute;
      width: 100%;
      text-align: center;
      z-index: 10;
    }
    .title {
      position: absolute;
      width: 100%;
      top: ${CONTENT_STYLE.title.topPercent}%;
      left: 0;
      font-size: ${CONTENT_STYLE.title.fontSize}px;
      font-weight: ${CONTENT_STYLE.title.fontWeight};
      color: ${CONTENT_STYLE.title.color};
      text-shadow: ${CONTENT_STYLE.title.textShadow};
      text-align: center;
      padding: 0 40px;
    }
    .subtitle {
      position: absolute;
      width: 100%;
      top: ${CONTENT_STYLE.subtitle.topPercent}%;
      left: 0;
      font-size: ${CONTENT_STYLE.subtitle.fontSize}px;
      font-weight: ${CONTENT_STYLE.subtitle.fontWeight};
      color: ${CONTENT_STYLE.subtitle.color};
      text-shadow: ${CONTENT_STYLE.subtitle.textShadow};
      text-align: center;
      padding: 0 60px;
      line-height: 1.4;
    }
  </style>
</head>
<body>
  <div class="full-image"><img src="${imageSrc}" alt=""></div>
  <div class="gradient-overlay"></div>
  <div class="title">${title}</div>
  <div class="subtitle">${subtitle}</div>
</body>
</html>`;
}

// ============================================
// 메인 함수
// ============================================

async function main() {
  const args = process.argv.slice(2);

  if (args.length < 4) {
    console.error('Usage: node apply_content_overlay.js <input_image> <title> <subtitle> <output_path>');
    process.exit(1);
  }

  const [inputPath, title, subtitle, outputPath] = args;

  if (!fs.existsSync(inputPath)) {
    console.error(`Error: Input file not found: ${inputPath}`);
    process.exit(1);
  }

  console.log(`📝 본문 오버레이: ${title}`);

  // 이미지를 Base64로 변환
  const imageBuffer = fs.readFileSync(inputPath);
  const imageBase64 = imageBuffer.toString('base64');
  const ext = path.extname(inputPath).toLowerCase();
  const mimeType = ext === '.jpg' || ext === '.jpeg' ? 'image/jpeg' : 'image/png';
  const imageSrc = `data:${mimeType};base64,${imageBase64}`;

  // HTML 생성
  const html = generateHTML(imageSrc, title, subtitle);

  // Puppeteer로 렌더링
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1080 });
  await page.setContent(html, { waitUntil: 'networkidle0' });

  // 폰트 로딩 대기
  await page.evaluateHandle('document.fonts.ready');
  await new Promise(resolve => setTimeout(resolve, 500));

  // 스크린샷 저장
  await page.screenshot({ path: outputPath, type: 'png' });

  await page.close();
  await browser.close();

  console.log(`✅ 완료: ${path.basename(outputPath)}`);
}

main().catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});
