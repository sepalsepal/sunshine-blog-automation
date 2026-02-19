/**
 * 수박 텍스트 오버레이 - 브로콜리 스타일 100% 동일
 */

import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const ROOT = path.join(__dirname, '..');
const INPUT_DIR = path.join(ROOT, 'outputs', 'watermelon_final');
const OUTPUT_DIR = path.join(ROOT, 'outputs', 'watermelon_publish_v4');

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

  // 스타일 결정
  let layoutClass, styleClass, showGradient, showUnderline, titleColor, subtitleColor;

  if (slide.type === 'cover') {
    layoutClass = 'layout-cover-top';
    styleClass = 'style-cover';
    showGradient = false;
    showUnderline = true;
    titleColor = '#FFFFFF';
    subtitleColor = 'rgba(255,255,255,0.95)';
  } else if (slide.type === 'cta') {
    layoutClass = 'layout-center';
    styleClass = 'style-cta';
    showGradient = false;
    showUnderline = false;
    titleColor = '#E53935';  // 수박 빨간색
    subtitleColor = 'rgba(80,80,80,0.95)';
  } else {
    layoutClass = 'layout-bottom';
    styleClass = 'content';
    showGradient = true;
    showUnderline = false;
    titleColor = '#FFFFFF';
    subtitleColor = 'rgba(255,255,255,0.95)';
  }

  // HTML 생성 (브로콜리 템플릿 기반)
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
      font-family: 'Noto Sans KR', sans-serif;
      -webkit-font-smoothing: antialiased;
    }
    .canvas {
      width: 1080px;
      height: 1080px;
      position: relative;
    }
    .background-image {
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
      background-image: url('${bgImageUrl}');
      background-size: cover;
      background-position: center;
    }
    .gradient-bottom {
      position: absolute;
      bottom: 0; left: 0;
      width: 100%; height: 50%;
      background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.6) 30%, rgba(0,0,0,0.3) 60%, rgba(0,0,0,0) 100%);
      display: ${showGradient ? 'block' : 'none'};
    }
    .text-container {
      position: absolute;
      left: 0; width: 100%;
      text-align: center;
      padding: 0 60px;
      z-index: 10;
    }
    .layout-cover-top .text-container { top: 120px; }
    .layout-bottom .text-container { bottom: 120px; }
    .layout-center .text-container { top: 50%; transform: translateY(-50%); }

    .title {
      font-weight: 900;
      font-size: 72px;
      color: ${titleColor};
      margin-bottom: 16px;
      text-shadow: 0 1px 0 rgba(0,0,0,0.15), 0 2px 0 rgba(0,0,0,0.13), 0 3px 0 rgba(0,0,0,0.11),
                   0 4px 0 rgba(0,0,0,0.09), 0 5px 0 rgba(0,0,0,0.07), 0 0 1px rgba(255,255,255,0.1),
                   0 5px 10px rgba(0,0,0,0.25), 0 8px 15px rgba(0,0,0,0.2),
                   0 15px 30px rgba(0,0,0,0.25), 0 25px 50px rgba(0,0,0,0.15);
    }
    .style-cover .title {
      font-size: 58px;
      font-weight: 800;
      letter-spacing: 1px;
      text-transform: uppercase;
      text-shadow: 0 3px 20px rgba(0,0,0,0.5);
    }
    .style-cta .title {
      font-size: 64px;
    }
    .underline {
      width: 200px;
      height: 3px;
      background: #FFFFFF;
      margin: 0 auto;
      margin-top: 12px;
      border-radius: 2px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.3);
      display: ${showUnderline ? 'block' : 'none'};
    }
    .subtitle {
      font-weight: 500;
      font-size: 36px;
      color: ${subtitleColor};
      margin-top: 16px;
      text-shadow: 0 1px 2px rgba(0,0,0,0.3), 0 4px 8px rgba(0,0,0,0.2);
    }
    .style-cta .subtitle {
      font-size: 40px;
    }
  </style>
</head>
<body>
  <div class="canvas ${layoutClass} ${styleClass}">
    <div class="background-image"></div>
    <div class="gradient-bottom"></div>
    <div class="text-container">
      <div class="title">${slide.title}</div>
      <div class="underline"></div>
      ${slide.subtitle ? `<div class="subtitle">${slide.subtitle}</div>` : ''}
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
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--font-render-hinting=none']
  });

  try {
    for (const slide of slides) {
      await renderSlide(browser, slide);
    }
    console.log(`\n📁 ${slides.length}개 파일 저장됨: ${OUTPUT_DIR}`);
    console.log('✅ 브로콜리 스타일 렌더링 완료');
  } finally {
    await browser.close();
  }
}

main().catch(console.error);
