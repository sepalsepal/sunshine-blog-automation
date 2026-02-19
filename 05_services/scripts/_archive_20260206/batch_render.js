/**
 * 일괄 렌더링 스크립트 - v1.0 규칙 적용
 * 10개 콘텐츠 한번에 렌더링
 */

import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.join(__dirname, '..', '..');
const IMAGES_DIR = path.join(ROOT, 'content', 'images');
const REAL_PHOTO_DIR = path.join(ROOT, 'content', 'images', 'sunshine', '01_usable', 'grade_A', 'expression', 'happy');

// 콘텐츠 정의
const CONTENTS = [
  {
    folder: '029_chicken_닭고기', en: 'chicken', cover: 'CHICKEN',
    slides: [
      { slide: 1, type: 'content', title: '먹어도 돼요!', subtitle: '양질의 단백질 공급원 ✅' },
      { slide: 2, type: 'content', title: '급여 방법', subtitle: '껍질 제거, 익혀서 급여 🍗' },
    ]
  },
  {
    folder: '030_salmon_연어', en: 'salmon', cover: 'SALMON',
    slides: [
      { slide: 1, type: 'content', title: '먹어도 돼요!', subtitle: '오메가-3 풍부한 슈퍼푸드 ✅' },
      { slide: 2, type: 'content', title: '급여 방법', subtitle: '뼈 제거 후 익혀서 급여 🐟' },
    ]
  },
  {
    folder: '031_tofu_두부', en: 'tofu', cover: 'TOFU',
    slides: [
      { slide: 1, type: 'content', title: '먹어도 돼요!', subtitle: '저칼로리 고단백 간식 ✅' },
      { slide: 2, type: 'content', title: '급여 방법', subtitle: '소량씩 천천히 시작 🫘' },
    ]
  },
  {
    folder: '032_boiled_egg_삶은달걀', en: 'boiled_egg', cover: 'BOILED EGG',
    slides: [
      { slide: 1, type: 'content', title: '먹어도 돼요!', subtitle: '완전식품 단백질 ✅' },
      { slide: 2, type: 'content', title: '급여 방법', subtitle: '완숙으로 소량 급여 🥚' },
    ]
  },
  {
    folder: '033_mackerel_고등어', en: 'mackerel', cover: 'MACKEREL',
    slides: [
      { slide: 1, type: 'content', title: '먹어도 돼요!', subtitle: '오메가-3 풍부 ✅' },
      { slide: 2, type: 'content', title: '급여 방법', subtitle: '뼈 제거, 익혀서 급여 🐟' },
    ]
  },
  {
    folder: '034_yogurt_요거트', en: 'yogurt', cover: 'YOGURT',
    slides: [
      { slide: 1, type: 'caution', title: '주의가 필요해요!', subtitle: '무가당 플레인만 OK ⚠️' },
      { slide: 2, type: 'caution', title: '급여 방법', subtitle: '소량씩, 유당불내증 확인 🥛' },
    ]
  },
  {
    folder: '035_tuna_참치', en: 'tuna', cover: 'TUNA',
    slides: [
      { slide: 1, type: 'caution', title: '주의가 필요해요!', subtitle: '수은 함량 주의 ⚠️' },
      { slide: 2, type: 'caution', title: '급여 방법', subtitle: '가끔, 소량만 급여 🐟' },
    ]
  },
  {
    folder: '036_sweet_potato_고구마', en: 'sweet_potato', cover: 'SWEET POTATO',
    slides: [
      { slide: 1, type: 'content', title: '먹어도 돼요!', subtitle: '식이섬유 풍부한 간식 ✅' },
      { slide: 2, type: 'content', title: '급여 방법', subtitle: '익혀서 소량 급여 🍠' },
    ]
  },
  {
    folder: '037_chocolate_초콜릿', en: 'chocolate', cover: 'CHOCOLATE',
    slides: [
      { slide: 1, type: 'danger', title: '절대 안돼요!', subtitle: '테오브로민 중독 위험 ❌' },
      { slide: 2, type: 'danger', title: '섭취 시 증상', subtitle: '구토, 경련, 심장마비 위험 🚨' },
    ]
  },
  {
    folder: '038_cake_케이크', en: 'cake', cover: 'CAKE',
    slides: [
      { slide: 1, type: 'danger', title: '주지 마세요!', subtitle: '설탕/초콜릿 위험 ❌' },
      { slide: 2, type: 'danger', title: '위험 요소', subtitle: '비만, 당뇨, 췌장염 유발 🚨' },
    ]
  },
];

// 스타일 설정
const STYLES = {
  content: { titleColor: '#4CAF50', titleSize: '72px', titleWeight: 900, subtitleColor: '#FFFFFF', subtitleSize: '36px', subtitleWeight: 500 },
  caution: { titleColor: '#FFE066', titleSize: '72px', titleWeight: 900, subtitleColor: '#FFFFFF', subtitleSize: '36px', subtitleWeight: 500 },
  danger: { titleColor: '#FF6B6B', titleSize: '72px', titleWeight: 900, subtitleColor: '#FFFFFF', subtitleSize: '36px', subtitleWeight: 500 },
  cta: { titleColor: '#FFD93D', titleSize: '64px', titleWeight: 900, subtitleColor: '#FFFFFF', subtitleSize: '40px', subtitleWeight: 500 },
  cover: { titleColor: '#FFFFFF', titleSize: '114px', fontFamily: "'Arial Black', Arial, sans-serif", fontWeight: 900 }
};

function generateHTML(imageSrc, slideConfig) {
  const style = STYLES[slideConfig.type] || STYLES.content;
  const isCover = slideConfig.type === 'cover';

  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&display=swap" rel="stylesheet">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      width: 1080px;
      height: 1080px;
      font-family: 'Noto Sans KR', sans-serif;
      position: relative;
      overflow: hidden;
    }
    .bg {
      position: absolute;
      top: 0; left: 0;
      width: 100%; height: 100%;
    }
    .bg img {
      width: 100%; height: 100%;
      object-fit: cover;
    }
    ${!isCover ? `
    .gradient {
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
    ` : ''}
    .text-area {
      position: absolute;
      ${isCover ? 'top: 150px;' : 'bottom: 120px;'}
      left: 0;
      width: 100%;
      text-align: center;
      padding: 0 60px;
      z-index: 10;
    }
    .title {
      font-family: ${isCover ? style.fontFamily : "'Noto Sans KR', sans-serif"};
      font-size: ${style.titleSize};
      font-weight: ${style.fontWeight || 900};
      color: ${style.titleColor};
      text-shadow: 0 3px 15px rgba(0,0,0,0.5);
      margin-bottom: ${isCover ? '0' : '16px'};
      ${isCover ? 'letter-spacing: 4px; text-transform: uppercase;' : ''}
    }
    ${!isCover ? `
    .subtitle {
      font-size: ${style.subtitleSize};
      font-weight: ${style.subtitleWeight || 500};
      color: ${style.subtitleColor};
      text-shadow: 0 2px 8px rgba(0,0,0,0.5);
    }
    ` : ''}
  </style>
</head>
<body>
  <div class="bg"><img src="${imageSrc}" alt=""></div>
  ${!isCover ? '<div class="gradient"></div>' : ''}
  <div class="text-area">
    <div class="title">${slideConfig.title}</div>
    ${!isCover && slideConfig.subtitle ? `<div class="subtitle">${slideConfig.subtitle}</div>` : ''}
  </div>
</body>
</html>`;
}

async function renderSlide(page, contentDir, en, slideConfig) {
  let bgImagePath;

  if (slideConfig.type === 'cover') {
    bgImagePath = path.join(contentDir, `${en}_00_bg.png`);
  } else if (slideConfig.type === 'cta') {
    const photos = fs.readdirSync(REAL_PHOTO_DIR).filter(f => f.endsWith('.jpg') || f.endsWith('.png'));
    const randomPhoto = photos[Math.floor(Math.random() * photos.length)];
    bgImagePath = path.join(REAL_PHOTO_DIR, randomPhoto);
    console.log(`       📸 실사진: ${randomPhoto}`);
  } else {
    bgImagePath = path.join(contentDir, `${en}_0${slideConfig.slide}_bg.png`);
  }

  if (!fs.existsSync(bgImagePath)) {
    console.log(`       ⚠️ 이미지 없음: ${path.basename(bgImagePath)}`);
    return false;
  }

  const imageBuffer = fs.readFileSync(bgImagePath);
  const imageBase64 = imageBuffer.toString('base64');
  const ext = path.extname(bgImagePath).toLowerCase();
  const mimeType = ext === '.jpg' || ext === '.jpeg' ? 'image/jpeg' : 'image/png';
  const imageSrc = `data:${mimeType};base64,${imageBase64}`;

  const html = generateHTML(imageSrc, slideConfig);
  await page.setContent(html, { waitUntil: 'networkidle0' });
  await page.evaluateHandle('document.fonts.ready');
  await new Promise(resolve => setTimeout(resolve, 300));

  const outputPath = path.join(contentDir, `${en}_0${slideConfig.slide}.png`);
  await page.screenshot({
    path: outputPath,
    type: 'png',
    clip: { x: 0, y: 0, width: 1080, height: 1080 }
  });

  console.log(`       ✅ ${en}_0${slideConfig.slide}.png`);
  return true;
}

async function renderContent(browser, content) {
  const contentDir = path.join(IMAGES_DIR, content.folder);
  console.log(`\n   📦 ${content.folder}`);

  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1080, deviceScaleFactor: 1 });

  try {
    // 표지 (00)
    console.log(`     [00] 표지: ${content.cover}`);
    await renderSlide(page, contentDir, content.en, { slide: 0, type: 'cover', title: content.cover, subtitle: '' });

    // 본문 (01, 02)
    for (const slide of content.slides) {
      console.log(`     [0${slide.slide}] ${slide.type}: ${slide.title}`);
      await renderSlide(page, contentDir, content.en, slide);
    }

    // CTA (03)
    console.log(`     [03] CTA`);
    await renderSlide(page, contentDir, content.en, { slide: 3, type: 'cta', title: '저장 & 공유', subtitle: '주변 견주에게 알려주세요! 🐶' });

  } finally {
    await page.close();
  }
}

async function main() {
  console.log('═'.repeat(60));
  console.log('🎨 일괄 렌더링 시작 (10개 콘텐츠)');
  console.log('═'.repeat(60));

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  try {
    for (const content of CONTENTS) {
      await renderContent(browser, content);
    }

    console.log('\n' + '═'.repeat(60));
    console.log('✨ 전체 렌더링 완료!');
    console.log('═'.repeat(60));

  } finally {
    await browser.close();
  }
}

main().catch(console.error);
