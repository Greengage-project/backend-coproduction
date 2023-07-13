import json
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional
import threading

import emails
from emails import Message
import uuid
from emails.template import JinjaTemplate

from app.models import Team
from app.config import settings

semaphore = threading.Semaphore(4)

def thread_send_email(message, email_to, environment, smtp_options):
    with semaphore:
        message.dkim(key=os.environ['DKIM_KEY'], domain='interlink-project.eu', selector='google')
        response = message.send(to=email_to, render=environment, smtp=smtp_options)
        logging.info(f"send email result: {response}")

# Create a new class that inherits from the emails.Message class
class CustomMessage(Message):
    def build(self):
        msg = super().build()
        msg['Message-ID'] = '<{}@'+settings.SERVER_NAME+'>'.format(uuid.uuid4())
        return msg

def send_email(
    email_to: str,
    type: str = "",
    environment: Dict[str, Any] = {},
) -> None:
    assert settings.EMAILS_ENABLED, "no provided configuration for email variables"

    
    environment["server"] = settings.SERVER_NAME
    if type == 'add_member_team':
        subject = 'Interlink: You have been added to a new team'
        environment["team_url"] = 'https://{server}/dashboard/organizations/{org_id}/{team_id}'.format(
            server=settings.SERVER_NAME,
            org_id=environment['org_id'],
            team_id=environment['team_id'])
        environment["link"] = 'https://{server}/dashboard/organizations/{org_id}/{team_id}'.format(
            server=settings.SERVER_NAME,
            org_id=environment['org_id'],
            team_id=environment['team_id'])
    elif type == 'add_admin_coprod':
        subject = 'Interlink: You have been added to a new coproduction process'
        environment["link"] = 'https://{server}/dashboard/coproductionprocesses/{id}/overview'.format(
            server=settings.SERVER_NAME,
            id=environment['coprod_id'])
    elif type == 'user_apply_team':
        subject = 'Interlink: A new user has applied to join your team'
        environment["link"] = 'https://{server}/dashboard/organizations/{org_id}/{team_id}?user={user_email}'.format(
            server=settings.SERVER_NAME,
            org_id=environment['org_id'],
            team_id=environment['team_id'],
            user_email=environment['user_email'])
    elif type == 'apply_to_be_contributor':
        subject = 'Interlink: A user has applied to be a contributor'
        environment["link"] = 'https://{server}/dashboard/coproductionprocesses/{id}/team?tab=Requests'.format(
            server=settings.SERVER_NAME,
            id=environment['coprod_id'])
        environment["coprod_id"] = str(environment.get("coprod_id", ""))
    
    elif type == 'ask_team_contribution':
        subject = environment['subject']

    # Load HTML template
    with open(Path(settings.EMAIL_TEMPLATES_DIR) / "{type}.html".format(type=type)) as f:
        template_str = f.read()
    template = JinjaTemplate(template_str)
    
    
    # Create EmailMessage instance
    message = CustomMessage(
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

    t = threading.Thread(target=thread_send_email,args=(message, email_to, environment, smtp_options))
    t.start()


def send_team_email(
    team: Team,
    type: str = "",
    environment: Dict[str, Any] = {},
) -> None:
    assert settings.EMAILS_ENABLED, "no provided configuration for email variables"
    
    environment["server"] = settings.SERVER_NAME
    if type == 'add_team_coprod':
        subject = 'Interlink: Your team has been added to a coproduction process'
        environment["team_url"] = 'https://{server}/dashboard/organizations/{org_id}/{team_id}'.format(
            server=settings.SERVER_NAME,
            org_id=environment['org_id'],
            team_id=environment['team_id'])
        environment["link"] = 'https://{server}/dashboard/coproductionprocesses/{id}/overview'.format(
            server=settings.SERVER_NAME,
            id=environment['coprod_id'])

    elif type == 'add_member_team':
        subject = 'Interlink: You have been added to a new team'
        environment["team_url"] = 'https://{server}/dashboard/organizations/{org_id}/{team_id}'.format(
            server=settings.SERVER_NAME,
            org_id=environment['org_id'],
            team_id=environment['team_id'])
        environment["link"] = 'https://{server}/dashboard/organizations/{org_id}/{team_id}'.format(
            server=settings.SERVER_NAME,
            org_id=environment['org_id'],
            team_id=environment['team_id'])

    elif type == 'add_team_treeitem':
        subject = 'Interlink: New permissions on a coproduction item'
        environment["team_url"] = 'https://{server}/dashboard/organizations/{org_id}/{team_id}'.format(
            server=settings.SERVER_NAME,
            org_id=environment['org_id'],
            team_id=environment['team_id'])
        environment["coprod_url"] = 'https://{server}/dashboard/coproductionprocesses/{coprod_id}'.format(
            server=settings.SERVER_NAME,
            coprod_id=environment['coprod_id'])
        environment["link"] = 'https://{server}/dashboard/coproductionprocesses/{coprod_id}/{treeitem_id}/guide'.format(
            server=settings.SERVER_NAME,
            coprod_id=environment['coprod_id'],
            treeitem_id=environment['treeitem_id'])
    elif type == 'ask_team_contribution':
        subject = environment['subject']
        
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
        t = threading.Thread(target=thread_send_email,args=(message, user.email, environment, smtp_options))
        t.start()

def send_test_email(email_to: str) -> None:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Test email"
    with open(Path(settings.EMAIL_TEMPLATES_DIR) / "added_to_process.html") as f:
        template_str = f.read()
