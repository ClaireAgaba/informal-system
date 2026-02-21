import logging
import threading
from django.core.mail import EmailMessage
from django.conf import settings

logger = logging.getLogger(__name__)


def send_collection_receipt_email(receipt_data, recipient_email):
    """
    Send a transcript collection receipt as an HTML email.
    Runs in a background thread so it doesn't block the API response.
    """
    def _send():
        try:
            subject = f"Transcript Collection Receipt - {receipt_data['receipt_number']}"

            candidates_rows = ''
            for i, c in enumerate(receipt_data['candidates'], 1):
                candidates_rows += f"""
                <tr>
                    <td style="padding:8px 12px;border:1px solid #e5e7eb;">{i}</td>
                    <td style="padding:8px 12px;border:1px solid #e5e7eb;">{c['registration_number'] or '-'}</td>
                    <td style="padding:8px 12px;border:1px solid #e5e7eb;">{c['full_name']}</td>
                    <td style="padding:8px 12px;border:1px solid #e5e7eb;">{c.get('tr_sno', '-') or '-'}</td>
                </tr>"""

            designation_labels = {
                'head_teacher': 'Head Teacher',
                'deputy_head_teacher': 'Deputy Head Teacher',
                'center_administrator': 'Center Administrator',
                'candidate': 'Candidate',
                'other_person': 'Other Person',
            }
            designation_display = designation_labels.get(
                receipt_data['designation'], receipt_data['designation']
            )

            issued_by = receipt_data.get('issued_by', 'UVTAB Staff')

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; color: #1f2937; margin: 0; padding: 0; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ text-align: center; border-bottom: 2px solid #1e40af; padding-bottom: 16px; margin-bottom: 20px; }}
                    .header h1 {{ color: #1e40af; font-size: 20px; margin: 0 0 4px 0; }}
                    .header p {{ margin: 2px 0; font-size: 12px; color: #6b7280; }}
                    .receipt-title {{ text-align: center; font-size: 16px; font-weight: bold; color: #1e40af; margin: 16px 0; text-transform: uppercase; }}
                    .info-grid {{ width: 100%; margin-bottom: 16px; }}
                    .info-grid td {{ padding: 6px 0; font-size: 13px; }}
                    .info-label {{ color: #6b7280; width: 160px; }}
                    .info-value {{ font-weight: 600; }}
                    table.candidates {{ width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 13px; }}
                    table.candidates th {{ background: #1e40af; color: white; padding: 8px 12px; text-align: left; }}
                    table.candidates td {{ font-size: 13px; }}
                    .footer {{ margin-top: 24px; padding-top: 16px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; text-align: center; }}
                    .issued {{ margin-top: 20px; padding-top: 12px; border-top: 1px dashed #d1d5db; font-size: 13px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>UGANDA VOCATIONAL TRAINING AND ASSESSMENT BOARD</h1>
                        <p>Plot 2 - 4 Jinja Road, P.O. Box 7120, Kampala</p>
                        <p>Tel: 0392002468</p>
                    </div>

                    <div class="receipt-title">Transcript Collection Receipt</div>

                    <table class="info-grid">
                        <tr>
                            <td class="info-label">Receipt Number:</td>
                            <td class="info-value">{receipt_data['receipt_number']}</td>
                        </tr>
                        <tr>
                            <td class="info-label">Collection Date:</td>
                            <td class="info-value">{receipt_data['collection_date']}</td>
                        </tr>
                        <tr>
                            <td class="info-label">Center:</td>
                            <td class="info-value">{receipt_data['center_name']}</td>
                        </tr>
                        <tr>
                            <td class="info-label">Designation:</td>
                            <td class="info-value">{designation_display}</td>
                        </tr>
                        <tr>
                            <td class="info-label">Collector Name:</td>
                            <td class="info-value">{receipt_data['collector_name']}</td>
                        </tr>
                        <tr>
                            <td class="info-label">NIN:</td>
                            <td class="info-value">{receipt_data['nin']}</td>
                        </tr>
                        <tr>
                            <td class="info-label">Phone:</td>
                            <td class="info-value">{receipt_data['collector_phone']}</td>
                        </tr>
                        <tr>
                            <td class="info-label">Email:</td>
                            <td class="info-value">{receipt_data['email']}</td>
                        </tr>
                    </table>

                    <table class="candidates">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Reg. Number</th>
                                <th>Full Name</th>
                                <th>TR S/No</th>
                            </tr>
                        </thead>
                        <tbody>
                            {candidates_rows}
                        </tbody>
                    </table>

                    <p style="font-size:13px;"><strong>Total Candidates:</strong> {receipt_data['candidate_count']}</p>

                    <div class="issued">
                        <strong>Issued By:</strong> {issued_by}
                    </div>

                    <div class="footer">
                        <p>This is an official receipt from UVTAB EMIS.</p>
                        <p>For any inquiries, contact us at 0392002468</p>
                    </div>
                </div>
            </body>
            </html>
            """

            email = EmailMessage(
                subject=subject,
                body=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
            )
            email.content_subtype = 'html'
            email.send(fail_silently=False)

            logger.info(f"Receipt email sent to {recipient_email} for {receipt_data['receipt_number']}")

        except Exception as e:
            logger.error(f"Failed to send receipt email to {recipient_email}: {e}")

    thread = threading.Thread(target=_send, daemon=True)
    thread.start()
