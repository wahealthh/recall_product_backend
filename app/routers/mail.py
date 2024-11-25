from fastapi import APIRouter, Request, status, HTTPException
from jinja2 import Environment, select_autoescape, PackageLoader
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.config.config import settings
from app.schema.mail import AppointmentData

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
)
async def send_confirmation_email(request: Request):
    try:
        data = await request.json()
        print(data)

        appointment_raw = data["message"]["tool_calls"][0]["function"]["arguments"][
            "appointment_data"
        ]

        appointment = AppointmentData(**appointment_raw)

        template = jinja2_env.get_template("mail.html")
        html = template.render(
            patient_name=appointment.patient_name,
            appointment_date=appointment.appointment_date,
            appointment_time=appointment.appointment_time,
            gp_name=appointment.gp_name,
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
    except KeyError as e:
        print(f"Missing required field in request structure: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required field in request structure: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending mail: {str(e)}",
        )
