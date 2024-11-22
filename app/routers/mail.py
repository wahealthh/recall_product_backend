from fastapi import APIRouter, status, HTTPException
from jinja2 import Environment, select_autoescape, PackageLoader
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.config.config import settings
from app.schema.mail import AppointmentEmail

router = APIRouter(prefix="/mail", tags=["Mail management"])


jinja2_env = Environment(
    loader=PackageLoader("app"), autoescape=select_autoescape(["html", "xml"])
)
sg_client = SendGridAPIClient(settings.SENDGRID_API_KEY)


@router.post(
    "/confirmation_email",
    status_code=status.HTTP_201_CREATED,
    summary="Send appointment confirmation email",
    description="Sends an email confirmation for a scheduled appointment",
    response_description="Email sent successfully",
)
async def send_confirmation_email(appointment: AppointmentEmail):
    try:
        template = jinja2_env.get_template("mail.html")
        html = template.render(
            patient_name=appointment.patient_name,
            appointment_date=appointment.appointment_date,
            appointment_time=appointment.appointment_time,
            appointment_details=appointment.model_dump(),
        )

        mail = Mail(
            from_email=settings.SENDER_EMAIL,
            to_emails=appointment.patient_email,
            subject=f"Appointment Confirmation for {appointment.patient_name}",
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
