/**
 * 실사진 CTA 오버레이 스크립트 (A안 구현)
 * - 햇살이 실사진을 CTA 슬라이드(03번)에 적용
 * - 기존 텍스트 오버레이 스타일 100% 동일
 *
 * 사용법:
 *   node apply_real_photo_cta.js <content_folder> <topic> [mood]
 *
 * 예시:
 *   node apply_real_photo_cta.js content/images/023_코카콜라 coca_cola happy
 *
 * Author: 김부장
 * Version: 2.0 (기존 스타일 매칭)
 */

import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, '..', '..');

// 실사진 폴더 경로
const REAL_PHOTO_PATHS = {
  happy: path.join(PROJECT_ROOT, 'content/images/sunshine/01_usable/grade_A/expression/happy'),
  cuddle: path.join(PROJECT_ROOT, 'content/images/sunshine/02_with_human/cuddle'),
  daily: path.join(PROJECT_ROOT, 'content/images/sunshine/02_with_human/daily'),
};

// CTA 스타일 (v1.0 확정 - 포도/시금치 기준)
const CTA_STYLE = {
  titleFont: "'Noto Sans KR', 'Apple SD Gothic Neo', sans-serif",
  titleSize: 64,
  titleWeight: 900,
  titleColor: '#FFD93D',  // CTA용 노란색
  subtitleSize: 40,
  subtitleWeight: 500,
  subtitleColor: '#FFFFFF',
};

// CTA 텍스트 옵션
const CTA_TEXTS = {
  default: { title: '공유 필수!', subtitle: '다른 견주에게도 알려주세요' },
  save: { title: '저장하세요!', subtitle: '나중에 다시 확인하세요' },
  follow: { title: '팔로우하세요!', subtitle: '더 많은 정보를 받아보세요' },
};

// 폴더에서 랜덤 이미지 선택
function getRandomPhoto(mood = 'happy') {
  const folder = REAL_PHOTO_PATHS[mood] || REAL_PHOTO_PATHS.happy;

  if (!fs.existsSync(folder)) {
    throw new Error(`폴더를 찾을 수 없습니다: ${folder}`);
  }

  const files = fs.readdirSync(folder).filter(f =>
    ['.jpg', '.jpeg', '.png'].includes(path.extname(f).toLowerCase())
  );

  if (files.length === 0) {
    throw new Error(`사진을 찾을 수 없습니다: ${folder}`);
  }

  const randomFile = files[Math.floor(Math.random() * files.length)];
  return path.join(folder, randomFile);
}

// 이미지를 Base64로 변환
function imageToBase64(imagePath) {
  const buffer = fs.readFileSync(imagePath);
  const ext = path.extname(imagePath).toLowerCase();
  const mimeType = ext === '.png' ? 'image/png' : 'image/jpeg';
  return `data:${mimeType};base64,${buffer.toString('base64')}`;
}

// HTML 생성 - 실사진 CTA (기존 스타일과 100% 동일)
function generateCTAHTML(imageSrc, title, subtitle) {
  const s = CTA_STYLE;

  // 핵심: object-fit: cover + object-position: center로 중앙 크롭 (비율 유지)
  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css" rel="stylesheet">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      width: 1080px; height: 1080px;
      position: relative; overflow: hidden;
      font-family: ${s.titleFont};
    }
    .bg {
      position: absolute; top: 0; left: 0;
      width: 100%; height: 100%;
      object-fit: cover;
      object-position: center;
    }
    .gradient {
      position: absolute;
      bottom: 0; left: 0;
      width: 100%; height: 55%;
      background: linear-gradient(
        to top,
        rgba(0,0,0,0.9) 0%,
        rgba(0,0,0,0.7) 35%,
        rgba(0,0,0,0.4) 65%,
        rgba(0,0,0,0) 100%
      );
    }
    .text-wrap {
      position: absolute;
      bottom: 130px;
      left: 0; width: 100%;
      text-align: center;
      padding: 0 60px;
    }
    .title {
      font-size: ${s.titleSize}px;
      font-weight: ${s.titleWeight};
      color: ${s.titleColor};
      text-shadow: 0 4px 16px rgba(0,0,0,0.8), 0 2px 4px rgba(0,0,0,0.9);
      margin-bottom: 32px;
      letter-spacing: 0.02em;
    }
    .subtitle {
      font-size: ${s.subtitleSize}px;
      font-weight: ${s.subtitleWeight};
      color: ${s.subtitleColor};
      text-shadow: 0 2px 8px rgba(0,0,0,0.6);
      letter-spacing: 0.01em;
    }
  </style>
</head>
<body>
  <img class="bg" src="${imageSrc}" alt="background" />
  <div class="gradient"></div>
  <div class="text-wrap">
    <div class="title">${title}</div>
    <div class="subtitle">${subtitle}</div>
  </div>
</body>
</html>`;
}

// 메인 함수
async function main() {
  const args = process.argv.slice(2);

  if (args.length < 2) {
    console.log('Usage: node apply_real_photo_cta.js <content_folder> <topic> [mood] [cta_type]');
    console.log('');
    console.log('Examples:');
    console.log('  node apply_real_photo_cta.js content/images/023_코카콜라 coca_cola happy');
    console.log('  node apply_real_photo_cta.js content/images/022_아보카도 avocado cuddle');
    console.log('');
    console.log('Moods: happy, cuddle, daily');
    console.log('CTA types: default, save, follow');
    process.exit(1);
  }

  const contentFolder = path.resolve(args[0]);
  const topic = args[1];
  const mood = args[2] || 'happy';
  const ctaType = args[3] || 'default';

  console.log('━'.repeat(60));
  console.log('📸 실사진 CTA 오버레이 (A안)');
  console.log('━'.repeat(60));
  console.log(`📁 폴더: ${contentFolder}`);
  console.log(`🎯 토픽: ${topic}`);
  console.log(`😊 분위기: ${mood}`);
  console.log('');

  // 실사진 선택
  const photoPath = getRandomPhoto(mood);
  console.log(`📸 선택된 사진: ${path.basename(photoPath)}`);

  // 출력 경로
  const outputPath = path.join(contentFolder, `${topic}_03.png`);
  const archiveDir = path.join(contentFolder, 'archive');

  // 기존 파일 백업
  if (fs.existsSync(outputPath)) {
    if (!fs.existsSync(archiveDir)) {
      fs.mkdirSync(archiveDir, { recursive: true });
    }
    const backupPath = path.join(archiveDir, `${topic}_03_ai_backup.png`);
    fs.renameSync(outputPath, backupPath);
    console.log(`📦 기존 AI 이미지 백업: ${path.basename(backupPath)}`);
  }

  // CTA 텍스트
  const ctaText = CTA_TEXTS[ctaType] || CTA_TEXTS.default;

  // Puppeteer로 렌더링
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1080 });

  const imageSrc = imageToBase64(photoPath);
  const html = generateCTAHTML(imageSrc, ctaText.title, ctaText.subtitle);

  await page.setContent(html, { waitUntil: 'networkidle0' });
  await page.evaluateHandle('document.fonts.ready');
  await new Promise(r => setTimeout(r, 500));
  await page.screenshot({ path: outputPath, type: 'png' });

  await browser.close();

  console.log(`✅ CTA 슬라이드 생성: ${path.basename(outputPath)}`);
  console.log('');
  console.log('━'.repeat(60));
  console.log('🎉 완료! 실사진 CTA가 적용되었습니다.');
  console.log('━'.repeat(60));
}

main().catch(console.error);
