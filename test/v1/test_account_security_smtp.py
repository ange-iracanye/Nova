from backend import account_security


class FakeSMTP:
    ports = []

    def __init__(self, host, port, **kwargs):
        self.ports.append(port)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def ehlo(self):
        pass

    def starttls(self, **kwargs):
        pass

    def send_message(self, message):
        pass


def test_email_delivery_falls_back_for_invalid_smtp_port(monkeypatch):
    FakeSMTP.ports = []
    monkeypatch.setenv("NOVA_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("NOVA_SMTP_FROM", "no-reply@example.com")
    monkeypatch.setenv("NOVA_SMTP_PORT", "not-a-port")
    monkeypatch.setenv("NOVA_SMTP_STARTTLS", "false")
    monkeypatch.setattr(account_security.smtplib, "SMTP", FakeSMTP)

    assert account_security._send_email(
        "student@example.com",
        "Nova verification",
        "Verification message",
    ) is True
    assert FakeSMTP.ports == [587]


def test_email_delivery_falls_back_for_out_of_range_smtp_port(monkeypatch):
    FakeSMTP.ports = []
    monkeypatch.setenv("NOVA_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("NOVA_SMTP_FROM", "no-reply@example.com")
    monkeypatch.setenv("NOVA_SMTP_PORT", "70000")
    monkeypatch.setenv("NOVA_SMTP_STARTTLS", "false")
    monkeypatch.setattr(account_security.smtplib, "SMTP", FakeSMTP)

    assert account_security._send_email(
        "student@example.com",
        "Nova verification",
        "Verification message",
    ) is True
    assert FakeSMTP.ports == [587]
