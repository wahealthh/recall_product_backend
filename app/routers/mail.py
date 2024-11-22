from fastapi import APIRouter, Request, status, HTTPException
from jinja2 import Environment, select_autoescape, PackageLoader
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.config.config import settings


router = APIRouter(prefix="/mail", tags=["Mail management"])

jinja2_env = Environment(
    loader=PackageLoader("app"), autoescape=select_autoescape(["html", "xml"])
)
sg_client = SendGridAPIClient(settings.SENDGRID_API_KEY)


@router.post("/confirmation_email", status_code=status.HTTP_201_CREATED)
async def send_confirmation_email(request: Request):
    try:
        appointment_data = await request.json()
        template = jinja2_env.get_template("mail.html")

        appointment_date = appointment_data.get("appointment_date", "Not specified")
        appointment_time = appointment_data.get("appointment_time", "Not specified")
        patient_name = appointment_data.get("patient_name", "Patient")
        patient_email = appointment_data.get("patient_email", "Not specified")

        html = template.render(
            patient_name=patient_name,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            appointment_details=appointment_data,
            patient_email=patient_email,
        )

        mail = Mail(
            from_email=settings.SENDER_EMAIL,
            to_emails=patient_email,
            subject=f"Appointment Confirmation for {patient_name}",
            html_content=html,
        )

        response = sg_client.send(mail)
        return {
            "status": "success",
            "message": "Email sent successfully",
            "status_code": response.status_code,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending mail: {str(e)}",
        )
