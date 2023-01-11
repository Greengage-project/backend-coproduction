import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import emails
from emails.template import JinjaTemplate

from app.models import Team
from app.config import settings


async def send_email(
    email_to: str,
    type: str = "",
    environment: Dict[str, Any] = {},
) -> None:
    assert settings.EMAILS_ENABLED, "no provided configuration for email variables"

    if type == 'add_member_team':
        subject = 'Interlink: You have been added to a new team'
        environment["link"] = 'https://{server}/dashboard/organizations'.format(
            server=settings.SERVER_NAME)
    elif type == 'add_admin_coprod':
        subject = 'Interlink: You have been added to a new coproduction process'
        environment["link"] = 'https://{server}/dashboard/coproductionprocesses/{id}'.format(
            server=settings.SERVER_NAME, id=environment['coprod_id'])

    with open(Path(settings.EMAIL_TEMPLATES_DIR) / "{type}.html".format(type=type)) as f:
        template_str = f.read()
    template = JinjaTemplate(template_str)
    message = emails.Message(
        subject=subject,
        html=template,
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    )

    # SMTP settings
    smtp_options = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
    if settings.SMTP_TLS:
        smtp_options["tls"] = True
    if settings.SMTP_USER:
        smtp_options["user"] = settings.SMTP_USER
    if settings.SMTP_PASSWORD:
        smtp_options["password"] = settings.SMTP_PASSWORD

    response = message.send(to=email_to, render=environment, smtp=smtp_options)
    logging.info(f"send email result: {response}")


async def send_team_email(
    team: Team,
    type: str = "",
    environment: Dict[str, Any] = {},
) -> None:
    assert settings.EMAILS_ENABLED, "no provided configuration for email variables"

    if type == 'add_team_coprod':
        subject = 'Interlink: Your team has been added to a coproduction process'
        environment["link"] = 'https://{server}/dashboard/coproductionprocesses/{id}'.format(
            server=settings.SERVER_NAME,
            id=environment['coprod_id'])
        
    elif type == 'add_member_team':
        subject = 'Interlink: You have been added to a new team'
        environment["link"] = 'https://{server}/dashboard/organizations'.format(
            server=settings.SERVER_NAME)
        
    elif type == 'add_team_treeitem':
        subject = 'Interlink: New permissions on a coproduction item'
    environment["link"] = 'https://{server}/dashboard/coproductionprocesses/{coprod_id}/{treeitem_id}'.format(
        server=settings.SERVER_NAME,
        coprod_id=environment['coprod_id'],
        treeitem_id=environment['treeitem_id'])

    with open(Path(settings.EMAIL_TEMPLATES_DIR) / "{type}.html".format(type=type)) as f:
        template_str = f.read()
    template = JinjaTemplate(template_str)

    message = emails.Message(
        subject=subject,
        html=template,
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    )

    # SMTP settings
    smtp_options = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
    if settings.SMTP_TLS:
        smtp_options["tls"] = True
    if settings.SMTP_USER:
        smtp_options["user"] = settings.SMTP_USER
    if settings.SMTP_PASSWORD:
        smtp_options["password"] = settings.SMTP_PASSWORD

    for user in team.users:
        response = message.send(to=user.email,
                                render=environment,
                                smtp=smtp_options)
        logging.info(f"send email result: {response}")


def send_test_email(email_to: str) -> None:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Test email"
    with open(Path(settings.EMAIL_TEMPLATES_DIR) / "added_to_process.html") as f:
        template_str = f.read()
    # message = emails.html(html=open(Path(settings.EMAIL_TEMPLATES_DIR) / "added_to_process.html"),
    #                   subject='Friday party',
    #                   mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL))
    # response = message.send(render={"project_name": "user/project1", "username": 121},
    #               to='ruben.sanchez@deusto.es',
    #               smtp={"host": settings.SMTP_HOST, "port": settings.SMTP_PORT})
    # send_email(
    #     email_to=email_to,
    #     subject_template=subject,
    #     html_template=template_str,
    #     environment={"project_name": settings.PROJECT_NAME, "email": email_to, "username": "asdf", "password": "asdf", "link": "asdf"},
    # )
