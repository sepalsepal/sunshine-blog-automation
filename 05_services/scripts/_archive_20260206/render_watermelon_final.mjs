/**
 * 수박 텍스트 오버레이 - 브로콜리 스펙 100% 동일 적용
 * 기준: text_overlay_spec_v1.md (브로콜리 코드 스펙)
 */

import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const ROOT = path.join(__dirname, '..');
const INPUT_DIR = path.join(ROOT, 'outputs', 'watermelon_final');
const OUTPUT_DIR = path.join(ROOT, 'outputs', 'watermelon_publish_final');

// 출력 디렉토리 생성
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

// 슬라이드 정보
const slides = [
  { idx: 0, type: 'cover', title: 'WATERMELON', subtitle: null },
  { idx: 1, type: 'result', title: '수박, 먹어도 돼요!', subtitle: '안전하게 급여 가능해요' },
  { idx: 2, type: 'benefit1', title: '수분 보충', subtitle: '92% 수분 함량, 여름철 탈수 예방' },
  { idx: 3, type: 'benefit2', title: '비타민 풍부', subtitle: '비타민 A, C가 면역력 강화' },
  { idx: 4, type: 'caution', title: '주의하세요!', subtitle: '씨와 껍질은 반드시 제거' },
  { idx: 5, type: 'amount', title: '적정량', subtitle: '체중 1kg당 10~20g' },
  { idx: 6, type: 'cta', title: '저장해두세요!', subtitle: '우리 아이 건강 간식 🍉' },
];

async function renderSlide(browser, slide) {
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1080 });

  // 입력 이미지 경로 결정
  let inputFile;
  if (slide.idx === 0) {
    inputFile = path.join(INPUT_DIR, `watermelon_${String(slide.idx).padStart(2, '0')}_cover.png`);
  } else if (slide.idx === 6) {
    inputFile = path.join(INPUT_DIR, `watermelon_${String(slide.idx).padStart(2, '0')}_cta.png`);
  } else {
    inputFile = path.join(INPUT_DIR, `watermelon_${String(slide.idx).padStart(2, '0')}_content.png`);
  }

  // 이미지를 base64로 인코딩
  const imageData = fs.readFileSync(inputFile);
  const base64Image = imageData.toString('base64');
  const bgImageUrl = `data:image/png;base64,${base64Image}`;

  // HTML 생성 (브로콜리 overlay.html 스펙 100% 동일)
  const html = `
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap" rel="stylesheet">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      width: 1080px;
      height: 1080px;
      overflow: hidden;
      font-family: 'Noto Sans KR', 'Apple SD Gothic Neo', -apple-system, sans-serif;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }
    .canvas {
      width: 1080px;
      height: 1080px;
      position: relative;
      background: #1a1a2e;
    }
    .background-image {
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      background-image: url('${bgImageUrl}');
      background-size: cover;
      background-position: center;
      background-repeat: no-repeat;
    }

    /* 그라데이션 오버레이 - 하단 50% */
    .gradient-bottom {
      position: absolute;
      bottom: 0; left: 0;
      width: 100%; height: 50%;
      background: linear-gradient(
        to top,
        rgba(0, 0, 0, 0.85) 0%,
        rgba(0, 0, 0, 0.6) 30%,
        rgba(0, 0, 0, 0.3) 60%,
        rgba(0, 0, 0, 0) 100%
      );
    }

    /* 텍스트 컨테이너 */
    .text-container {
      position: absolute;
      left: 0;
      width: 100%;
      text-align: center;
      padding: 0 60px;
      z-index: 10;
    }

    /* cover: top 120px */
    .layout-cover-top .text-container {
      top: 120px;
    }

    /* content/cta: bottom 120px */
    .layout-bottom .text-container {
      bottom: 120px;
    }

    /* ============================================
       들어올리기 효과 (Lift) - 프리미엄 버전
       ============================================ */
    .lift-effect {
      text-shadow:
        0 1px 0 rgba(0,0,0,0.15),
        0 2px 0 rgba(0,0,0,0.13),
        0 3px 0 rgba(0,0,0,0.11),
        0 4px 0 rgba(0,0,0,0.09),
        0 5px 0 rgba(0,0,0,0.07),
        0 0 1px rgba(255,255,255,0.1),
        0 5px 10px rgba(0,0,0,0.25),
        0 8px 15px rgba(0,0,0,0.2),
        0 15px 30px rgba(0,0,0,0.25),
        0 25px 50px rgba(0,0,0,0.15);
    }

    .lift-light {
      text-shadow:
        0 1px 2px rgba(0,0,0,0.3),
        0 4px 8px rgba(0,0,0,0.2),
        0 8px 16px rgba(0,0,0,0.1);
    }

    /* ============================================
       COVER 스타일: 58px, 800, 언더라인 180px×3px
       ============================================ */
    .style-cover .title {
      font-family: 'Noto Sans KR', sans-serif;
      font-size: 58px;
      font-weight: 800;
      color: #FFFFFF;
      letter-spacing: 1px;
      text-transform: uppercase;
      text-shadow: 0 3px 20px rgba(0,0,0,0.5);
      margin-bottom: 0;
    }

    .style-cover .underline {
      width: 180px;
      height: 3px;
      background: #FFFFFF;
      margin: 0 auto;
      margin-top: 12px;
      border-radius: 2px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }

    /* ============================================
       CONTENT 스타일: 72px/900, 36px/500
       ============================================ */
    .style-content .title {
      font-family: 'Noto Sans KR', sans-serif;
      font-size: 72px;
      font-weight: 900;
      line-height: 1.2;
      color: #FFFFFF;
      letter-spacing: -0.02em;
      margin-bottom: 24px;
    }

    .style-content .subtitle {
      font-family: 'Noto Sans KR', sans-serif;
      font-size: 36px;
      font-weight: 500;
      line-height: 1.4;
      color: rgba(255, 255, 255, 0.95);
      letter-spacing: -0.01em;
    }

    /* ============================================
       CTA 스타일: 64px/900/#E53935, 40px/500
       ============================================ */
    .style-cta .title {
      font-family: 'Noto Sans KR', sans-serif;
      font-size: 64px;
      font-weight: 900;
      line-height: 1.2;
      color: #E53935;
      letter-spacing: -0.02em;
      margin-bottom: 24px;
    }

    .style-cta .subtitle {
      font-family: 'Noto Sans KR', sans-serif;
      font-size: 40px;
      font-weight: 500;
      line-height: 1.4;
      color: rgba(255, 255, 255, 0.95);
      letter-spacing: -0.01em;
    }

    /* 이모지 스타일링 */
    .emoji {
      font-family: "Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", sans-serif;
    }
  </style>
</head>
<body>
  <div class="canvas ${slide.type === 'cover' ? 'layout-cover-top style-cover' : 'layout-bottom'} ${slide.type === 'cta' ? 'style-cta' : ''} ${slide.type !== 'cover' && slide.type !== 'cta' ? 'style-content' : ''}" id="canvas">
    <div class="background-image"></div>
    ${slide.type !== 'cover' ? '<div class="gradient-bottom"></div>' : ''}
    <div class="text-container">
      <div class="title ${slide.type !== 'cover' ? 'lift-effect' : ''}">${slide.title}</div>
      ${slide.type === 'cover' ? '<div class="underline"></div>' : ''}
      ${slide.subtitle ? `<div class="subtitle lift-light">${slide.subtitle}</div>` : ''}
    </div>
  </div>
</body>
</html>`;

  await page.setContent(html, { waitUntil: 'networkidle0' });

  // 폰트 로딩 대기
  await page.waitForFunction(() => document.fonts.ready);
  await new Promise(r => setTimeout(r, 500));

  // 스크린샷
  const outputFile = path.join(OUTPUT_DIR, `watermelon_${String(slide.idx).padStart(2, '0')}_${slide.type}.png`);
  await page.screenshot({ path: outputFile, type: 'png' });

  console.log(`✓ ${path.basename(outputFile)}: ${slide.title}`);
  await page.close();
}

async function main() {
  console.log('🚀 Puppeteer 브라우저 시작...');
  console.log('📋 브로콜리 스펙 적용:');
  console.log('   cover: 58px/800, top:120px, 언더라인 180px×3px');
  console.log('   content: 72px/900 + 36px/500, bottom:120px');
  console.log('   cta: 64px/900/#E53935 + 40px/500, bottom:120px');
  console.log('');

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--font-render-hinting=none']
  });

  try {
    for (const slide of slides) {
      await renderSlide(browser, slide);
    }
    console.log(`\n📁 ${slides.length}개 파일 저장됨: ${OUTPUT_DIR}`);
    console.log('✅ 브로콜리 스펙 100% 적용 완료');
  } finally {
    await browser.close();
  }
}

main().catch(console.error);
