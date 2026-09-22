from pydantic import BaseModel


class DemoAccountResponse(BaseModel):
    """What the browser is told after generating a demo account.

    The password is returned because the person who clicked the button needs it to sign
    back in later. It is the same published demo password for every generated account, so
    nothing secret is being disclosed here.
    """

    email: str
    password: str
    full_name: str
