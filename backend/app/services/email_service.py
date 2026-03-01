import smtplib
import base64
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def send_email(to_email: str, subject: str, html_content: str, inline_images: dict = None):
    """
    Send an HTML email with optional inline images (CID embedding).
    inline_images: dict of {cid: file_path}
    """
    try:
        # Outer message wrapper
        msg_outer = MIMEMultipart("mixed")
        msg_outer["From"] = settings.SMTP_USER
        msg_outer["To"] = to_email
        msg_outer["Subject"] = subject

        # Related part holds HTML + inline images
        msg_related = MIMEMultipart("related")

        # Alternative part (plain + HTML)
        msg_alt = MIMEMultipart("alternative")
        msg_alt.attach(MIMEText("Please view this email in an HTML-enabled client.", "plain"))
        msg_alt.attach(MIMEText(html_content, "html"))

        msg_related.attach(msg_alt)

        # Attach inline images
        if inline_images:
            for cid, filepath in inline_images.items():
                if os.path.exists(filepath):
                    with open(filepath, "rb") as f:
                        img_data = f.read()
                    img = MIMEImage(img_data)
                    img.add_header("Content-ID", f"<{cid}>")
                    img.add_header("Content-Disposition", "inline", filename=os.path.basename(filepath))
                    msg_related.attach(img)

        msg_outer.attach(msg_related)

        # Connect to Gmail SMTP
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg_outer)
        server.quit()

        logger.info(f"Email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

def send_otp_email(to_email: str, otp: str):
    subject = "Verify Your Login Attempt"
    from datetime import datetime
    
    # Dummy values for context details (to be replaced with real request context later)
    device_type = "Desktop / Mobile"
    browser = "Web Browser"
    location = "Unknown Location"
    time_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    secure_link = "#"

    # Path to the InfiChat logo icon (will be CID-embedded in the email)
    logo_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "public", "logo_icon.png")
    logo_path = os.path.normpath(logo_path)

    html_content = f"""
<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="x-apple-disable-message-reformatting">
    <title>Verify Your Login Attempt</title>
    <!--[if mso]>
    <noscript>
        <xml>
            <o:OfficeDocumentSettings>
                <o:PixelsPerInch>96</o:PixelsPerInch>
            </o:OfficeDocumentSettings>
        </xml>
    </noscript>
    <![endif]-->
    <style type="text/css">
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        body, table, td, div, p, a {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }}
        
        body {{
            margin: 0;
            padding: 0;
            width: 100% !important;
            background-color: #0b0e14;
            -webkit-font-smoothing: antialiased;
        }}

        table {{
            border-spacing: 0;
            border-collapse: collapse;
            mso-table-lspace: 0pt;
            mso-table-rspace: 0pt;
        }}

        img {{
            border: 0;
            line-height: 100%;
            outline: none;
            text-decoration: none;
            display: block;
        }}

        .wrap {{
            width: 100%;
            max-width: 600px;
            margin: 0 auto;
        }}

        .glass-card {{
            background-color: #1a1e29;
            background: linear-gradient(145deg, rgba(30, 35, 48, 0.9) 0%, rgba(20, 24, 34, 0.95) 100%);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
            overflow: hidden;
        }}

        .otp-box {{
            background-color: #0b0e14;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 24px 40px;
            display: inline-block;
            box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.3);
        }}

        .info-card {{
            background-color: #232836;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 24px;
        }}

        @media screen and (max-width: 600px) {{
            .wrap {{
                width: 100% !important;
                padding: 0 16px !important;
                box-sizing: border-box;
            }}
            .content-pad {{
                padding: 32px 24px !important;
            }}
            .info-table td {{
                display: block !important;
                width: 100% !important;
                padding: 4px 0 !important;
            }}
            .info-label {{
                padding-bottom: 2px !important;
            }}
            .info-val {{
                padding-bottom: 12px !important;
            }}
        }}
    </style>
</head>
<body style="margin: 0; padding: 0; background-color: #0b0e14;">

    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #0b0e14; background-image: linear-gradient(135deg, #0b0e14 0%, #131824 100%);">
        <tr>
            <td align="center" style="padding: 40px 16px;">
                
                <!-- Main Wrapper -->
                <table class="wrap glass-card" cellpadding="0" cellspacing="0" border="0" style="width: 100%; max-width: 600px; background-color: #1a1e29; border: 1px solid #2d3345; border-radius: 16px;">
                    
                    <!-- Header Section -->
                    <tr>
                        <td class="content-pad" align="center" style="padding: 40px 40px 24px 40px; border-bottom: 1px solid rgba(255, 255, 255, 0.06);">
                            <!-- Logo Area: pure text, works in all email clients -->
                            <div style="margin-bottom: 20px; display: inline-block; text-align: center;">
                                <div style="font-size: 42px; line-height: 1; margin-bottom: 8px; color: #38bdf8;">&#8734;</div>
                                <div style="font-size: 26px; font-weight: 800; letter-spacing: -0.5px; color: #ffffff;">InfiChat</div>
                            </div>
                            <p style="margin: 8px 0 0 0; font-size: 13px; font-weight: 500; color: #60a5fa; letter-spacing: 1px; text-transform: uppercase;">Intelligent Conversations. Secure Access.</p>
                        </td>
                    </tr>

                    <!-- Body Section -->
                    <tr>
                        <td class="content-pad" style="padding: 40px;">
                            
                            <h2 style="margin: 0 0 16px 0; font-size: 24px; font-weight: 600; color: #ffffff; text-align: center;">Verify Your Login Attempt</h2>
                            <p style="margin: 0 0 32px 0; font-size: 15px; line-height: 24px; color: #9ca3af; text-align: center;">You have requested to log in to your account. Enter the authorization code below to successfully verify your identity.</p>
                            
                            <!-- OTP Verification Box -->
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom: 20px;">
                                <tr>
                                    <td align="center">
                                        <div class="otp-box" style="background-color: #0b0e14; border: 1px solid #2d3345; border-radius: 12px; padding: 24px 40px; display: inline-block;">
                                            <div style="margin: 0; font-size: 38px; font-weight: 700; letter-spacing: 8px; color: #ffffff; text-shadow: 0 0 20px rgba(255, 255, 255, 0.2);">{otp}</div>
                                        </div>
                                    </td>
                                </tr>
                            </table>

                            <!-- Expiration Timer -->
                            <p style="margin: 0 0 40px 0; font-size: 14px; font-weight: 500; color: #ef4444; text-align: center; display: flex; align-items: center; justify-content: center;">
                                <img src="https://img.icons8.com/ios-filled/50/ef4444/clock--v1.png" alt="Timer" width="16" height="16" style="vertical-align: middle; margin-right: 6px; display: inline-block;">
                                <span style="vertical-align: middle;">Valid for 5 minutes only</span>
                            </p>

                            <!-- Login Attempt Info -->
                            <div class="info-card" style="background-color: #232836; border: 1px solid #2d3345; border-radius: 12px; padding: 24px; margin-bottom: 40px;">
                                <h3 style="margin: 0 0 20px 0; font-size: 12px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 1px;">Login Attempt Details</h3>
                                <table class="info-table" width="100%" cellpadding="0" cellspacing="0" border="0">
                                    <tr>
                                        <td class="info-label" style="padding: 10px 0; font-size: 14px; color: #9ca3af; width: 35%; border-bottom: 1px solid rgba(255,255,255,0.03);">Device Type</td>
                                        <td class="info-val" style="padding: 10px 0; font-size: 14px; color: #e5e7eb; font-weight: 500; border-bottom: 1px solid rgba(255,255,255,0.03);">{device_type}</td>
                                    </tr>
                                    <tr>
                                        <td class="info-label" style="padding: 10px 0; font-size: 14px; color: #9ca3af; border-bottom: 1px solid rgba(255,255,255,0.03);">Browser</td>
                                        <td class="info-val" style="padding: 10px 0; font-size: 14px; color: #e5e7eb; font-weight: 500; border-bottom: 1px solid rgba(255,255,255,0.03);">{browser}</td>
                                    </tr>
                                    <tr>
                                        <td class="info-label" style="padding: 10px 0; font-size: 14px; color: #9ca3af; border-bottom: 1px solid rgba(255,255,255,0.03);">Location</td>
                                        <td class="info-val" style="padding: 10px 0; font-size: 14px; color: #e5e7eb; font-weight: 500; border-bottom: 1px solid rgba(255,255,255,0.03);">{location} <span style="color: #6b7280; font-size: 12px;">(Approximate)</span></td>
                                    </tr>
                                    <tr>
                                        <td class="info-label" style="padding: 10px 0 0 0; font-size: 14px; color: #9ca3af;">Time</td>
                                        <td class="info-val" style="padding: 10px 0 0 0; font-size: 14px; color: #e5e7eb; font-weight: 500;">{time_str}</td>
                                    </tr>
                                </table>
                            </div>

                            <!-- Trust / Security Notice Section -->
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="text-align: center;">
                                <tr>
                                    <td align="center" style="padding-bottom: 16px;">
                                        <div style="background-color: rgba(245, 158, 11, 0.1); border-radius: 50%; width: 48px; height: 48px; line-height: 48px; margin-bottom: 16px;">
                                            <img src="https://img.icons8.com/ios-filled/50/f59e0b/lock.png" alt="Lock Icon" width="24" height="24" style="display: inline-block; vertical-align: middle;">
                                        </div>
                                        <h3 style="margin: 0 0 10px 0; font-size: 18px; font-weight: 600; color: #f59e0b;">Security Notice</h3>
                                        <p style="margin: 0; font-size: 14px; color: #9ca3af; line-height: 22px;">If this wasn't you, your account may be at risk. <br />Take immediate action to secure your data.</p>
                                    </td>
                                </tr>
                                <tr>
                                    <td align="center" style="padding-top: 24px;">
                                        <a href="{secure_link}" style="display: inline-block; padding: 14px 32px; background-color: #ef4444; background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%); color: #ffffff; text-decoration: none; font-size: 15px; font-weight: 600; border-radius: 8px; border: 1px solid #f87171; box-shadow: 0 4px 14px rgba(239, 68, 68, 0.25);">Secure My Account</a>
                                    </td>
                                </tr>
                            </table>

                        </td>
                    </tr>

                    <!-- Footer Section -->
                    <tr>
                        <td class="content-pad" align="center" style="padding: 30px 40px; background-color: rgba(0, 0, 0, 0.3); border-top: 1px solid rgba(255, 255, 255, 0.05);">
                            <p style="margin: 0 0 16px 0; font-size: 12px; color: #6b7280; line-height: 18px;">
                                This is an automated security message. <br>
                                <strong style="color: #9ca3af;">Do not share your OTP with anyone.</strong>
                            </p>
                            <p style="margin: 0 0 12px 0; font-size: 13px; font-weight: 600; color: #9ca3af; letter-spacing: 0.5px;">
                                InfiChat Security Team
                            </p>
                            <p style="margin: 0; font-size: 11px; color: #4b5563;">
                                &copy; 2026 InfiChat. All Rights Reserved.
                            </p>
                        </td>
                    </tr>

                </table>
                
            </td>
        </tr>
    </table>

</body>
</html>
    """
    
    # DEV MODE: Print OTP to console explicitly
    print(f"\n{'='*40}")
    print(f"OTP for {to_email}: {otp}")
    print(f"{'='*40}\n")
    
    if settings.SMTP_PASSWORD == "CHANGE_ME" or not settings.SMTP_PASSWORD:
        logger.warning("SMTP not configured. Mocking email sending.")
        return True

    return send_email(to_email, subject, html_content, inline_images={"logo_icon": logo_path})
