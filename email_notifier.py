"""
Gmail 기반 승인 알림 시스템
텔레그램 대신 이메일로 승인 요청 전송
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

def send_approval_email(title, topic, preview_html, images, app_url):
    """
    승인 요청 이메일 전송
    
    Args:
        title: 블로그 글 제목
        topic: 주제
        preview_html: 글 미리보기 (HTML)
        images: 이미지 URL 리스트
        app_url: Streamlit 앱 URL
    """
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        print("❌ [Email] Gmail 설정이 없습니다")
        return False
    
    try:
        # 승인 URL 생성
        approve_url = f"{app_url}?action=approve"
        reject_url = f"{app_url}?action=reject"
        
        # HTML 이메일 본문
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #333;">📝 블로그 글 승인 요청</h1>
            
            <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h2 style="margin: 0 0 10px 0; color: #00875A;">{title}</h2>
                <p style="color: #666; margin: 0;">주제: {topic}</p>
            </div>
            
            <h3>📄 글 미리보기</h3>
            <div style="border: 1px solid #ddd; padding: 15px; border-radius: 8px; max-height: 300px; overflow: hidden;">
                {preview_html[:1000]}...
            </div>
            
            <h3>🖼️ 생성된 이미지 ({len(images)}장)</h3>
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                {"".join(f'<img src="{img}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 8px;">' for img in images[:3])}
            </div>
            
            <div style="margin: 30px 0; text-align: center;">
                <a href="{approve_url}" style="display: inline-block; background: #00875A; color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-size: 18px; margin-right: 10px;">
                    ✅ 승인하기
                </a>
                <a href="{reject_url}" style="display: inline-block; background: #DE350B; color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-size: 18px;">
                    ❌ 거절하기
                </a>
            </div>
            
            <p style="color: #999; font-size: 12px; text-align: center;">
                이 이메일은 Sunshine Blog Automation에서 자동 발송되었습니다.
            </p>
        </body>
        </html>
        """
        
        # 이메일 메시지 생성
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"[승인 요청] {title}"
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = GMAIL_ADDRESS
        
        # HTML 본문 추가
        msg.attach(MIMEText(html_body, 'html'))
        
        # Gmail SMTP 서버로 전송
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ [Email] 승인 요청 이메일 전송 완료: {title}")
        return True
        
    except Exception as e:
        print(f"❌ [Email] 이메일 전송 실패: {e}")
        return False


def send_completion_email(title, link):
    """업로드 완료 알림 이메일"""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        return False
    
    try:
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h1 style="color: #00875A;">✅ 블로그 업로드 완료!</h1>
            <p><strong>{title}</strong></p>
            <p><a href="{link}" style="color: #0066cc;">👉 블로그 글 보기</a></p>
        </body>
        </html>
        """
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"✅ [완료] {title}"
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = GMAIL_ADDRESS
        msg.attach(MIMEText(html_body, 'html'))
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ [Email] 완료 알림 전송: {title}")
        return True
        
    except Exception as e:
        print(f"❌ [Email] 완료 알림 실패: {e}")
        return False
